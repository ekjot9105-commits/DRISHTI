"""
Fire & smoke detection.

Two-stage, and works with or without dedicated weights:

  1. Model stage (optional) - if a fire/smoke YOLO checkpoint is present in the
     backend directory (`fire.pt`, `fire_smoke.pt` or `$FIRE_MODEL`), its
     detections drive the candidate regions. Class names containing "fire" or
     "flame" map to FIRE, "smoke" to SMOKE.
  2. HSV + flicker gate - the signature must pass a colour test AND move.

Flame colour is a union of two HSV sub-bands, because a real flame is not one
colour: the core is blown out (very high V, washed-out S) while the periphery
is deeply saturated orange at a lower V. A single band misses one or the other.

Flicker is measured *inside the flame mask only*. A whole-frame mean is diluted
by the static background in proportion to how much of the scene is burning, so
a real fire filling 15% of the frame scored below a threshold that a synthetic
full-frame fire cleared easily. In-mask flicker is independent of fire size.

A short tolerance window lets the signature drop below threshold for a few
frames without discarding the accumulated streak - flames flicker by nature,
and a hard reset on a single miss loses real detections.

Alerts carry `frame_data`, so evidence capture and hashing happen downstream.
"""
import os
import logging
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from app.services.detectors.base import Detector, DetectorContext, make_alert, register

logger = logging.getLogger(__name__)

_WEIGHT_CANDIDATES = ("fire.pt", "fire_smoke.pt", "fire.onnx")

# Flame colour, as a union of two sub-bands (H is 0-179 in OpenCV).
# Core: blown-out yellow-white centre - very bright, washed-out saturation.
FLAME_CORE = (np.array([0, 0, 220], np.uint8), np.array([35, 90, 255], np.uint8))
# Periphery: saturated red-orange at mid-to-high brightness.
FLAME_PERIPHERY = (np.array([0, 90, 120], np.uint8), np.array([35, 255, 255], np.uint8))
# Smoke: desaturated mid-brightness grey. Matches asphalt and overcast sky too,
# which is why the heuristic path is opt-in (see `smoke_enabled`).
SMOKE_BAND = (np.array([0, 0, 80], np.uint8), np.array([180, 45, 210], np.uint8))

# In-mask flicker is meaningless on a handful of pixels.
MIN_MASK_PIXELS = 400


def _load_fire_model():
    """Load a fire/smoke checkpoint if the operator has dropped one in. Optional."""
    path = os.getenv("FIRE_MODEL")
    if not path or not os.path.exists(path):
        path = next((p for p in _WEIGHT_CANDIDATES if os.path.exists(p)), None)
    if not path:
        logger.info("No fire/smoke weights found - using HSV heuristic only.")
        return None
    try:
        from ultralytics import YOLO
        model = YOLO(path)
        logger.info(f"Fire/smoke model loaded: {path}")
        return model
    except Exception as e:
        logger.error(f"Failed to load fire model '{path}': {e}")
        return None


