"""
Threat score — a rolling 0-100 measure of how dangerous the situation is.

Every alert contributes a weight based on its severity, and that contribution
decays exponentially so the score falls back to calm on its own when nothing
further happens. A single critical event should be visible but not pin the
meter; a burst of them should saturate it.

    score(t) = min(100, sum over events of  weight * 0.5 ** (age / half_life))

Exponential decay (rather than a fixed window) means the score moves smoothly
instead of stepping down when an event drops out of the window, which is what
makes the dial pleasant to watch.

Pure in-memory and thread-safe: the alert dispatcher records from the asyncio
loop while the API reads from request threads. No dependencies.
"""
import logging
import threading
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Contribution of a single event, before decay. Tuned so that one critical
# event reads "elevated", two concurrent criticals read "high", and a sustained
# burst saturates.
SEVERITY_WEIGHTS: Dict[str, float] = {
    "critical": 40.0,
    "high": 25.0,
    "warning": 12.0,
    "info": 4.0,
}
DEFAULT_WEIGHT = 4.0

# Bands the UI colours against. (lower bound inclusive, label, colour)
BANDS = [
    (75.0, "CRITICAL", "#dc2626"),
    (50.0, "HIGH", "#ea580c"),
    (25.0, "ELEVATED", "#ca8a04"),
    (0.0, "NOMINAL", "#16a34a"),
]

DEFAULT_HALF_LIFE = 120.0     # seconds for a contribution to halve
MAX_EVENTS = 500              # hard cap on retained events
PRUNE_AFTER_HALF_LIVES = 8    # ~0.4% of original weight; safe to forget


def classify(score: float) -> Dict[str, str]:
    for threshold, label, colour in BANDS:
        if score >= threshold:
            return {"label": label, "color": colour}
    return {"label": "NOMINAL", "color": "#16a34a"}


class ThreatScoreService:
    """Accumulates decaying alert weights into a 0-100 score."""

    def __init__(self, half_life: float = DEFAULT_HALF_LIFE):
        self._lock = threading.Lock()
        self._events: List[dict] = []
        self.half_life = half_life

    # ---- ingest -----------------------------------------------------------
    def record(self, alert: Dict[str, Any], now: Optional[float] = None) -> None:
        """Register one alert. Cheap, non-blocking, never raises at the caller."""
        try:
            now = now if now is not None else time.time()
            severity = str(alert.get("severity", "info")).lower()
            weight = SEVERITY_WEIGHTS.get(severity, DEFAULT_WEIGHT)
            entry = {
                "at": now,
                "weight": weight,
                "severity": severity,
                "type": alert.get("type", "unknown"),
                "title": alert.get("title", ""),
                "camera_id": alert.get("camera_id"),
                "camera_name": alert.get("camera_name", ""),
                "icon": alert.get("icon", ""),
                "id": alert.get("id", ""),
            }
            with self._lock:
                self._events.append(entry)
                self._prune_locked(now)
            logger.debug(f"[threat] recorded {severity} (+{weight}) — "
                         f"{len(self._events)} live contributions")
        except Exception as e:
            # The score is a nice-to-have; never let it break alert dispatch.
            logger.error(f"[threat] failed to record alert: {e}")

    def _prune_locked(self, now: float) -> None:
        cutoff = now - (self.half_life * PRUNE_AFTER_HALF_LIVES)
        self._events = [e for e in self._events if e["at"] >= cutoff]
        if len(self._events) > MAX_EVENTS:
            self._events = self._events[-MAX_EVENTS:]

    # ---- query ------------------------------------------------------------
    def _decayed(self, entry: dict, at: float) -> float:
        age = at - entry["at"]
        if age < 0:
            return 0.0
        return entry["weight"] * (0.5 ** (age / self.half_life))

    def score_at(self, at: float, events: Optional[List[dict]] = None) -> float:
        """Score as it stood at time `at`, ignoring anything later."""
        events = self._events if events is None else events
        total = sum(self._decayed(e, at) for e in events if e["at"] <= at)
        return round(min(100.0, total), 1)

    def get_state(self, now: Optional[float] = None,
                  trend_window: float = 30.0,
                  top_n: int = 5) -> Dict[str, Any]:
        """Full snapshot for /api/threat."""
        now = now if now is not None else time.time()
        with self._lock:
            self._prune_locked(now)
            events = list(self._events)

        score = self.score_at(now, events)
        previous = self.score_at(now - trend_window, events)
        band = classify(score)

        # Which live events are actually driving the number right now.
        contributors = sorted(
            ({
                "id": e["id"],
                "type": e["type"],
                "title": e["title"],
                "severity": e["severity"],
                "icon": e["icon"],
                "camera_id": e["camera_id"],
                "camera_name": e["camera_name"],
                "age_seconds": round(now - e["at"], 1),
                "contribution": round(self._decayed(e, now), 1),
            } for e in events),
            key=lambda c: c["contribution"], reverse=True,
        )[:top_n]

        per_camera: Dict[str, float] = {}
        for e in events:
            key = str(e["camera_id"])
            per_camera[key] = round(per_camera.get(key, 0.0) + self._decayed(e, now), 1)

        return {
            "score": score,
            "level": band["label"],
            "color": band["color"],
            "previous_score": previous,
            "trend": round(score - previous, 1),
            "active_events": len(events),
            "half_life": self.half_life,
            "bands": [{"from": t, "label": l, "color": c} for t, l, c in reversed(BANDS)],
            "contributors": [c for c in contributors if c["contribution"] >= 0.1],
            "per_camera": per_camera,
            "updated_at": now,
        }

    def reset(self) -> None:
        with self._lock:
            self._events.clear()


# Singleton, mirroring ml_service / blockchain_service.
threat_service = ThreatScoreService()
