"""
NullChannel — logs the event and does nothing else.

Enabled by default with an `info` threshold so the fan-out path is exercisable
end to end with zero configuration: trigger any alert and it shows up in the
backend log. Also the reference implementation for real channels.
"""
import logging
from typing import Any, Dict

from app.services.notify.dispatcher import Channel, NotificationEvent, register

logger = logging.getLogger(__name__)


@register
class NullChannel(Channel):
    name = "null"
    default_enabled = True
    default_min_severity = "info"   # see everything

    async def send(self, event: NotificationEvent, settings: Dict[str, Any]) -> None:
        logger.info(f"[notify:null] {event.summary()}"
                    + (f" evidence={event.evidence_path}" if event.evidence_path else ""))
