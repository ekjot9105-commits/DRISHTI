import os
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.database import get_db, WatchlistFace, WatchlistPlate
from app.core.config import FACES_DIR

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])

@router.get("/faces")
def get_faces(db: Session = Depends(get_db)):
    return db.query(WatchlistFace).all()

@router.post("/faces")
async def add_face(
    name: str = Form(...),
    description: str = Form(""),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        from deepface import DeepFace
    except ImportError:
        raise HTTPException(status_code=500, detail="Face recognition library not installed yet")
        
    file_path = FACES_DIR / image.filename
    with open(file_path, "wb") as f:
        shutil.copyfileobj(image.file, f)
        
    try:
        # Generate embedding immediately to verify it's a valid face
        DeepFace.represent(img_path=str(file_path), model_name="VGG-Face", enforce_detection=True, detector_backend="retinaface")
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"No face detected in image: {e}")

    # Delete the deepface cache so it rebuilds on next inference
    pkl_path = FACES_DIR / "representations_vgg_face.pkl"
    if pkl_path.exists():
        os.remove(pkl_path)
    
    face = WatchlistFace(name=name, description=description, image_path=str(file_path))
    db.add(face)
    db.commit()
    db.refresh(face)
    return face

@router.delete("/faces/{face_id}")
def delete_face(face_id: int, db: Session = Depends(get_db)):
    face = db.query(WatchlistFace).filter(WatchlistFace.id == face_id).first()
    if not face:
        raise HTTPException(status_code=404, detail="Not found")
    
    if os.path.exists(face.image_path):
        os.remove(face.image_path)
        
    pkl_path = FACES_DIR / "representations_vgg_face.pkl"
    if pkl_path.exists():
        os.remove(pkl_path)
        
    db.delete(face)
    db.commit()
    return {"status": "deleted"}

@router.get("/plates")
def get_plates(db: Session = Depends(get_db)):
    return db.query(WatchlistPlate).all()

@router.post("/plates")
def add_plate(
    plate_number: str = Form(...),
    vehicle_description: str = Form(""),
    owner_name: str = Form(""),
    alert_level: str = Form("critical"),
    db: Session = Depends(get_db)
):
    plate = WatchlistPlate(
        plate_number=plate_number.upper().strip(),
        vehicle_description=vehicle_description,
        owner_name=owner_name,
        alert_level=alert_level
    )
    db.add(plate)
    db.commit()
    db.refresh(plate)
    return plate

@router.delete("/plates/{plate_id}")
def delete_plate(plate_id: int, db: Session = Depends(get_db)):
    plate = db.query(WatchlistPlate).filter(WatchlistPlate.id == plate_id).first()
    if not plate:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(plate)
    db.commit()
    return {"status": "deleted"}
