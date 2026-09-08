"""
Pluggable detector framework.

Every detector receives the same per-frame context (frame, tracked boxes, track
history, settings) and returns a list of alert dicts in the exact shape the
existing pipeline expects — `ml_inference` appends them to its own alerts list,
`video_ingestion` pushes them onto `alert_queue`, and `main.alert_dispatcher`
persists them, saves `frame_data` as evidence and broadcasts over WebSocket.
"""
import time
import uuid
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_REGISTRY: List["Detector"] = []


@dataclass
class DetectorContext:
    """Everything a detector may need for one frame of one camera."""
    camera_id: int
    frame: Any                      # BGR numpy array (raw, undrawn)
    boxes: List[dict]               # [{"id", "class", "conf", "box", "identity"}, ...]
    history: Dict[Any, dict]        # ml_service.object_history[camera_id]
    settings: Dict[str, Any]
    now: float = field(default_factory=time.time)

    def persons(self) -> List[dict]:
        """Tracked person boxes only (untracked detections have id '?')."""
        return [b for b in self.boxes if b.get("class") == "person" and b.get("id") != "?"]


def make_alert(camera_id: int, event_type: str, severity: str, level: str,
               title: str, detail: str, icon: str = "⚠️",
               frame=None, now: Optional[float] = None) -> dict:
    """Build an alert dict matching the existing event/evidence contract."""
    now = now or time.time()
    alert = {
        "id": f"inc_{int(now)}_{uuid.uuid4().hex[:6]}",
        "camera_id": camera_id,
        "type": event_type,
        "severity": severity,
        "level": level,
        "title": title,
        "detail": detail,
        "time": time.strftime("%H:%M:%S"),
        "icon": icon,
    }
    if frame is not None:
        # Consumed and popped by alert_dispatcher -> _save_evidence()
        alert["frame_data"] = frame
    return alert


class Detector(ABC):
    """Base class for all per-frame detectors.

    Subclasses set `name` / `enabled_key` and implement `detect()`. State that
    must survive between frames (previous frames, streak timers) belongs on the
    instance, keyed by camera_id.
    """
    name: str = "detector"
    enabled_key: Optional[str] = None   # settings key toggling this detector

    def __init__(self):
        self._cooldowns: Dict[str, float] = {}

    def is_enabled(self, settings: Dict[str, Any]) -> bool:
        if self.enabled_key is None:
            return True
        return bool(settings.get(self.enabled_key, True))

    def cooldown_ok(self, key: str, now: float, seconds: float) -> bool:
        """Incident-level dedup, same semantics as ml_service.incident_cache.

        A key that has never fired always passes — using 0.0 as the sentinel
        would suppress the first alert whenever the clock is small (offline
        replays, tests, any non-epoch timebase).
        """
        last = self._cooldowns.get(key)
        if last is not None and now - last < seconds:
            return False
        self._cooldowns[key] = now
        return True

    @abstractmethod
    def detect(self, ctx: DetectorContext) -> List[dict]:
        """Return zero or more alert dicts for this frame."""
        raise NotImplementedError


def register(detector_cls):
    """Class decorator: instantiate and add a detector to the registry."""
    instance = detector_cls()
    _REGISTRY.append(instance)
    logger.info(f"Detector registered: '{instance.name}' ({detector_cls.__name__})")
    return detector_cls


def get_detectors() -> List[Detector]:
    return list(_REGISTRY)


def run_all(ctx: DetectorContext) -> List[dict]:
    """Run every enabled detector, isolating failures so one cannot kill a frame."""
    alerts: List[dict] = []
    if not _REGISTRY:
        logger.warning("run_all: detector registry is EMPTY — no detectors imported")
    for det in _REGISTRY:
        try:
            if not det.is_enabled(ctx.settings):
                logger.debug(f"[detector] cam={ctx.camera_id} '{det.name}' SKIPPED "
                             f"({det.enabled_key}=False)")
                continue
            logger.debug(f"[detector] cam={ctx.camera_id} '{det.name}' INVOKED "
                         f"boxes={len(ctx.boxes)}")
            found = det.detect(ctx) or []
            if found:
                logger.debug(f"[detector] cam={ctx.camera_id} '{det.name}' emitted "
                             f"{[a.get('type') for a in found]}")
            alerts.extend(found)
        except Exception:
            # Full traceback — a silently swallowed detector bug is invisible otherwise.
            logger.exception(f"[detector] cam={ctx.camera_id} '{det.name}' RAISED")
    return alerts