@register
class FireDetector(Detector):
    name = "fire"
    enabled_key = "fire_enabled"

    def __init__(self):
        super().__init__()
        self._model = None
        self._model_loaded = False
        self._prev_gray: Dict[int, "np.ndarray"] = {}
        # camera_id -> {"fire": {"start": ts, "misses": int} | None, "smoke": ...}
        self._streaks: Dict[int, Dict[str, Optional[dict]]] = {}

    # ---- stage 1: optional model ------------------------------------------
    def _regions(self, frame) -> List[Tuple[str, Tuple[int, int, int, int], float]]:
        """Return [(kind, (x1,y1,x2,y2), conf)] candidates. Empty when no model."""
        if not self._model_loaded:
            self._model = _load_fire_model()
            self._model_loaded = True
        if self._model is None:
            return []
        try:
            res = self._model.predict(frame, device="cpu", verbose=False)
        except Exception as e:
            logger.error(f"Fire model inference failed: {e}")
            return []
        out = []
        if not res or res[0].boxes is None:
            return out
        names = getattr(self._model, "names", {}) or {}
        for cls_id, conf, xyxy in zip(res[0].boxes.cls.int().cpu().tolist(),
                                      res[0].boxes.conf.cpu().tolist(),
                                      res[0].boxes.xyxy.cpu().tolist()):
            label = str(names.get(cls_id, cls_id)).lower()
            if "fire" in label or "flame" in label:
                kind = "fire"
            elif "smoke" in label:
                kind = "smoke"
            else:
                continue
            out.append((kind, tuple(int(v) for v in xyxy), float(conf)))
        return out

    # ---- stage 2: colour masks + in-mask flicker ---------------------------
    @staticmethod
    def flame_mask(hsv):
        """Union of the blown-out core and the saturated periphery."""
        return cv2.bitwise_or(cv2.inRange(hsv, *FLAME_CORE),
                              cv2.inRange(hsv, *FLAME_PERIPHERY))

    @staticmethod
    def smoke_mask(hsv):
        return cv2.inRange(hsv, *SMOKE_BAND)

    def _masked_flicker(self, camera_id: int, gray, mask) -> float:
        """Mean |frame difference| over masked pixels only (0.0 if too few)."""
        prev = self._prev_gray.get(camera_id)
        if prev is None or prev.shape != gray.shape:
            return 0.0
        if mask is None or np.count_nonzero(mask) < MIN_MASK_PIXELS:
            return 0.0
        return float(cv2.absdiff(prev, gray)[mask > 0].mean())

    def _advance(self, streak: dict, kind: str, hit: bool, now: float,
                 duration: float, tolerance: int, min_hit_ratio: float,
                 max_gap: float, camera_id: int) -> bool:
        """Update the persistence streak. True when it has held long enough.

        `tolerance` consecutive sub-threshold frames are forgiven, so a
        flickering flame does not lose its accumulated streak. Tolerance alone
        is not enough though: it is counted in frames, so on a slow feed a
        handful of forgiven misses buys a lot of wall-clock time. A scene with
        3 real hits in 125 frames reached 1.44s of a 1.50s gate that way.
        So the streak must ALSO be mostly hits - `min_hit_ratio` of the frames
        seen since it started, and no single gap between real hits may exceed
        `max_gap` seconds - frames are the wrong unit for forgiveness, since
        3 frames is 0.15s on a 20fps feed but 0.72s on a 4fps one.
        """
        state = streak[kind]

        if not hit:
            if state is None:
                return False
            state["misses"] += 1
            state["frames"] += 1
            gap = now - state["last_hit"]
            if state["misses"] > tolerance or gap > max_gap:
                logger.debug("[fire] cam=%s %s streak BROKEN after %.2fs "
                             "(%d consecutive misses vs tol %d, gap %.2fs vs max %.2fs)",
                             camera_id, kind, now - state["start"],
                             state["misses"], tolerance, gap, max_gap)
                streak[kind] = None
            return False

        if state is None:
            streak[kind] = {"start": now, "last_hit": now,
                            "misses": 0, "hits": 1, "frames": 1}
            return False

        state["misses"] = 0
        state["last_hit"] = now
        state["hits"] += 1
        state["frames"] += 1

        if (now - state["start"]) < duration:
            return False

        ratio = state["hits"] / max(1, state["frames"])
        if ratio < min_hit_ratio:
            logger.debug("[fire] cam=%s %s held %.2fs but only %d/%d frames hit "
                         "(%.2f < %.2f) - not firing",
                         camera_id, kind, now - state["start"],
                         state["hits"], state["frames"], ratio, min_hit_ratio)
            return False
        return True

    def detect(self, ctx: DetectorContext) -> List[dict]:
        s = ctx.settings
        fire_area = s.get("fire_area_ratio", 0.04)
        smoke_area = s.get("smoke_area_ratio", 0.15)
        flicker_min = s.get("fire_flicker", 12.0)
        duration = s.get("fire_duration", 1.5)
        cooldown = s.get("fire_cooldown", 60.0)
        tolerance = int(s.get("fire_streak_tolerance", 3))
        min_hit_ratio = float(s.get("fire_min_hit_ratio", 0.6))
        max_gap = float(s.get("fire_max_gap", 0.5))
        # The colour-only smoke gate also matches asphalt and overcast sky, so
        # it stays off unless explicitly enabled. Model-driven smoke is exempt.
        smoke_heuristic = bool(s.get("smoke_enabled", False))

        frame = ctx.frame
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape[:2]

        f_mask = self.flame_mask(hsv)
        f_px = int(np.count_nonzero(f_mask))
        fire_metric = f_px / f_mask.size
        fire_flicker = self._masked_flicker(ctx.camera_id, gray, f_mask)

        if smoke_heuristic:
            s_mask = self.smoke_mask(hsv)
            smoke_metric = float(np.count_nonzero(s_mask)) / s_mask.size
            smoke_flicker = self._masked_flicker(ctx.camera_id, gray, s_mask)
        else:
            smoke_metric = smoke_flicker = 0.0

        self._prev_gray[ctx.camera_id] = gray

        regions = self._regions(frame)
        if regions:
            # Model proposed regions - keep fire boxes that also look like flame.
            fire_hit = False
            for kind, (x1, y1, x2, y2), _conf in regions:
                if kind != "fire":
                    continue
                crop = hsv[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]
                if crop.size == 0:
                    continue
                crop_mask = self.flame_mask(crop)
                if np.count_nonzero(crop_mask) / crop_mask.size > 0.05:
                    fire_hit = True
                    break
            smoke_hit = any(r[0] == "smoke" for r in regions)
            fire_metric = max([r[2] for r in regions if r[0] == "fire"] or [0.0])
            smoke_metric = max([r[2] for r in regions if r[0] == "smoke"] or [0.0])
        else:
            fire_hit = fire_metric > fire_area and fire_flicker > flicker_min
            smoke_hit = (smoke_heuristic
                         and smoke_metric > smoke_area
                         and smoke_flicker > (flicker_min / 2.0))

        streak = self._streaks.setdefault(ctx.camera_id, {"fire": None, "smoke": None})
        alerts: List[dict] = []

        logger.debug(
            "[fire] cam=%s mode=%s %sx%s | flame=%.4f px=%d (need>%.4f) "
            "in-mask flicker=%.2f (need>%.2f) | smoke=%.4f (need>%.4f, heuristic=%s) "
            "| fire_hit=%s smoke_hit=%s | streak fire=%s misses=%s (need %.1fs, tol %d)",
            ctx.camera_id, "model" if regions else "hsv", w, h,
            fire_metric, f_px, fire_area, fire_flicker, flicker_min,
            smoke_metric, smoke_area, smoke_heuristic, fire_hit, smoke_hit,
            None if streak["fire"] is None else round(ctx.now - streak["fire"]["start"], 2),
            None if streak["fire"] is None else
            f'{streak["fire"]["misses"]} hits={streak["fire"]["hits"]}/{streak["fire"]["frames"]}',
            duration, tolerance,
        )

        for kind, hit, metric in (("fire", fire_hit, fire_metric),
                                  ("smoke", smoke_hit, smoke_metric)):
            if not self._advance(streak, kind, hit, ctx.now, duration,
                                 tolerance, min_hit_ratio, max_gap, ctx.camera_id):
                continue
            if not self.cooldown_ok(f"{ctx.camera_id}_{kind}", ctx.now, cooldown):
                continue
            # restart after firing
            streak[kind] = {"start": ctx.now, "last_hit": ctx.now,
                            "misses": 0, "hits": 1, "frames": 1}
            is_fire = kind == "fire"
            alerts.append(make_alert(
                camera_id=ctx.camera_id,
                event_type=kind,
                severity="critical" if is_fire else "high",
                level="CRITICAL" if is_fire else "PRIORITY ALPHA",
                title="Fire Detected" if is_fire else "Smoke Detected",
                detail=(f"Sustained {'flame' if is_fire else 'smoke'} signature "
                        f"(area {metric:.3f}, in-mask flicker "
                        f"{fire_flicker if is_fire else smoke_flicker:.1f}) "
                        f"held for over {duration}s."),
                icon="🔥" if is_fire else "💨",
                frame=frame,
                now=ctx.now,
            ))

        return alerts
