"""
Fire & smoke detection.

Two-stage, and works with or without dedicated weights:

  1. Model stage (optional) - if a fire/smoke YOLO checkpoint is present in the
     backend directory (`fire.pt`, `fire_smoke.pt` or `$FIRE_MODEL`), its
     detections drive the candidate regions.
  2. Structural HSV stage - the default. Colour alone is not enough: sky, bright
     car bodies, road glare and skin all land in the same hue band. So instead
     of measuring colour over the whole frame, candidate pixels are grouped into
     connected regions and each region must look like a flame STRUCTURALLY:

       * a bright washed-out core AND a saturated orange periphery, spatially
         ADJACENT (a flame has a hot centre wrapped in orange; glare and sky are
         core-only, with nothing around them)
       * a core:periphery ratio inside a band - neither all-core (glare, sky)
         nor all-periphery (a red wall)
       * saturation variance across the region - fire is a gradient from white
         through yellow to deep orange; a painted panel or a patch of sky is
         near-uniform
       * hue variance - flame hue shifts frame to frame, paintwork does not
       * flicker measured INSIDE the region only, so a small fire in a large
         static scene is not averaged away

Every gate is required. Measured on the demo clips, no single gate separates
fire from a daylight street - car_crash.mp4 contains regions that individually
reach sat_std 72 and adj_frac 60 - but the conjunction rejects all of them,
with most regions failing several gates at once.

A candidate must then persist for `fire_duration`, tolerating a few
sub-threshold frames, before an alert fires.

The colour-only SMOKE heuristic remains opt-in (`smoke_enabled`, default off):
its band also matches asphalt and overcast sky, which is a false-alarm
generator. Smoke from real weights is unaffected by that flag.

Alerts carry `frame_data`, so evidence capture and hashing happen downstream.
"""
import os
import logging
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

from app.services.detectors.base import Detector, DetectorContext, make_alert, register

logger = logging.getLogger(__name__)

_WEIGHT_CANDIDATES = ("fire.pt", "fire_smoke.pt", "fire.onnx")

# Flame hue band (OpenCV H is 0-179): red -> orange -> yellow.
# Core: blown-out yellow-white centre - very bright, washed-out saturation.
FLAME_CORE = (np.array([0, 0, 220], np.uint8), np.array([35, 90, 255], np.uint8))
# Periphery: saturated red-orange at mid-to-high brightness.
FLAME_PERIPHERY = (np.array([0, 90, 120], np.uint8), np.array([35, 255, 255], np.uint8))
# Smoke: desaturated mid-brightness grey. Matches asphalt and overcast sky too,
# which is why the heuristic path is opt-in (see `smoke_enabled`).
SMOKE_BAND = (np.array([0, 0, 80], np.uint8), np.array([180, 45, 210], np.uint8))

# Morphology kernel used both to clean the mask and to test core/periphery
# adjacency (dilating the core by this much and intersecting the periphery).
KERNEL = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))

# In-region flicker is meaningless on a handful of pixels.
MIN_MASK_PIXELS = 400


