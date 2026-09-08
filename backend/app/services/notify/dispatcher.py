"""
Notification fan-out.

One entry point — `dispatch(alert)` — sends an event to every enabled channel.
Channels self-register with `@register`, exactly like the detectors in
`services/detectors/base.py`.

Non-blocking by construction. `dispatch()` is a plain function that schedules
each channel as its own asyncio task and returns immediately, so the caller
(the alert_dispatcher loop, which also drives WebSocket broadcast) never waits
on a channel. Every channel run is additionally wrapped in `asyncio.wait_for`,
so a dead SMTP server or a hanging HTTP request is abandoned after
`notify_timeout` seconds instead of accumulating forever. Blocking (non-async)
channel implementations are run on a dedicated daemon thread rather than on the
event loop, so a synchronous `smtplib` call cannot stall the frame pipeline
either. They deliberately do NOT use `asyncio.to_thread`: that shares one
bounded executor, so a hung send would hold a pool slot forever and healthy
channels would eventually queue behind the zombies. A daemon thread that is
abandoned on timeout costs one leaked thread and blocks nothing - not the loop,
not interpreter shutdown - and `notify_max_blocking_threads` caps how many can
pile up before sends are refused outright.

Failures are isolated per channel and logged with a full traceback: one broken
channel never prevents the others from firing.
"""
import asyncio
import inspect
import logging
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.core.settings_manager import load_settings

logger = logging.getLogger(__name__)

# Ordered low -> high. Anything unrecognised is treated as the lowest rank so an
# odd severity string can never escalate past a channel's threshold.
SEVERITY_ORDER: Dict[str, int] = {"info": 0, "warning": 1, "high": 2, "critical": 3}
DEFAULT_SEVERITY = "info"

_REGISTRY: List["Channel"] = []

# Strong references to in-flight tasks. asyncio only holds weak ones, so without
# this a channel task can be garbage collected mid-send.
_INFLIGHT: set = set()


def severity_rank(severity: Optional[str]) -> int:
    return SEVERITY_ORDER.get((severity or DEFAULT_SEVERITY).lower(), 0)


@dataclass
class NotificationEvent:
    """The stable payload handed to every channel.

    Built from the alert dict already flowing through `alert_queue`, so channels
    never have to know the shape of that dict or of the DB row.
    """
    id: str = ""
    db_id: Optional[int] = None
    camera_id: Optional[int] = None
    camera_name: str = ""
    type: str = "unknown"
    severity: str = DEFAULT_SEVERITY
    level: str = ""
    title: str = ""
    detail: str = ""
    time: str = ""
    icon: str = ""
    has_evidence: bool = False
    evidence_path: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def rank(self) -> int:
        return severity_rank(self.severity)

    @classmethod
    def from_alert(cls, alert: Dict[str, Any]) -> "NotificationEvent":
        db_id = alert.get("db_id")
        has_evidence = bool(alert.get("has_evidence"))
        # Written asynchronously by _save_evidence(); may not exist on disk yet,
        # so channels must tolerate a missing file.
        evidence_path = f"data/evidence/evt_{db_id}.jpg" if (has_evidence and db_id) else None
        return cls(
            id=str(alert.get("id", "")),
            db_id=db_id,
            camera_id=alert.get("camera_id"),
            camera_name=alert.get("camera_name", ""),
            type=alert.get("type", "unknown"),
            severity=alert.get("severity", DEFAULT_SEVERITY),
            level=alert.get("level", ""),
            title=alert.get("title", ""),
            detail=alert.get("detail", ""),
            time=alert.get("time", ""),
            icon=alert.get("icon", ""),
            has_evidence=has_evidence,
            evidence_path=evidence_path,
            # `frame_data` is popped upstream; this is the JSON-safe remainder.
            raw={k: v for k, v in alert.items() if k != "frame_data"},
        )

    def summary(self) -> str:
        return (f"{self.icon} [{self.level or self.severity.upper()}] {self.title} "
                f"— {self.detail} (camera: {self.camera_name or self.camera_id}, "
                f"event {self.db_id or self.id})")


class Channel(ABC):
    """Base class for notification channels.

    Subclasses set `name` and implement `send()`. `send()` may be either a
    coroutine or a plain blocking function — the dispatcher detects which and
    runs blocking ones in a thread so they cannot stall the event loop.

    Settings keys are derived from the name:
      notify_<name>_enabled       bool   (default: `default_enabled`)
      notify_<name>_min_severity  str    (default: `default_min_severity`)
    """
    name: str = "channel"
    default_enabled: bool = False
    default_min_severity: str = "critical"

    @property
    def enabled_key(self) -> str:
        return f"notify_{self.name}_enabled"

    @property
    def threshold_key(self) -> str:
        return f"notify_{self.name}_min_severity"

    def is_enabled(self, settings: Dict[str, Any]) -> bool:
        return bool(settings.get(self.enabled_key, self.default_enabled))

    def min_severity(self, settings: Dict[str, Any]) -> str:
        return str(settings.get(self.threshold_key, self.default_min_severity))

    def meets_threshold(self, event: NotificationEvent, settings: Dict[str, Any]) -> bool:
        return event.rank >= severity_rank(self.min_severity(settings))

    @abstractmethod
    def send(self, event: NotificationEvent, settings: Dict[str, Any]):
        """Deliver one event. May be `async def` or a plain blocking function."""
        raise NotImplementedError


