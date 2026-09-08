"""
Email notification channel — HTML incident report with the evidence frame
embedded inline as a CID attachment (not a hotlink, so it renders in clients
that block remote images and survives the mail leaving the LAN).

Configuration comes from the environment only; nothing is hardcoded:

    SMTP_HOST      smtp.gmail.com
    SMTP_PORT      587
    SMTP_USER      account used to authenticate
    SMTP_PASSWORD  app password (Gmail: 16-char App Password, 2FA required)
    SMTP_FROM      optional display From, defaults to SMTP_USER
    SMTP_TO        comma-separated recipients
    SMTP_USE_TLS   STARTTLS on 587 (default true)
    SMTP_USE_SSL   implicit TLS on 465 (default false)

With SMTP_HOST, SMTP_USER, SMTP_PASSWORD or SMTP_TO missing the channel logs
once and skips every send, so a fresh clone boots with no configuration.

`send()` is deliberately a plain blocking function: the dispatcher detects that
and runs it on its own daemon thread, so smtplib's socket timeouts and the
evidence wait below never touch the event loop or the frame pipeline.
"""
import logging
import os
import smtplib
import time
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.services.notify.dispatcher import Channel, NotificationEvent, register

logger = logging.getLogger(__name__)

# Severity -> accent colour for the report header.
SEVERITY_COLOURS = {
    "critical": "#dc2626",
    "high": "#ea580c",
    "warning": "#ca8a04",
    "info": "#0284c7",
}

# A JPEG ends with FFD9. Used to confirm the evidence file is fully flushed
# before we attach it, rather than trusting a non-zero size.
JPEG_EOI = b"\xff\xd9"


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


def _env_bool(name: str, default: bool) -> bool:
    raw = _env(name)
    if not raw:
        return default
    return raw.lower() in ("1", "true", "yes", "on")


def smtp_config() -> Optional[Dict[str, Any]]:
    """Read SMTP settings from the environment. None when incomplete."""
    host = _env("SMTP_HOST")
    user = _env("SMTP_USER")
    password = _env("SMTP_PASSWORD")
    recipients = [a.strip() for a in _env("SMTP_TO").split(",") if a.strip()]

    missing = [n for n, v in (("SMTP_HOST", host), ("SMTP_USER", user),
                              ("SMTP_PASSWORD", password), ("SMTP_TO", recipients)) if not v]
    if missing:
        return {"_missing": missing}

    return {
        "host": host,
        "port": int(_env("SMTP_PORT", "587") or 587),
        "user": user,
        "password": password,
        "sender": _env("SMTP_FROM") or user,
        "recipients": recipients,
        "use_tls": _env_bool("SMTP_USE_TLS", True),
        "use_ssl": _env_bool("SMTP_USE_SSL", False),
    }


def wait_for_evidence(path: Optional[str], timeout: float,
                      poll: float = 0.1) -> Optional[bytes]:
    """Bounded wait for the evidence JPEG, returning its bytes or None.

    `_save_evidence()` writes the frame asynchronously after the alert is
    already on its way here, so the file usually does not exist yet. We wait a
    short bounded time on our own daemon thread - the dispatcher is never
    blocked - and give up rather than delay the email indefinitely. The file is
    only accepted once it ends with the JPEG end-of-image marker, so a
    half-flushed frame is never attached.
    """
    if not path:
        return None

    target = Path(path)
    deadline = time.monotonic() + max(0.0, timeout)
    while True:
        try:
            if target.is_file() and target.stat().st_size > 0:
                data = target.read_bytes()
                if data.endswith(JPEG_EOI):
                    return data
                # Present but still being written - fall through and retry.
        except OSError as e:
            logger.debug(f"[notify:email] evidence not readable yet ({e})")

        if time.monotonic() >= deadline:
            return None
        time.sleep(poll)


def _html_body(event: NotificationEvent, cid: Optional[str]) -> str:
    accent = SEVERITY_COLOURS.get(event.severity.lower(), SEVERITY_COLOURS["info"])
    rows = [
        ("Event type", event.type.upper()),
        ("Severity", f"{event.level or event.severity.upper()}"),
        ("Camera", event.camera_name or f"Camera {event.camera_id}"),
        ("Timestamp", event.time),
        ("Event ID", str(event.db_id or event.id)),
    ]
    row_html = "".join(
        f'<tr>'
        f'<td style="padding:6px 12px;color:#64748b;font-size:12px;'
        f'text-transform:uppercase;letter-spacing:.05em;white-space:nowrap;">{label}</td>'
        f'<td style="padding:6px 12px;color:#0f172a;font-size:14px;'
        f'font-weight:600;">{value}</td>'
        f'</tr>'
        for label, value in rows
    )

    if cid:
        evidence_html = (
            f'<p style="margin:0 0 8px;color:#64748b;font-size:12px;'
            f'text-transform:uppercase;letter-spacing:.05em;">Evidence frame</p>'
            f'<img src="cid:{cid}" alt="Evidence frame" '
            f'style="width:100%;max-width:640px;border-radius:6px;border:1px solid #e2e8f0;">'
        )
    else:
        evidence_html = (
            '<p style="margin:0;padding:12px;background:#fef3c7;border-radius:6px;'
            'color:#92400e;font-size:13px;">No evidence frame was available for '
            'this incident. Open the Evidence Vault in DRISHTI for the full record.</p>'
        )

    return f"""<!doctype html>
<html>
  <body style="margin:0;padding:24px;background:#f1f5f9;
               font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;">
    <div style="max-width:680px;margin:0 auto;background:#ffffff;border-radius:10px;
                overflow:hidden;box-shadow:0 1px 3px rgba(15,23,42,.12);">
      <div style="background:{accent};padding:18px 24px;">
        <div style="color:rgba(255,255,255,.8);font-size:11px;letter-spacing:.18em;
                    text-transform:uppercase;">DRISHTI &middot; Incident Alert</div>
        <div style="color:#ffffff;font-size:22px;font-weight:700;margin-top:4px;">
          {event.icon} {event.title}
        </div>
      </div>
      <div style="padding:20px 24px;">
        <p style="margin:0 0 16px;color:#334155;font-size:15px;line-height:1.5;">
          {event.detail}
        </p>
        <table style="width:100%;border-collapse:collapse;background:#f8fafc;
                      border-radius:6px;margin-bottom:20px;">{row_html}</table>
        {evidence_html}
      </div>
      <div style="padding:14px 24px;background:#f8fafc;color:#94a3b8;font-size:11px;
                  border-top:1px solid #e2e8f0;">
        Automated message from the DRISHTI safety monitoring platform.
        Evidence is SHA-256 hashed at report generation for chain-of-custody.
      </div>
    </div>
  </body>
</html>"""


