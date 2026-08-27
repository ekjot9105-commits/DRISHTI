"""
WebSocket Video Stream — Sends JPEG frames to frontend clients in real-time.
Each camera has its own WebSocket endpoint.
"""
import asyncio
import base64
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.video_ingestion import stream_manager

logger = logging.getLogger(__name__)
router = APIRouter()

# Track connected alert subscribers
alert_subscribers: list[WebSocket] = []


@router.websocket("/ws/camera/{camera_id}")
async def camera_stream(websocket: WebSocket, camera_id: int):
    """
    WebSocket endpoint that sends JPEG frames for a specific camera.
    Frontend connects to this to display live video feed.
    """
    await websocket.accept()
    logger.info(f"WebSocket client connected for camera {camera_id}")

    try:
        while True:
            stream = stream_manager.get_stream(camera_id)

            if stream is None or not stream.is_active():
                # Send status message and wait
                await websocket.send_json({
                    "type": "status",
                    "camera_id": camera_id,
                    "status": "inactive",
                    "message": "Camera stream not active",
                })
                await asyncio.sleep(1)
                continue

            jpeg_bytes = stream.get_jpeg_frame()

            if jpeg_bytes:
                # Send frame as base64 encoded JPEG
                frame_b64 = base64.b64encode(jpeg_bytes).decode('utf-8')
                await websocket.send_json({
                    "type": "frame",
                    "camera_id": camera_id,
                    "frame": frame_b64,
                    "fps": round(stream.fps_actual, 1),
                    "frame_count": stream.frame_count,
                })

            # Target ~15 FPS sending rate to frontend
            await asyncio.sleep(1.0 / 15)

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected for camera {camera_id}")
    except Exception as e:
        logger.error(f"WebSocket error for camera {camera_id}: {e}")


@router.websocket("/ws/alerts")
async def alert_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time alert notifications.
    Frontend subscribes to this to receive detection alerts.
    """
    await websocket.accept()
    alert_subscribers.append(websocket)
    logger.info("Alert subscriber connected")

    try:
        while True:
            # Keep connection alive, listen for any client messages
            data = await websocket.receive_text()
            # Client can send acknowledgments or config updates
            logger.debug(f"Alert client message: {data}")

    except WebSocketDisconnect:
        alert_subscribers.remove(websocket)
        logger.info("Alert subscriber disconnected")
    except Exception as e:
        if websocket in alert_subscribers:
            alert_subscribers.remove(websocket)
        logger.error(f"Alert WebSocket error: {e}")


async def broadcast_alert(alert: dict):
    """Send an alert to all connected alert subscribers."""
    disconnected = []
    for ws in alert_subscribers:
        try:
            await ws.send_json(alert)
        except Exception:
            disconnected.append(ws)

    # Clean up disconnected clients
    for ws in disconnected:
        if ws in alert_subscribers:
            alert_subscribers.remove(ws)
