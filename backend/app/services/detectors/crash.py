"""
Vehicle crash detection — FIXED CAMERAS ONLY.

Heuristic, no extra model weights. It reads the vehicle boxes YOLO + ByteTrack
already produce and looks for two signatures:

  1. Sudden deceleration — a vehicle that was genuinely moving loses most of its
     speed within a fraction of a second. Comparing a short "recent" window
     against the window just before it separates an impact from a gentle stop at
     a junction, which bleeds speed off over seconds rather than frames.

  2. Contact then stop — the overlap between two vehicle boxes jumps from
     separate to touching within `crash_iou_lookback`, and the vehicles are then
     stationary and still overlapping. All three parts matter: two cars in
     convoy overlap on screen but keep moving; two parked cars overlap
     constantly without the jump; a car queuing at a light closes the same gap
     gradually rather than in one or two frames.

Either signature must persist for `crash_duration`, with a per-track/per-pair
cooldown — the same shape as the fight detector.

SCOPE AND LIMITATIONS
---------------------
This works on a FIXED camera watching a junction, forecourt or car park, where
track identity is stable and box geometry means something. It was measured
against a real dashcam crash clip (backend/demo_videos/car_crash.mp4) and does
NOT detect it, for reasons that are properties of the footage, not tuning:

  * At the moment of impact, motion blur wipes out detection entirely — the
    clip goes from 6 tracked vehicles to 0 for ~0.3s.
  * ByteTrack loses identity through the collision. The vehicles that crash are
    re-acquired as new track IDs afterwards, so no single track spans
    "moving then stopped", and no pair spans "separate then touching".
  * The wreck's real boxes peak at IoU 0.159 across that clip, while ordinary
    traffic in the same clip reaches 0.078-0.100. Those ranges overlap, so no
    IoU threshold separates crash from normal driving there.

On a moving camera every static object drifts, so when the camera itself stops
every tracked vehicle appears to decelerate at once. The ego-motion guard below
suppresses that, which is why a dashcam feed produces silence rather than a
storm of false alerts. Detecting crashes in dashcam footage needs an impact-
motion cue or a trained model, neither of which is in scope here.

Alerts carry `frame_data`, so evidence capture and hashing happen downstream.
"""
import logging
from typing import Dict, List, Optional, Tuple

from app.services.detectors.base import Detector, DetectorContext, make_alert, register

logger = logging.getLogger(__name__)

# Track state older than this is discarded (vehicle left the frame).
TRACK_TTL = 3.0
# Samples kept per track; at ~5-20 inferences/sec this spans a couple of seconds.
MAX_SAMPLES = 40