def _text_body(event: NotificationEvent, has_evidence: bool) -> str:
    return (
        f"DRISHTI INCIDENT ALERT\n"
        f"{'=' * 46}\n"
        f"{event.title}\n\n"
        f"{event.detail}\n\n"
        f"Event type : {event.type.upper()}\n"
        f"Severity   : {event.level or event.severity.upper()}\n"
        f"Camera     : {event.camera_name or event.camera_id}\n"
        f"Timestamp  : {event.time}\n"
        f"Event ID   : {event.db_id or event.id}\n\n"
        + ("Evidence frame attached.\n" if has_evidence
           else "No evidence frame was available for this incident.\n")
    )


@register
class EmailChannel(Channel):
    name = "email"
    default_enabled = True
    # Nobody wants 40 emails during a demo.
    default_min_severity = "critical"

    def __init__(self):
        super().__init__()
        self._warned_missing = False

    def _log_missing(self, missing: List[str]) -> None:
        """Warn once, then stay quiet - a fresh clone must not spam the log."""
        message = (f"[notify:email] not configured, skipping send "
                   f"(missing: {', '.join(missing)}). Set these in .env to enable.")
        if not self._warned_missing:
            logger.warning(message)
            self._warned_missing = True
        else:
            logger.debug(message)

    def build_message(self, event: NotificationEvent, config: Dict[str, Any],
                      evidence: Optional[bytes]) -> EmailMessage:
        """Assemble the multipart/alternative message, image inlined by CID."""
        message = EmailMessage()
        message["Subject"] = (f"[{event.level or event.severity.upper()}] "
                              f"{event.title} — {event.camera_name or event.camera_id}")
        message["From"] = config["sender"]
        message["To"] = ", ".join(config["recipients"])
        message["Date"] = formatdate(localtime=True)

        cid = None
        if evidence:
            # make_msgid returns <...>; the src="cid:" reference drops the angles.
            cid = make_msgid(domain="drishti.local")

        message.set_content(_text_body(event, bool(evidence)))
        message.add_alternative(_html_body(event, cid[1:-1] if cid else None),
                                subtype="html")

        if evidence and cid:
            # Attach to the HTML part so it is a related inline resource.
            html_part = message.get_payload()[-1]
            html_part.add_related(evidence, maintype="image", subtype="jpeg",
                                  cid=cid, filename=f"evidence_{event.db_id or 'frame'}.jpg")
        return message

    def send(self, event: NotificationEvent, settings: Dict[str, Any]) -> None:
        """Blocking send. Runs on a dispatcher daemon thread, never on the loop."""
        config = smtp_config()
        if config is None or "_missing" in config:
            self._log_missing(config["_missing"] if config else ["SMTP_*"])
            return

        wait = float(settings.get("notify_email_evidence_wait", 3.0))
        evidence = wait_for_evidence(event.evidence_path, wait)
        if event.evidence_path and not evidence:
            logger.warning(f"[notify:email] evidence frame {event.evidence_path} did not "
                           f"appear within {wait}s — sending without it")

        message = self.build_message(event, config, evidence)
        timeout = float(settings.get("notify_email_smtp_timeout", 20.0))

        if config["use_ssl"]:
            server = smtplib.SMTP_SSL(config["host"], config["port"], timeout=timeout)
        else:
            server = smtplib.SMTP(config["host"], config["port"], timeout=timeout)
        try:
            server.ehlo()
            if config["use_tls"] and not config["use_ssl"]:
                server.starttls()
                server.ehlo()
            if config["password"]:
                server.login(config["user"], config["password"])
            server.send_message(message)
        finally:
            try:
                server.quit()
            except Exception:
                # Already-closed sockets are common; the mail is sent by now.
                pass

        logger.info(f"[notify:email] sent event={event.db_id or event.id} "
                    f"to {len(config['recipients'])} recipient(s)"
                    f"{' with evidence frame' if evidence else ' (no evidence)'}")
