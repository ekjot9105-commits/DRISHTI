"""
Fight detection.

Heuristic (no extra model weights, runs on CPU alongside YOLO):
  1. Proximity — two tracked persons whose boxes overlap (IoU above a threshold).
  2. Motion energy — mean frame-to-frame absolute difference inside the pair's
     union ROI, which spikes for flailing limbs and stays low for two people
     merely standing close or walking past each other.
  3. Persistence — both conditions must hold for `fight_duration` seconds before
     an alert fires, which rejects momentary occlusions and crossings. The
     streak uses the same tolerance machinery as the fire detector: real
     flailing oscillates, so energy dips below threshold at every swing
     reversal. A hard reset on one sub-threshold frame made the streak
     unreachable in practice — `fight_streak_tolerance` absorbs short dips,
     `fight_min_hit_ratio` still demands the signature dominate the window, and
     `fight_max_gap` is wall-clock so frame rate cannot distort it.

Emits a CRITICAL `fight` event carrying `frame_data`, so the existing dispatcher
saves the snapshot to the Evidence Vault and hashes it into the chain.
"""
import logging
from typing import Dict, List, Tuple

import cv2
import numpy as np

from app.services.detectors.base import Detector, DetectorContext, make_alert, register

logger = logging.getLogger(__name__)


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


@register
class FightDetector(Detector):
    name = "fight"
    enabled_key = "fight_enabled"

    def __init__(self):
        super().__init__()
        self._prev_gray: Dict[int, np.ndarray] = {}
        # (camera_id, tid_a, tid_b) -> {"start": float, "last": float, "peak": float}
        self._pairs: Dict[Tuple[int, object, object], dict] = {}

    def _motion_energy(self, camera_id: int, gray: np.ndarray, roi) -> float:
        prev = self._prev_gray.get(camera_id)
        if prev is None or prev.shape != gray.shape:
            return 0.0
        x1, y1, x2, y2 = roi
        if x2 - x1 < 8 or y2 - y1 < 8:
            return 0.0
        diff = cv2.absdiff(prev[y1:y2, x1:x2], gray[y1:y2, x1:x2])
        return float(diff.mean())

    def _advance(self, key, hit: bool, now: float, duration: float,
                 tolerance: int, min_hit_ratio: float, max_gap: float,
                 camera_id: int) -> bool:
        """Update a pair's persistence streak. True once the signature has held.

        Same shape as FireDetector._advance: `tolerance` consecutive misses are
        forgiven, `max_gap` bounds the wall-clock silence between hits so a slow
        frame rate cannot stretch the window, and `min_hit_ratio` stops a long
        mostly-quiet streak from qualifying on tolerance alone.
        """
        state = self._pairs.get(key)

        if not hit:
            if state is None:
                return False
            state["misses"] += 1
            state["frames"] += 1
            gap = now - state["last_hit"]
            if state["misses"] > tolerance or gap > max_gap:
                logger.debug("[fight] cam=%s pair=%s streak BROKEN after %.2fs "
                             "(%d consecutive misses vs tol %d, gap %.2fs vs max %.2fs)",
                             camera_id, key[1:], now - state["start"],
                             state["misses"], tolerance, gap, max_gap)
                self._pairs.pop(key, None)
            return False

        if state is None:
            self._pairs[key] = {"start": now, "last_hit": now, "misses": 0,
                                "hits": 1, "frames": 1, "peak": 0.0}
            return False

        state["misses"] = 0
        state["last_hit"] = now
        state["hits"] += 1
        state["frames"] += 1

        if (now - state["start"]) < duration:
            return False

        ratio = state["hits"] / max(1, state["frames"])
        if ratio < min_hit_ratio:
            logger.debug("[fight] cam=%s pair=%s held %.2fs but only %d/%d frames hit "
                         "(%.2f < %.2f) - not firing",
                         camera_id, key[1:], now - state["start"],
                         state["hits"], state["frames"], ratio, min_hit_ratio)
            return False
        return True

    def detect(self, ctx: DetectorContext) -> List[dict]:
        s = ctx.settings
        iou_thresh = s.get("fight_iou", 0.10)
        energy_thresh = s.get("fight_motion_energy", 12.0)
        duration = s.get("fight_duration", 1.2)
        cooldown = s.get("fight_cooldown", 20.0)
        tolerance = int(s.get("fight_streak_tolerance", 3))
        min_hit_ratio = float(s.get("fight_min_hit_ratio", 0.30))
        max_gap = float(s.get("fight_max_gap", 0.5))

        alerts: List[dict] = []
        persons = ctx.persons()

        gray = cv2.cvtColor(ctx.frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        h, w = gray.shape[:2]

        if len(persons) >= 2:
            for i in range(len(persons)):
                for j in range(i + 1, len(persons)):
                    a, b = persons[i], persons[j]
                    overlap = _iou(a["box"], b["box"])
                    key = (ctx.camera_id, *sorted([str(a["id"]), str(b["id"])]))

                    energy = 0.0
                    if overlap >= iou_thresh:
                        # Union ROI, clamped to the frame
                        x1 = max(0, int(min(a["box"][0], b["box"][0])))
                        y1 = max(0, int(min(a["box"][1], b["box"][1])))
                        x2 = min(w, int(max(a["box"][2], b["box"][2])))
                        y2 = min(h, int(max(a["box"][3], b["box"][3])))
                        energy = self._motion_energy(ctx.camera_id, gray, (x1, y1, x2, y2))

                    hit = overlap >= iou_thresh and energy >= energy_thresh

                    # Losing contact is a miss the tolerance window can absorb,
                    # not an instant reset — a brief occlusion or an IoU dip
                    # mid-scuffle should not discard the streak.
                    if not hit and key not in self._pairs:
                        continue

                    if hit:
                        state = self._pairs.get(key)
                        if state is not None:
                            state["peak"] = max(state["peak"], energy)

                    if not self._advance(key, hit, ctx.now, duration, tolerance,
                                         min_hit_ratio, max_gap, ctx.camera_id):
                        continue

                    # Cooldown is per-camera, not per-pair: ByteTrack ID churn
                    # during a scuffle rewrites the track ids, and a pair-keyed
                    # cooldown let every new id pair fire again, producing
                    # duplicate alerts and duplicate emails for one incident.
                    if not self.cooldown_ok(f"{ctx.camera_id}_fight", ctx.now, cooldown):
                        continue

                    state = self._pairs[key]
                    peak = max(state["peak"], energy)
                    self._pairs[key] = {"start": ctx.now, "last_hit": ctx.now,
                                        "misses": 0, "hits": 1, "frames": 1,
                                        "peak": 0.0}
                    alerts.append(make_alert(
                        camera_id=ctx.camera_id,
                        event_type="fight",
                        severity="critical",
                        level="CRITICAL",
                        title="Physical Altercation Detected",
                        detail=(
                            f"Two subjects in sustained contact with violent motion "
                            f"(overlap {overlap:.2f}, motion energy {peak:.1f}) "
                            f"for over {duration}s."
                        ),
                        icon="🥊",
                        frame=ctx.frame,
                        now=ctx.now,
                    ))

        # Drop pair streaks that went stale (subjects separated or left the frame)
        # A pair that vanished entirely (subjects separated, or both tracks lost)
        # stops receiving misses, so drop it once it exceeds the same wall-clock
        # gap the tolerance window uses.
        for key in [k for k, v in self._pairs.items()
                    if k[0] == ctx.camera_id and ctx.now - v["last_hit"] > max_gap]:
            del self._pairs[key]

        self._prev_gray[ctx.camera_id] = gray
        return alerts
