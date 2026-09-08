"""
WebSocket Video Stream — Sends JPEG frames to frontend clients in real-time.
Each camera has its own WebSocket endpoint.
"""
import asyncio
import base64
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.video_ingestion import stream_manager, PushStream

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
                try:
                    await websocket.send_json({
                        "type": "frame",
                        "camera_id": camera_id,
                        "frame": frame_b64,
                        "fps": round(stream.fps_actual, 1),
                        "frame_count": stream.frame_count,
                    })
                except RuntimeError:
                    # Connection closed by client
                    break
                except Exception as e:
                    logger.error(f"Error sending frame for camera {camera_id}: {e}")
                    break

            # Target ~15 FPS sending rate to frontend
            await asyncio.sleep(1.0 / 15)

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected for camera {camera_id}")
    except Exception as e:
        logger.error(f"WebSocket error for camera {camera_id}: {e}")


@router.websocket("/ws/cameras/{camera_id}/push")
async def camera_push(websocket: WebSocket, camera_id: int):
    """Receive JPEG frames pushed from a phone browser and feed the pipeline.

    The phone page (/phone) grabs its webcam, encodes each frame as JPEG and
    sends it as a binary message. Frames enter the same render + inference path
    as any other camera, so tripwires, fight and fire detection all apply.
    """
    await websocket.accept()

    from app.core.database import SessionLocal, Camera
    db = SessionLocal()
    try:
        camera = db.query(Camera).filter(Camera.id == camera_id).first()
        if camera is None:
            await websocket.send_json({"type": "error", "message": "Camera not found"})
            await websocket.close()
            return

        stream = stream_manager.get_stream(camera_id)
        if not isinstance(stream, PushStream) or not stream.running:
            stream = stream_manager.start_push_stream(camera_id)
        camera.status = "active"
        db.commit()
    finally:
        db.close()

    logger.info(f"Phone camera {camera_id}: push connection opened")
    await websocket.send_json({"type": "ready", "camera_id": camera_id})

    frames = 0
    try:
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                break

            data = message.get("bytes")
            if data is None:
                # Text messages are control/keepalive pings; ignore the content.
                continue

            if stream.push_jpeg(data):
                frames += 1
                if frames % 30 == 0:
                    await websocket.send_json({"type": "ack", "frames": frames,
                                               "fps": round(stream.fps_actual, 1)})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"Phone camera {camera_id} push error: {e}")
    finally:
        logger.info(f"Phone camera {camera_id}: push connection closed after {frames} frames")


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
