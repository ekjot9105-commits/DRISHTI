import io
import socket
import logging

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse, JSONResponse

from app.core.system_monitor import sys_monitor
from app.services.threat_score import threat_service
from app.core.settings_manager import load_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/system", tags=["System"])


@router.get("/status")
def get_system_status():
    return sys_monitor.get_stats()


@router.get("/threat")
def get_threat_score():
    """Rolling 0-100 threat score with decay, band, trend and contributors."""
    # Half-life is operator-tunable; picked up without a restart.
    threat_service.half_life = float(load_settings().get("threat_half_life", 120.0))
    return threat_service.get_state()


def _lan_ip() -> str:
    """Best-effort LAN address of this host (no traffic is actually sent)."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
        finally:
            sock.close()
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


@router.get("/lan-url")
def lan_url(path: str = Query("/phone"), port: int = Query(5173)):
    """The URL a phone on the same network should open to join as a camera."""
    ip = _lan_ip()
    return {"ip": ip, "url": f"http://{ip}:{port}{path}", "port": port}


@router.get("/qr")
def qr_code(data: str = Query(..., description="Text/URL to encode")):
    """PNG QR code for the given text. Requires the `qrcode` package."""
    try:
        import qrcode
    except ImportError:
        return JSONResponse(
            status_code=501,
            content={"detail": "qrcode package not installed — run: pip install 'qrcode[pil]'",
                     "data": data},
        )
    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png",
                             headers={"Cache-Control": "no-store"})
