"""
IBVAP — Intelligent Border Video Analytics Platform
Main FastAPI Application Entry Point

Run with: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import FRONTEND_URL, DATA_DIR
from app.core.database import init_db
from app.api.cameras import router as camera_router
from app.ws.video_stream import router as ws_router
from app.api.watchlist import router as watchlist_router
from app.api.events import router as events_router
from app.api.settings import router as settings_router
from app.api.system import router as system_router
from app.api.reports import router as reports_router
import asyncio
from app.services.video_ingestion import stream_manager, alert_queue
from app.ws.video_stream import broadcast_alert


# Configure logging
# LOG_LEVEL=DEBUG surfaces the per-frame detector diagnostics.
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

from fastapi.staticfiles import StaticFiles
from app.core.database import SessionLocal, Event, Camera
import json
import cv2
import os
import hashlib
from app.services.blockchain import blockchain_service

# Mount evidence directory for serving images
os.makedirs("data/evidence", exist_ok=True)

async def _save_evidence(event_id: int, frame, event_metadata: str):
    """Background task to save numpy frame to disk and secure on blockchain."""
    try:
        path = f"data/evidence/evt_{event_id}.jpg"
        cv2.imwrite(path, frame)
        
        # Calculate cryptographic hashes
        evidence_hash = "No Image"
        if os.path.exists(path):
            with open(path, "rb") as f:
                evidence_hash = hashlib.sha256(f.read()).hexdigest()
                
        event_hash = hashlib.sha256(event_metadata.encode()).hexdigest()
        
        # Queue to Blockchain without blocking YOLO or WebSockets
        blockchain_service.queue_transaction(event_id, evidence_hash, event_hash)
        
        # Update database with thumbnail path
        db = SessionLocal()
        event = db.query(Event).filter(Event.id == event_id).first()
        if event:
            event.thumbnail_path = f"/evidence/evt_{event_id}.jpg"
            db.commit()
        db.close()
    except Exception as e:
        logger.error(f"Failed to save evidence: {e}")

async def alert_dispatcher():
    """Background task to poll the alert queue, save to DB, and broadcast via WebSockets."""
    logger.info("Alert dispatcher started.")
    while True:
        try:
            while not alert_queue.empty():
                alert = alert_queue.get_nowait()
                
                # Extract frame data if present (don't save to DB or broadcast it directly)
                frame_data = alert.pop("frame_data", None)
                
                # Save to database
                db = SessionLocal()
                try:
                    new_event = Event(
                        camera_id=alert.get("camera_id", 0),
                        event_type=alert.get("type", "unknown"),
                        severity=alert.get("severity", "info"),
                        object_class=alert.get("icon", "??").replace("👤", "person").replace("🚗", "vehicle"),
                        details=json.dumps({
                            "title": alert.get("title", ""),
                            "detail": alert.get("detail", ""),
                            "id": alert.get("id", "")
                        })
                    )
                    db.add(new_event)
                    db.commit()
                    db.refresh(new_event)
                    
                    # Attach DB ID to alert before broadcasting
                    alert["db_id"] = new_event.id
                    
                    # Fetch camera name for better context
                    cam = db.query(Camera).filter(Camera.id == alert.get("camera_id")).first()
                    alert["camera_name"] = cam.name if cam else f"Camera {alert.get('camera_id')}"

                    
                    # If we have frame evidence (like from a tripwire intrusion), save it asynchronously
                    if frame_data is not None:
                        asyncio.create_task(_save_evidence(new_event.id, frame_data, str(alert)))
                        alert["has_evidence"] = True
                        
                finally:
                    db.close()
                
                # Dispatch Webhook if configured
                try:
                    from app.core.settings_manager import load_settings
                    import httpx
                    settings = load_settings()
                    webhook_url = settings.get("webhook_url", "")
                    if webhook_url and alert.get("severity") in ["high", "critical", "warning"]:
                        async def send_webhook(url, payload):
                            try:
                                async with httpx.AsyncClient() as client:
                                    await client.post(url, json=payload, timeout=5.0)
                            except Exception as we:
                                logger.error(f"Webhook failed: {we}")
                        asyncio.create_task(send_webhook(webhook_url, alert))
                except Exception as e:
                    logger.error(f"Failed to dispatch webhook: {e}")
                
                # Broadcast via WebSocket
                await broadcast_alert(alert)
        except Exception as e:
            logger.error(f"Alert dispatcher error: {e}")
        await asyncio.sleep(0.5)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    # Startup
    logger.info("=" * 60)
    logger.info("  IBVAP — Intelligent Border Video Analytics Platform")
    logger.info("  Starting backend server...")
    logger.info("=" * 60)
    init_db()
    logger.info("Database initialized")
    
    # Start the alert dispatcher task
    dispatcher_task = asyncio.create_task(alert_dispatcher())

    yield

    # Shutdown
    logger.info("Shutting down — stopping all video streams...")
    dispatcher_task.cancel()
    stream_manager.stop_all()
    logger.info("All streams stopped. Goodbye!")


app = FastAPI(
    title="IBVAP API",
    description="Intelligent Border Video Analytics Platform — AI-driven surveillance backend",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/evidence", StaticFiles(directory="data/evidence"), name="evidence")

# CORS — allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:5173", "http://127.0.0.1:5173"],
    # Phones joining from the LAN hit the dev server on a private IP origin
    allow_origin_regex=r"http://(192\.168|10\.|172\.(1[6-9]|2\d|3[01]))[\d.]*(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded files (thumbnails, evidence, etc.)
app.mount("/data", StaticFiles(directory=str(DATA_DIR)), name="data")

# Register routers
app.include_router(camera_router)
app.include_router(ws_router)
app.include_router(watchlist_router)
app.include_router(events_router)
app.include_router(settings_router)
app.include_router(system_router)
app.include_router(reports_router)


@app.get("/")
def root():
    return {
        "name": "IBVAP API",
        "version": "1.0.0",
        "status": "running",
        "description": "Intelligent Border Video Analytics Platform",
    }


@app.get("/api/health")
def health_check():
    streams = stream_manager.get_status()
    return {
        "status": "healthy",
        "active_streams": len([s for s in streams if s["active"]]),
        "total_streams": len(streams),
    }
