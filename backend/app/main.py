"""
IBVAP — Intelligent Border Video Analytics Platform
Main FastAPI Application Entry Point

Run with: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""
import logging
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
import asyncio
from app.services.video_ingestion import stream_manager, alert_queue
from app.ws.video_stream import broadcast_alert


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

from app.core.database import SessionLocal, Event
import json

async def alert_dispatcher():
    """Background task to poll the alert queue, save to DB, and broadcast via WebSockets."""
    logger.info("Alert dispatcher started.")
    while True:
        try:
            while not alert_queue.empty():
                alert = alert_queue.get_nowait()
                
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
                finally:
                    db.close()
                
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

# CORS — allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:5173", "http://127.0.0.1:5173"],
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
