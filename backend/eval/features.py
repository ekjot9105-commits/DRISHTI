"""Per-frame diagnostic features, so a result explains itself.

Everything here calls the detectors' own code read-only - `flame_candidates`
and `region_passes` from FireDetector, `_iou` from the fight detector - so the
numbers reported are the same ones the gates actually compare against. Nothing
in this module mutates detector state.
"""
from statistics import median
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

from app.services.detectors.fight import _iou

# Feature -> which detector it explains, in report order.
FIRE_FEATURES = ["flame_area_frac", "core_frac", "adj_frac",
                 "sat_std", "hue_std", "in_region_flicker"]
FIGHT_FEATURES = ["pair_iou", "motion_energy", "longest_contact_s"]
ALL_FEATURES = FIRE_FEATURES + FIGHT_FEATURES


class FeatureCollector:
    """Accumulates per-frame features for one clip."""

    def __init__(self, fire_detector, settings: Dict[str, Any], fps: float):
        self._fire = fire_detector
        self._s = settings
        self._fps = fps
        self._prev_gray: Optional[np.ndarray] = None

        self._fire_rows: List[Dict[str, float]] = []
        self._pair_iou: List[float] = []
        self._energy: List[float] = []

        # Longest unbroken run of frames carrying a contacting person pair.
        self._contact_run = 0
        self._contact_best = 0
        # Every person pair per frame, threshold-independent, so fight
        # thresholds can be swept offline without re-running YOLO.
        self._pair_frames: List[List[List[float]]] = []
        self._frames = 0
        self._passing_fire_frames = 0

    # ---- per frame --------------------------------------------------------
    def observe(self, frame: np.ndarray, boxes: List[dict]) -> None:
        self._frames += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)   # fight uses a blurred gray
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        self._observe_fire(hsv, gray)
        self._observe_fight(blurred, boxes)

        self._prev_gray = gray

    def _observe_fire(self, hsv, gray) -> None:
        min_px = int(self._s.get("fire_min_region_px", 250))
        try:
            regions = self._fire.flame_candidates(hsv, gray, self._prev_gray, min_px)
        except Exception:
            return
        if not regions:
            return
        # The region the detector would judge on: the largest candidate.
        best = max(regions, key=lambda r: r["area_frac"])
        self._fire_rows.append({
            "flame_area_frac": best["area_frac"],
            "core_frac": best["core_frac"],
            "adj_frac": best["adj_frac"],
            "sat_std": best["sat_std"],
            "hue_std": best["hue_std"],
            "in_region_flicker": best["flicker"],
        })
        if any(self._fire.region_passes(r, self._s) for r in regions):
            self._passing_fire_frames += 1

    def _observe_fight(self, blurred_gray, boxes: List[dict]) -> None:
        persons = [b for b in boxes
                   if b.get("class") == "person" and b.get("id") != "?"
                   and not b.get("ghost")]
        iou_thresh = float(self._s.get("fight_iou", 0.10))

        best_iou, best_energy, contact = 0.0, 0.0, False
        frame_pairs: List[List[float]] = []
        for i in range(len(persons)):
            for j in range(i + 1, len(persons)):
                overlap = _iou(persons[i]["box"], persons[j]["box"])
                if overlap <= 0.0:
                    continue
                energy = self._roi_energy(blurred_gray,
                                          persons[i]["box"], persons[j]["box"])
                frame_pairs.append([str(persons[i]["id"]), str(persons[j]["id"]),
                                    round(overlap, 4), round(energy, 3)])
                if overlap < iou_thresh or overlap <= best_iou:
                    continue
                best_iou, best_energy, contact = overlap, energy, True
        self._pair_frames.append(frame_pairs)

        if contact:
            self._pair_iou.append(best_iou)
            self._energy.append(best_energy)
            self._contact_run += 1
            self._contact_best = max(self._contact_best, self._contact_run)
        else:
            self._contact_run = 0

    def _roi_energy(self, blurred_gray, box_a, box_b) -> float:
        if self._prev_gray is None or self._prev_gray.shape != blurred_gray.shape:
            return 0.0
        h, w = blurred_gray.shape[:2]
        x1 = max(0, int(min(box_a[0], box_b[0])))
        y1 = max(0, int(min(box_a[1], box_b[1])))
        x2 = min(w, int(max(box_a[2], box_b[2])))
        y2 = min(h, int(max(box_a[3], box_b[3])))
        if x2 - x1 < 8 or y2 - y1 < 8:
            return 0.0
        prev = cv2.GaussianBlur(self._prev_gray, (5, 5), 0)
        return float(cv2.absdiff(prev[y1:y2, x1:x2], blurred_gray[y1:y2, x1:x2]).mean())

    # ---- summary ----------------------------------------------------------
    def summary(self) -> Dict[str, Any]:
        def med(values: List[float]) -> Optional[float]:
            return float(median(values)) if values else None

        out: Dict[str, Any] = {}
        for key in FIRE_FEATURES:
            out[key] = med([row[key] for row in self._fire_rows])
        out["pair_iou"] = med(self._pair_iou)
        out["motion_energy"] = med(self._energy)
        out["longest_contact_s"] = round(self._contact_best / self._fps, 2)
        out["_frames"] = self._frames
        out["_frames_with_flame_region"] = len(self._fire_rows)
        out["_frames_passing_fire_gates"] = self._passing_fire_frames
        out["_frames_with_contact_pair"] = len(self._pair_iou)
        return out

    def pair_frames(self) -> List[List[List[float]]]:
        """Per frame, [[id_a, id_b, iou, energy], ...] for every overlapping pair.

        Track ids are kept because the fight streak is keyed per pair - a
        sweep that ignored identity would model a detector that does not exist.
        """
        return self._pair_frames