def _iou(a: List[float], b: List[float]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def _centroid(box: List[float]) -> Tuple[float, float]:
    return ((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)


def _diag(box: List[float]) -> float:
    """Box diagonal, used to express speed in box-lengths rather than pixels."""
    w = max(1.0, box[2] - box[0])
    h = max(1.0, box[3] - box[1])
    return (w * w + h * h) ** 0.5


def _mean_speed(samples: List[tuple], t_from: float, t_to: float) -> Optional[float]:
    """Mean speed in box-diagonals/second over [t_from, t_to]. None if too few."""
    window = [s for s in samples if t_from <= s[0] <= t_to]
    if len(window) < 2:
        return None
    dt = window[-1][0] - window[0][0]
    if dt <= 0:
        return None
    dx = window[-1][1] - window[0][1]
    dy = window[-1][2] - window[0][2]
    dist = (dx * dx + dy * dy) ** 0.5
    # Normalise by box size so a lorry near the camera and a car far away are
    # measured on the same scale, and a zoomed-in view does not read as fast.
    scale = max(1.0, window[-1][3])
    return (dist / scale) / dt


@register
class CrashDetector(Detector):
    name = "crash"
    enabled_key = "crash_enabled"

    def __init__(self):
        super().__init__()
        # camera_id -> track_id -> [(t, cx, cy, diag), ...]
        self._tracks: Dict[int, Dict[object, List[tuple]]] = {}
        # camera_id -> track_id -> highest speed ever observed for that track
        self._peak_speed: Dict[int, Dict[object, float]] = {}
        # (camera_id, id_a, id_b) -> [(t, iou), ...] recent overlap history
        self._pair_iou: Dict[Tuple, List[tuple]] = {}
        # (camera_id, id_a, id_b) -> timestamp the overlap crossed into contact
        self._contact_at: Dict[Tuple, float] = {}
        # (camera_id, id_a, id_b) -> {"iou": last_iou, "t": last_seen}
        self._pairs: Dict[Tuple, dict] = {}
        # streak keys -> start timestamp
        self._streaks: Dict[str, float] = {}

    # ---- helpers ----------------------------------------------------------
    @staticmethod
    def vehicles(ctx: DetectorContext) -> List[dict]:
        """Real, tracked vehicle boxes only.

        Ghost boxes are ml_inference replaying a track's last known position for
        up to 2s after it drops out. Their position is frozen, which would read
        as a vehicle stopping dead — exactly the crash signature — so they are
        excluded here.
        """
        return [b for b in ctx.boxes
                if b.get("class") == "vehicle" and b.get("id") != "?"
                and not b.get("ghost")]

    def _advance(self, key: str, hit: bool, now: float, duration: float) -> bool:
        """Persistence gate. True once the signature has held for `duration`."""
        if not hit:
            self._streaks.pop(key, None)
            return False
        start = self._streaks.get(key)
        if start is None:
            self._streaks[key] = now
            return False
        return (now - start) >= duration

    # ---- signature 1: sudden deceleration ---------------------------------
    def _decel_hit(self, samples: List[tuple], now: float,
                   recent_win: float, prior_win: float,
                   min_speed: float, ratio: float) -> Optional[Tuple[float, float]]:
        """Return (prior_speed, recent_speed) when the drop qualifies."""
        recent = _mean_speed(samples, now - recent_win, now)
        prior = _mean_speed(samples, now - recent_win - prior_win, now - recent_win)
        if recent is None or prior is None:
            return None
        if prior < min_speed:
            return None                      # was not really moving
        if recent > prior * ratio:
            return None                      # slowed gently, or not at all
        return (prior, recent)

    # ---- main -------------------------------------------------------------
    def detect(self, ctx: DetectorContext) -> List[dict]:
        s = ctx.settings
        min_speed = float(s.get("crash_min_speed", 0.45))        # box-diagonals/sec
        decel_ratio = float(s.get("crash_decel_ratio", 0.25))    # recent/prior
        recent_win = float(s.get("crash_recent_window", 0.5))    # seconds
        prior_win = float(s.get("crash_prior_window", 0.8))      # seconds
        iou_spike = float(s.get("crash_iou_spike", 0.25))        # overlap on contact
        iou_prior = float(s.get("crash_iou_prior", 0.08))        # must come from below
        # The overlap must cross from separate to contact within this window.
        # A collision does it in a frame or two; a car queuing up behind another
        # grows the same overlap gradually over several seconds.
        iou_lookback = float(s.get("crash_iou_lookback", 0.6))
        # How long after contact forms the wreck may still be confirmed.
        contact_window = float(s.get("crash_contact_window", 4.0))
        pair_min_speed = float(s.get("crash_pair_min_speed", 0.30))
        stopped_ratio = float(s.get("crash_stopped_ratio", 0.30))
        stopped_speed = float(s.get("crash_stopped_speed", 0.10))
        duration = float(s.get("crash_duration", 0.7))           # persistence
        cooldown = float(s.get("crash_cooldown", 30.0))

        now = ctx.now
        vehicles = self.vehicles(ctx)
        tracks = self._tracks.setdefault(ctx.camera_id, {})
        peaks = self._peak_speed.setdefault(ctx.camera_id, {})

        # --- update per-track motion history ---
        for v in vehicles:
            cx, cy = _centroid(v["box"])
            samples = tracks.setdefault(v["id"], [])
            samples.append((now, cx, cy, _diag(v["box"])))
            if len(samples) > MAX_SAMPLES:
                del samples[:-MAX_SAMPLES]

        alerts: List[dict] = []
        speeds: Dict[object, float] = {}
        drops: Dict[object, Tuple[float, float]] = {}

        for v in vehicles:
            samples = tracks.get(v["id"], [])
            recent = _mean_speed(samples, now - recent_win, now)
            if recent is not None:
                speeds[v["id"]] = recent
                peaks[v["id"]] = max(peaks.get(v["id"], 0.0), recent)
            drop = self._decel_hit(samples, now, recent_win, prior_win,
                                   min_speed, decel_ratio)
            if drop is not None:
                drops[v["id"]] = drop

        # --- ego-motion guard -------------------------------------------------
        # On a moving camera (dashcam, PTZ) every static object drifts across the
        # frame, so the moment the camera itself stops, every tracked vehicle
        # "decelerates" at once. A real crash stops one or two vehicles, not the
        # entire scene, so a synchronised stop is treated as camera motion.
        measured = [v for v in vehicles if v["id"] in speeds]
        ego_motion = (len(measured) >= 3
                      and len(drops) >= max(2, int(round(0.5 * len(measured)))))
        if ego_motion:
            logger.debug(f"[crash] cam={ctx.camera_id} EGO-MOTION suppressed: "
                         f"{len(drops)}/{len(measured)} vehicles decelerated together")
            for tid in list(drops):
                self._streaks.pop(f"{ctx.camera_id}_decel_{tid}", None)
            drops.clear()

        # --- signature 1: a tracked vehicle stops dead ---
        for v in vehicles:
            drop = drops.get(v["id"])
            key = f"{ctx.camera_id}_decel_{v['id']}"
            if not self._advance(key, drop is not None, now, duration):
                continue
            if not self.cooldown_ok(key, now, cooldown):
                continue
            self._streaks[key] = now      # restart after firing
            prior_speed, recent_speed = drop
            logger.debug(f"[crash] cam={ctx.camera_id} track={v['id']} DECEL "
                         f"prior={prior_speed:.2f} recent={recent_speed:.2f} diag/s")
            alerts.append(make_alert(
                camera_id=ctx.camera_id,
                event_type="crash",
                severity="critical",
                level="CRITICAL",
                title="Possible Vehicle Crash",
                detail=(f"A vehicle decelerated abruptly, from {prior_speed:.2f} to "
                        f"{recent_speed:.2f} box-lengths/sec, and stayed stopped for "
                        f"over {duration}s."),
                icon="\U0001F4A5",
                frame=ctx.frame,
                now=now,
            ))

        # --- signature 2: contact between vehicles, followed by a stop --------
        # A collision is not merely overlap: two cars driving in convoy overlap
        # on screen and keep moving, and two parked cars overlap constantly.
        # What marks a crash is an overlap that GREW, between vehicles that WERE
        # moving, which then STOP and stay overlapped.
        for i in range(len(vehicles)):
            for j in range(i + 1, len(vehicles)):
                a, b = vehicles[i], vehicles[j]
                pair_key = (ctx.camera_id, *sorted([str(a["id"]), str(b["id"])]))
                overlap = _iou(a["box"], b["box"])

                history = self._pair_iou.setdefault(pair_key, [])
                history.append((now, overlap))
                del history[:max(0, len(history) - MAX_SAMPLES)]
                self._pairs[pair_key] = {"iou": overlap, "t": now}

                # Latch the moment the overlap crossed from separate into
                # contact. It has to be remembered rather than tested every
                # frame: "the overlap just jumped" and "the vehicles have now
                # been stationary for half a second" are true at different
                # times, so requiring both at once can never match.
                window = [h for h in history if h[0] >= now - iou_lookback]
                crossed = (len(window) >= 2 and overlap >= iou_spike
                           and min(h[1] for h in window) < iou_prior)
                if crossed:
                    self._contact_at.setdefault(pair_key, now)
                contact_at = self._contact_at.get(pair_key)
                recent_contact = (contact_at is not None
                                  and now - contact_at <= contact_window)

                peak_a, peak_b = peaks.get(a["id"], 0.0), peaks.get(b["id"], 0.0)
                peak = max(peak_a, peak_b)
                now_a = speeds.get(a["id"], 0.0)
                now_b = speeds.get(b["id"], 0.0)
                # Absolute floor as well as a fraction of the observed peak: a
                # tracker re-acquires the wreck only AFTER the impact, so those
                # tracks have no fast history of their own to compare against.
                stopped = max(now_a, now_b) <= max(stopped_speed,
                                                   stopped_ratio * peak)

                key = f"{ctx.camera_id}_contact_{pair_key[1]}_{pair_key[2]}"
                hit = overlap >= iou_spike and recent_contact and stopped
                # Once the streak is running the overlap alone sustains it: the
                # moment the overlap grew is by definition in the past by then.
                sustained = hit or (key in self._streaks and overlap >= iou_spike)

                if not self._advance(key, sustained, now, duration):
                    continue
                if not self.cooldown_ok(key, now, cooldown):
                    continue
                self._streaks[key] = now
                logger.debug(f"[crash] cam={ctx.camera_id} CONTACT {a['id']}+{b['id']} "
                             f"iou={overlap:.2f} peaks=({peak_a:.2f},{peak_b:.2f}) "
                             f"now=({now_a:.2f},{now_b:.2f})")
                alerts.append(make_alert(
                    camera_id=ctx.camera_id,
                    event_type="crash",
                    severity="critical",
                    level="CRITICAL",
                    title="Possible Vehicle Collision",
                    detail=(f"Two vehicles made contact and stopped: overlap rose to "
                            f"{overlap:.2f} and both vehicles are stationary "
                            f"({max(now_a, now_b):.2f} box-lengths/sec), held for "
                            f"over {duration}s."),
                    icon="\U0001F4A5",
                    frame=ctx.frame,
                    now=now,
                ))

        # --- prune state for vehicles that left the frame ---
        for tid in [t for t, smp in tracks.items() if now - smp[-1][0] > TRACK_TTL]:
            del tracks[tid]
            peaks.pop(tid, None)
        for pk in [k for k, v in self._pairs.items()
                   if k[0] == ctx.camera_id and now - v["t"] > TRACK_TTL]:
            del self._pairs[pk]
            self._pair_iou.pop(pk, None)
            self._contact_at.pop(pk, None)

        return alerts
