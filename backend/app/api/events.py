from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
import os
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import json
from datetime import datetime, timedelta, timezone

from app.core.database import get_db, Event, Camera

router = APIRouter(prefix="/api/events", tags=["Events"])

@router.get("/")
def get_events(
    skip: int = 0,
    limit: int = 100,
    camera_id: Optional[int] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Event)
    
    if camera_id:
        query = query.filter(Event.camera_id == camera_id)
    if severity:
        query = query.filter(Event.severity == severity)
    if status:
        query = query.filter(Event.status == status)
        
    events = query.order_by(Event.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for event in events:
        try:
            details = json.loads(event.details) if event.details else {}
        except:
            details = {}
            
        result.append({
            "id": event.id,
            "camera_id": event.camera_id,
            "event_type": event.event_type,
            "severity": event.severity,
            "object_class": event.object_class,
            "status": event.status,
            "created_at": event.created_at.replace(tzinfo=timezone.utc) if event.created_at else None,
            "resolved_at": event.resolved_at.replace(tzinfo=timezone.utc) if event.resolved_at else None,
            "thumbnail_path": event.thumbnail_path,
            "title": details.get("title", ""),
            "detail": details.get("detail", ""),
        })
        
    return result

@router.patch("/{event_id}/status")
def update_event_status(event_id: int, status: str = Query(..., description="new, acknowledged, resolved, archived"), db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    if status not in ["new", "acknowledged", "resolved", "archived"]:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    event.status = status
    if status == "resolved":
        event.resolved_at = datetime.now(timezone.utc)
        
    db.commit()
    db.refresh(event)
    return {"status": "success", "event_id": event.id, "new_status": event.status}

@router.get("/stats")
def get_event_stats(db: Session = Depends(get_db)):
    # 1. Detections over the last 24 hours (grouped by hour)
    twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
    recent_events = db.query(Event).filter(Event.created_at >= twenty_four_hours_ago).all()
    
    hourly_counts = {}
    for event in recent_events:
        hour_str = event.created_at.strftime("%Y-%m-%d %H:00")
        hourly_counts[hour_str] = hourly_counts.get(hour_str, 0) + 1
        
    timeline_data = [{"time": k, "count": v} for k, v in sorted(hourly_counts.items())]
    
    # 2. Severity breakdown (All time)
    severity_query = db.query(Event.severity, func.count(Event.id)).group_by(Event.severity).all()
    severity_data = [{"name": s[0], "value": s[1]} for s in severity_query]
    
    # 3. Camera activity (All time)
    camera_query = db.query(Event.camera_id, func.count(Event.id)).group_by(Event.camera_id).all()
    camera_data = [{"name": f"Cam {c[0]}", "value": c[1]} for c in camera_query]
    
    return {
        "timeline": timeline_data,
        "severity": severity_data,
        "cameras": camera_data
    }

@router.get("/heatmap")
def get_heatmap_data(db: Session = Depends(get_db)):
    # Return count of events joined with camera lat/long
    cameras = db.query(Camera).all()
    heat_data = []
    
    for cam in cameras:
        # Give random demo coordinates if None for prototyping Phase 4 visualization
        lat = cam.latitude if cam.latitude else (28.6139 + (cam.id * 0.01))
        lng = cam.longitude if cam.longitude else (77.2090 + (cam.id * 0.01))
        
        count = db.query(func.count(Event.id)).filter(Event.camera_id == cam.id).scalar()
        if count > 0:
            heat_data.append({
                "lat": lat,
                "lng": lng,
                "intensity": count,
                "name": cam.name
            })
            
    return heat_data

@router.get("/{event_id}/evidence/download")
def download_evidence(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event or not event.thumbnail_path:
        raise HTTPException(status_code=404, detail="Evidence not found")
    
    # Path is something like '/evidence/evt_123.jpg', but we serve it from 'data/evidence'
    file_name = event.thumbnail_path.split('/')[-1]
    file_path = os.path.join("data", "evidence", file_name)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File missing from disk")
        
    return FileResponse(
        path=file_path, 
        filename=f"IBVAP_Evidence_CAM{event.camera_id}_{file_name}",
        media_type="image/jpeg",
        headers={"Content-Disposition": f"attachment; filename=IBVAP_Evidence_CAM{event.camera_id}_{file_name}"}
    )


from app.services.blockchain import blockchain_service

@router.get("/{event_id}/blockchain")
def get_blockchain_verification(event_id: int):
    block = blockchain_service.get_block_by_event(event_id)
    if not block:
        return {"status": "pending", "message": "Transaction pending inclusion in block"}
    return {
        "status": "verified",
        "block": block
    }