def register(channel_cls):
    """Class decorator: instantiate and add a channel to the registry."""
    instance = channel_cls()
    _REGISTRY.append(instance)
    logger.info(f"Notification channel registered: '{instance.name}' ({channel_cls.__name__})")
    return channel_cls


def get_channels() -> List[Channel]:
    return list(_REGISTRY)


# Live daemon threads running blocking channel sends, including abandoned ones.
_blocking_threads = 0
_blocking_lock = threading.Lock()


async def _call_blocking(channel: Channel, event: NotificationEvent,
                         settings: Dict[str, Any], max_threads: int):
    """Run a blocking `send` on a daemon thread, bridged back to the loop.

    If the caller times out and drops us, the thread is simply abandoned: it is
    a daemon, so it never blocks interpreter shutdown, and it holds no shared
    executor slot. The counter caps how many such zombies may accumulate.
    """
    global _blocking_threads

    with _blocking_lock:
        if _blocking_threads >= max_threads:
            raise RuntimeError(
                f"refusing blocking send: {_blocking_threads} blocking channel "
                f"threads already live (notify_max_blocking_threads={max_threads}) "
                f"— a channel is probably hung")
        _blocking_threads += 1

    loop = asyncio.get_running_loop()
    future = loop.create_future()

    def _resolve(setter, value):
        # The future is already done if wait_for cancelled us; just drop the result.
        if not future.done():
            setter(value)

    def _runner():
        global _blocking_threads
        try:
            result = channel.send(event, settings)
        except BaseException as exc:  # noqa: BLE001 - reported through the future
            loop.call_soon_threadsafe(_resolve, future.set_exception, exc)
        else:
            loop.call_soon_threadsafe(_resolve, future.set_result, result)
        finally:
            with _blocking_lock:
                _blocking_threads -= 1

    threading.Thread(target=_runner, daemon=True,
                     name=f"notify-{channel.name}").start()
    return await future


def blocking_thread_count() -> int:
    """Live blocking-channel threads, abandoned ones included. For diagnostics."""
    with _blocking_lock:
        return _blocking_threads


async def _run_channel(channel: Channel, event: NotificationEvent,
                       settings: Dict[str, Any], timeout: float) -> bool:
    """Run one channel under a timeout, isolating and logging every failure."""
    max_threads = int(settings.get("notify_max_blocking_threads", 16))
    try:
        if inspect.iscoroutinefunction(channel.send):
            await asyncio.wait_for(channel.send(event, settings), timeout)
        else:
            # Blocking channel (smtplib, requests, ...) — keep it off the loop.
            await asyncio.wait_for(
                _call_blocking(channel, event, settings, max_threads), timeout)
        logger.debug(f"[notify] channel '{channel.name}' SENT event={event.id} "
                     f"severity={event.severity}")
        return True
    except asyncio.TimeoutError:
        logger.error(f"[notify] channel '{channel.name}' TIMED OUT after {timeout}s "
                     f"for event={event.id} — abandoned "
                     f"(live blocking threads: {blocking_thread_count()})")
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception(f"[notify] channel '{channel.name}' RAISED for event={event.id}")
    return False


def dispatch(alert: Dict[str, Any], settings: Optional[Dict[str, Any]] = None) -> List[asyncio.Task]:
    """Fan one alert out to every enabled channel. Returns immediately.

    Returns the scheduled tasks (useful in tests); callers in the hot path
    should ignore the return value rather than awaiting it.
    """
    settings = settings if settings is not None else load_settings()

    if not settings.get("notify_enabled", True):
        logger.debug("[notify] dispatch SKIPPED — notify_enabled=False")
        return []

    event = NotificationEvent.from_alert(alert)

    if not _REGISTRY:
        logger.warning("[notify] channel registry is EMPTY — no channels imported")
        return []

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # Called from a sync context (a worker thread or a script). Never block
        # the caller — say so rather than silently dropping the event.
        logger.error(f"[notify] dispatch called with no running event loop — "
                     f"event={event.id} not sent. Use dispatch_and_wait() instead.")
        return []

    timeout = float(settings.get("notify_timeout", 10.0))
    tasks: List[asyncio.Task] = []

    for channel in _REGISTRY:
        if not channel.is_enabled(settings):
            logger.debug(f"[notify] channel '{channel.name}' SKIPPED "
                         f"({channel.enabled_key}=False)")
            continue
        if not channel.meets_threshold(event, settings):
            logger.debug(f"[notify] channel '{channel.name}' BELOW THRESHOLD "
                         f"(event={event.severity}, needs "
                         f"{channel.min_severity(settings)}) event={event.id}")
            continue

        logger.debug(f"[notify] channel '{channel.name}' DISPATCHED event={event.id} "
                     f"severity={event.severity}")
        task = asyncio.create_task(_run_channel(channel, event, settings, timeout))
        _INFLIGHT.add(task)
        task.add_done_callback(_INFLIGHT.discard)
        tasks.append(task)

    if not tasks:
        logger.debug(f"[notify] event={event.id} severity={event.severity} "
                     f"matched no enabled channel")
    return tasks


async def dispatch_and_wait(alert: Dict[str, Any],
                            settings: Optional[Dict[str, Any]] = None) -> List[bool]:
    """Same fan-out, but await completion. For tests and the settings test-send.

    Never use this on the frame path — it waits for the slowest channel.
    """
    tasks = dispatch(alert, settings)
    if not tasks:
        return []
    return list(await asyncio.gather(*tasks, return_exceptions=False))
