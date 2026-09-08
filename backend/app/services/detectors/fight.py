"""
Fight detection.

Heuristic (no extra model weights, runs on CPU alongside YOLO):
  1. Proximity — two tracked persons whose boxes overlap (IoU above a threshold).
  2. Motion energy — mean frame-to-frame absolute difference inside the pair's
     union ROI, which spikes for flailing limbs and stays low for two people
     merely standing close or walking past each other.
  3. Persistence — both conditions must hold for `fight_duration` seconds before
     an alert fires, which rejects momentary occlusions and crossings.

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

    def detect(self, ctx: DetectorContext) -> List[dict]:
        s = ctx.settings
        iou_thresh = s.get("fight_iou", 0.10)
        energy_thresh = s.get("fight_motion_energy", 12.0)
        duration = s.get("fight_duration", 1.2)
        cooldown = s.get("fight_cooldown", 20.0)

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
                    if overlap < iou_thresh:
                        continue

                    # Union ROI, clamped to the frame
                    x1 = max(0, int(min(a["box"][0], b["box"][0])))
                    y1 = max(0, int(min(a["box"][1], b["box"][1])))
                    x2 = min(w, int(max(a["box"][2], b["box"][2])))
                    y2 = min(h, int(max(a["box"][3], b["box"][3])))
                    energy = self._motion_energy(ctx.camera_id, gray, (x1, y1, x2, y2))

                    key = (ctx.camera_id, *sorted([str(a["id"]), str(b["id"])]))
                    state = self._pairs.get(key)

                    if energy < energy_thresh:
                        # Contact without violent motion — reset the streak.
                        self._pairs.pop(key, None)
                        continue

                    if state is None:
                        self._pairs[key] = {"start": ctx.now, "last": ctx.now, "peak": energy}
                        continue

                    state["last"] = ctx.now
                    state["peak"] = max(state["peak"], energy)

                    if ctx.now - state["start"] < duration:
                        continue

                    inc_key = f"{ctx.camera_id}_fight_{key[1]}_{key[2]}"
                    if not self.cooldown_ok(inc_key, ctx.now, cooldown):
                        continue

                    state["start"] = ctx.now  # restart the streak after firing
                    alerts.append(make_alert(
                        camera_id=ctx.camera_id,
                        event_type="fight",
                        severity="critical",
                        level="CRITICAL",
                        title="Physical Altercation Detected",
                        detail=(
                            f"Two subjects in sustained contact with violent motion "
                            f"(overlap {overlap:.2f}, motion energy {state['peak']:.1f}) "
                            f"for over {duration}s."
                        ),
                        icon="🥊",
                        frame=ctx.frame,
                        now=ctx.now,
                    ))

        # Drop pair streaks that went stale (subjects separated or left the frame)
        for key in [k for k, v in self._pairs.items()
                    if k[0] == ctx.camera_id and ctx.now - v["last"] > 1.5]:
            del self._pairs[key]

        self._prev_gray[ctx.camera_id] = gray
        return alerts