def _load_fire_model():
    """Load a fire/smoke checkpoint if the operator has dropped one in. Optional."""
    path = os.getenv("FIRE_MODEL")
    if not path or not os.path.exists(path):
        path = next((p for p in _WEIGHT_CANDIDATES if os.path.exists(p)), None)
    if not path:
        logger.info("No fire/smoke weights found - using structural HSV analysis only.")
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
        # camera_id -> {"fire": {...} | None, "smoke": {...} | None}
        self._streaks: Dict[int, Dict[str, Optional[dict]]] = {}

    # ---- stage 1: optional model ------------------------------------------
    def _model_regions(self, frame) -> List[Tuple[str, Tuple[int, int, int, int], float]]:
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

    # ---- stage 2: structural region analysis ------------------------------
    @staticmethod
    def flame_masks(hsv):
        """Core, periphery and cleaned union masks for the flame hue band."""
        core = cv2.inRange(hsv, *FLAME_CORE)
        periphery = cv2.inRange(hsv, *FLAME_PERIPHERY)
        union = cv2.morphologyEx(cv2.bitwise_or(core, periphery),
                                 cv2.MORPH_OPEN, KERNEL)
        return core, periphery, union

    @staticmethod
    def smoke_mask(hsv):
        return cv2.inRange(hsv, *SMOKE_BAND)

    def flame_candidates(self, hsv, gray, prev_gray,
                         min_region_px: int) -> List[Dict[str, Any]]:
        """Per-region structural features for every candidate flame blob."""
        core, periphery, union = self.flame_masks(hsv)
        count, labels, stats, _cents = cv2.connectedComponentsWithStats(union, 8)
        # Where the core physically touches the periphery.
        adjacency = cv2.bitwise_and(cv2.dilate(core, KERNEL), periphery)
        diff = (cv2.absdiff(prev_gray, gray)
                if prev_gray is not None and prev_gray.shape == gray.shape else None)

        h, w = gray.shape[:2]
        frame_px = float(h * w)
        out: List[Dict[str, Any]] = []
        for i in range(1, count):
            area = int(stats[i, cv2.CC_STAT_AREA])
            if area < min_region_px:
                continue
            region = labels == i
            core_px = int(np.count_nonzero(core[region]))
            peri_px = int(np.count_nonzero(periphery[region]))
            total = core_px + peri_px
            if total == 0:
                continue
            hues = hsv[:, :, 0][region].astype(np.float32)
            sats = hsv[:, :, 1][region].astype(np.float32)
            out.append({
                "area_frac": area / frame_px,
                "area_px": area,
                # Balance of hot core against orange surround.
                "core_frac": core_px / total,
                # How much of the smaller of the two touches the other.
                "adj_frac": int(np.count_nonzero(adjacency[region])) / max(1, min(core_px, peri_px)),
                "hue_std": float(np.std(hues)),
                "sat_std": float(np.std(sats)),
                "flicker": float(diff[region].mean()) if diff is not None else 0.0,
            })
        return out

    @staticmethod
    def region_passes(region: Dict[str, Any], s: Dict[str, Any]) -> bool:
        """Every structural gate must hold - see the module docstring."""
        return (region["area_frac"] >= float(s.get("fire_area_ratio", 0.004))
                and float(s.get("fire_core_frac_min", 0.01))
                    <= region["core_frac"]
                    <= float(s.get("fire_core_frac_max", 0.95))
                and region["adj_frac"] >= float(s.get("fire_adjacency_min", 0.15))
                and region["sat_std"] >= float(s.get("fire_sat_std_min", 12.0))
                and region["hue_std"] >= float(s.get("fire_hue_std_min", 1.5))
                and region["flicker"] >= float(s.get("fire_flicker", 6.0)))

    def _masked_flicker(self, camera_id: int, gray, mask) -> float:
        """Mean |frame difference| over masked pixels only (0.0 if too few)."""
        prev = self._prev_gray.get(camera_id)
        if prev is None or prev.shape != gray.shape:
            return 0.0
        if mask is None or np.count_nonzero(mask) < MIN_MASK_PIXELS:
            return 0.0
        return float(cv2.absdiff(prev, gray)[mask > 0].mean())

    # ---- persistence ------------------------------------------------------
    def _advance(self, streak: dict, kind: str, hit: bool, now: float,
                 duration: float, tolerance: int, min_hit_ratio: float,
                 max_gap: float, camera_id: int) -> bool:
        """Update the persistence streak. True once the signature has held."""
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

    # ---- main -------------------------------------------------------------
    def detect(self, ctx: DetectorContext) -> List[dict]:
        s = ctx.settings
        smoke_area = float(s.get("smoke_area_ratio", 0.15))
        flicker_min = float(s.get("fire_flicker", 6.0))
        duration = float(s.get("fire_duration", 1.5))
        cooldown = float(s.get("fire_cooldown", 60.0))
        tolerance = int(s.get("fire_streak_tolerance", 3))
        min_hit_ratio = float(s.get("fire_min_hit_ratio", 0.6))
        max_gap = float(s.get("fire_max_gap", 0.5))
        min_region_px = int(s.get("fire_min_region_px", 250))
        smoke_heuristic = bool(s.get("smoke_enabled", False))

        frame = ctx.frame
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        prev_gray = self._prev_gray.get(ctx.camera_id)
        h, w = gray.shape[:2]

        candidates = self.flame_candidates(hsv, gray, prev_gray, min_region_px)
        passing = [r for r in candidates if self.region_passes(r, s)]
        best = max(passing, key=lambda r: r["area_frac"]) if passing else (
            max(candidates, key=lambda r: r["area_frac"]) if candidates else None)

        fire_hit = bool(passing)
        fire_metric = best["area_frac"] if best else 0.0
        fire_flicker = best["flicker"] if best else 0.0

        if smoke_heuristic:
            s_mask = self.smoke_mask(hsv)
            smoke_metric = float(np.count_nonzero(s_mask)) / s_mask.size
            smoke_flicker = self._masked_flicker(ctx.camera_id, gray, s_mask)
            smoke_hit = smoke_metric > smoke_area and smoke_flicker > (flicker_min / 2.0)
        else:
            smoke_metric = smoke_flicker = 0.0
            smoke_hit = False

        self._prev_gray[ctx.camera_id] = gray

        model_regions = self._model_regions(frame)
        if model_regions:
            # Weights present: their boxes decide, but a fire box still has to
            # contain something structurally flame-like.
            fire_hit = False
            for kind, (x1, y1, x2, y2), _conf in model_regions:
                if kind != "fire":
                    continue
                crop = hsv[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]
                if crop.size == 0:
                    continue
                crop_gray = gray[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]
                crop_prev = (prev_gray[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]
                             if prev_gray is not None and prev_gray.shape == gray.shape else None)
                if any(self.region_passes(r, s)
                       for r in self.flame_candidates(crop, crop_gray, crop_prev,
                                                      max(50, min_region_px // 4))):
                    fire_hit = True
                    break
            smoke_hit = any(r[0] == "smoke" for r in model_regions)
            fire_metric = max([r[2] for r in model_regions if r[0] == "fire"] or [0.0])
            smoke_metric = max([r[2] for r in model_regions if r[0] == "smoke"] or [0.0])

        streak = self._streaks.setdefault(ctx.camera_id, {"fire": None, "smoke": None})
        alerts: List[dict] = []

        logger.debug(
            "[fire] cam=%s mode=%s %sx%s | regions=%d passing=%d | best "
            "area=%.4f core=%.2f adj=%.2f sat_std=%.1f hue_std=%.1f flicker=%.1f "
            "| fire_hit=%s | streak=%s",
            ctx.camera_id, "model" if model_regions else "hsv", w, h,
            len(candidates), len(passing),
            fire_metric,
            best["core_frac"] if best else -1.0,
            best["adj_frac"] if best else -1.0,
            best["sat_std"] if best else -1.0,
            best["hue_std"] if best else -1.0,
            fire_flicker,
            fire_hit,
            None if streak["fire"] is None else
            f'{round(ctx.now - streak["fire"]["start"], 2)}s '
            f'hits={streak["fire"]["hits"]}/{streak["fire"]["frames"]}',
        )

        for kind, hit, metric in (("fire", fire_hit, fire_metric),
                                  ("smoke", smoke_hit, smoke_metric)):
            if not self._advance(streak, kind, hit, ctx.now, duration,
                                 tolerance, min_hit_ratio, max_gap, ctx.camera_id):
                continue
            if not self.cooldown_ok(f"{ctx.camera_id}_{kind}", ctx.now, cooldown):
                continue
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
                        f"(region {metric:.3f} of frame, in-region flicker "
                        f"{fire_flicker if is_fire else smoke_flicker:.1f}) "
                        f"held for over {duration}s."),
                icon="\U0001F525" if is_fire else "\U0001F4A8",
                frame=frame,
                now=ctx.now,
            ))

        return alerts
