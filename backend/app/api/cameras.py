"""
Camera CRUD API — Add, list, update, and remove camera sources.
"""
import shutil
import logging
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.database import get_db, Camera
from app.core.config import SAMPLE_VIDEOS_DIR
from app.services.video_ingestion import stream_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/cameras", tags=["cameras"])


@router.get("/")
def list_cameras(db: Session = Depends(get_db)):
    """List all configured cameras with their stream status."""
    cameras = db.query(Camera).all()
    result = []
    for cam in cameras:
        stream = stream_manager.get_stream(cam.id)
        result.append({
            "id": cam.id,
            "name": cam.name,
            "source_type": cam.source_type,
            "source_url": cam.source_url,
            "location": cam.location,
            "latitude": cam.latitude,
            "longitude": cam.longitude,
            "status": "active" if stream and stream.is_active() else "inactive",
            "fps": stream.fps_actual if stream else 0,
            "created_at": cam.created_at.isoformat() if cam.created_at else None,
        })
    return result


@router.post("/")
async def add_camera(
    name: str = Form(...),
    source_type: str = Form(...),  # "file" or "rtsp"
    location: str = Form(""),
    source_url: str = Form(""),  # RTSP URL (when source_type is "rtsp")
    video_file: UploadFile = File(None),  # Video file (when source_type is "file")
    db: Session = Depends(get_db),
):
    """
    Add a new camera source.
    - For file sources: upload a video file.
    - For RTSP sources: provide the RTSP URL.
    """
    if source_type not in ("file", "rtsp"):
        raise HTTPException(status_code=400, detail="source_type must be 'file' or 'rtsp'")

    if source_type == "file":
        if video_file is None:
            raise HTTPException(status_code=400, detail="Video file is required for file source")

        # Save uploaded file
        file_path = SAMPLE_VIDEOS_DIR / video_file.filename
        with open(file_path, "wb") as f:
            shutil.copyfileobj(video_file.file, f)
        source_url = str(file_path)
        logger.info(f"Saved video file: {file_path}")

    elif source_type == "rtsp":
        if not source_url:
            raise HTTPException(status_code=400, detail="RTSP URL is required")

    # Save to database
    camera = Camera(
        name=name,
        source_type=source_type,
        source_url=source_url,
        location=location,
        status="inactive",
    )
    db.add(camera)
    db.commit()
    db.refresh(camera)

    logger.info(f"Added camera: {camera.name} (ID: {camera.id})")
    return {
        "id": camera.id,
        "name": camera.name,
        "source_type": camera.source_type,
        "source_url": camera.source_url,
        "status": "inactive",
    }


@router.post("/{camera_id}/start")
def start_camera(camera_id: int, db: Session = Depends(get_db)):
    """Start streaming from a camera source."""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    success = stream_manager.start_stream(
        camera_id=camera.id,
        source=camera.source_url,
        source_type=camera.source_type,
    )

    if success:
        camera.status = "active"
        db.commit()
        return {"message": f"Camera '{camera.name}' started", "status": "active"}
    else:
        stream = stream_manager.get_stream(camera_id)
        error = stream.error if stream else "Unknown error"
        raise HTTPException(status_code=500, detail=f"Failed to start camera: {error}")


@router.post("/{camera_id}/stop")
def stop_camera(camera_id: int, db: Session = Depends(get_db)):
    """Stop streaming from a camera source."""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    stream_manager.stop_stream(camera_id)
    camera.status = "inactive"
    db.commit()
    return {"message": f"Camera '{camera.name}' stopped", "status": "inactive"}


@router.delete("/{camera_id}")
def delete_camera(camera_id: int, db: Session = Depends(get_db)):
    """Delete a camera and stop its stream."""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    # Stop stream if running
    stream_manager.stop_stream(camera_id)

    # Delete video file if it was uploaded
    if camera.source_type == "file":
        file_path = Path(camera.source_url)
        if file_path.exists():
            file_path.unlink()

    db.delete(camera)
    db.commit()
    logger.info(f"Deleted camera: {camera.name} (ID: {camera_id})")
    return {"message": f"Camera '{camera.name}' deleted"}


@router.get("/streams/status")
def stream_status():
    """Get status of all active video streams."""
    return stream_manager.get_status()
