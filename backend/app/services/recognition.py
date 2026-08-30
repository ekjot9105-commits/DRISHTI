import logging
import time
import os
import cv2
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, WatchlistFace, WatchlistPlate
from app.core.config import FACES_DIR

logger = logging.getLogger(__name__)

class RecognitionService:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Load EasyOCR lazily when first needed to save startup memory
        self.reader = None
        self.deepface_loaded = False
        
        # Track-and-Check Cache: {camera_id: {track_id: "identity_or_none"}}
        self.checked_objects = {}

    def _init_ocr(self):
        if self.reader is None:
            logger.info("Initializing EasyOCR (CPU)...")
            import easyocr
            # Load only english letters/numbers to be faster
            self.reader = easyocr.Reader(['en'], gpu=False, quantize=True)
            logger.info("EasyOCR loaded.")

    def _init_deepface(self):
        if not self.deepface_loaded:
            logger.info("Initializing DeepFace (VGG-Face)...")
            from deepface import DeepFace
            # Dummy call to load model into memory
            try:
                import numpy as np
                dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
                DeepFace.represent(dummy_img, model_name="VGG-Face", enforce_detection=False, detector_backend="retinaface")
            except:
                pass
            self.deepface_loaded = True
            logger.info("DeepFace loaded.")

    def async_recognize(self, camera_id: int, track_id: int, obj_class: str, cropped_img, current_time: float):
        """Dispatches to background thread so it doesn't block video loop."""
        
        if camera_id not in self.checked_objects:
            self.checked_objects[camera_id] = {}
            
        status = self.checked_objects[camera_id].get(track_id)
        # If successfully recognized or explicitly marked unknown, skip.
        # But if pending, let it finish. If not present, start.
        if status not in [None, "checking"]:
            return
            
        self.checked_objects[camera_id][track_id] = "checking"
        
        if obj_class == "vehicle":
            self.executor.submit(self._recognize_plate, camera_id, track_id, cropped_img, current_time)
        elif obj_class == "person":
            self.executor.submit(self._recognize_face, camera_id, track_id, cropped_img, current_time)

    def _recognize_plate(self, camera_id: int, track_id: int, img, current_time: float):
        try:
            self._init_ocr()
            # Fast simple OCR on the cropped box
            results = self.reader.readtext(img)
            plate_text = ""
            best_conf = 0
            
            for (bbox, text, conf) in results:
                # filter out obvious noise
                cleaned = "".join([c for c in text if c.isalnum()]).upper()
                if len(cleaned) > 4 and conf > best_conf:
                    plate_text = cleaned
                    best_conf = conf
                    
            if plate_text:
                logger.info(f"ALPR detected plate: {plate_text} (conf: {best_conf:.2f})")
                
                # Check Database
                db: Session = SessionLocal()
                try:
                    match = db.query(WatchlistPlate).filter(WatchlistPlate.plate_number.like(f"%{plate_text}%")).first()
                    if match:
                        self.checked_objects[camera_id][track_id] = match.plate_number
                        self._trigger_alert("vehicle", match, camera_id, track_id, current_time)
                    else:
                        self.checked_objects[camera_id][track_id] = "unknown"
                finally:
                    db.close()
            else:
                self.checked_objects[camera_id][track_id] = "unknown"
        except Exception as e:
            logger.error(f"ALPR error: {e}")
            self.checked_objects[camera_id][track_id] = "error"

    def _recognize_face(self, camera_id: int, track_id: int, img, current_time: float):
        try:
            self._init_deepface()
            from deepface import DeepFace
            import numpy as np
            import time
            import os
            from sqlalchemy.orm import Session
            from app.core.database import SessionLocal, WatchlistFace
                
            # If the watchlist directory is empty, skip completely
            if not os.path.exists(FACES_DIR) or not any(f.endswith('.jpg') or f.endswith('.png') for f in os.listdir(FACES_DIR)):
                self.checked_objects[camera_id][track_id] = "unknown"
                return

            # Temporary save for DeepFace
            tmp_path = f"tmp_face_{camera_id}_{track_id}_{int(time.time()*1000)}.jpg"
            cv2.imwrite(tmp_path, img)

            try:
                # Find matching face
                results = DeepFace.find(
                    img_path=tmp_path, 
                    db_path=str(FACES_DIR), 
                    model_name="VGG-Face", 
                    enforce_detection=True,  # Now strictly enforce face detection
                    detector_backend="retinaface",
                    silent=True
                )
            except Exception as d_e:
                # Face not detected by deepface backend
                self.checked_objects[camera_id][track_id] = None
                if os.path.exists(tmp_path): os.remove(tmp_path)
                return
            
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
            if len(results) > 0 and len(results[0]) > 0:
                best_match_path = results[0].iloc[0]['identity']
                
                # Multi-observation confirmation logic
                if not hasattr(self, 'watchlist_hits'):
                    self.watchlist_hits = {}
                key = f"{camera_id}_{track_id}_{best_match_path}"
                self.watchlist_hits[key] = self.watchlist_hits.get(key, 0) + 1
                
                if self.watchlist_hits[key] >= 3:
                    # Confirmed match
                    db: Session = SessionLocal()
                    try:
                        match = db.query(WatchlistFace).filter(WatchlistFace.image_path == best_match_path).first()
                        if match:
                            self.checked_objects[camera_id][track_id] = match.name
                            self._trigger_alert("person", match, camera_id, track_id, current_time)
                        else:
                            self.checked_objects[camera_id][track_id] = "unknown"
                    finally:
                        db.close()
                else:
                    # Found a match, but need more confirmations
                    self.checked_objects[camera_id][track_id] = None
            else:
                self.checked_objects[camera_id][track_id] = "unknown"
                
        except Exception as e:
            logger.error(f"FaceRec error: {e}")
            self.checked_objects[camera_id][track_id] = None
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.remove(tmp_path)
    def _trigger_alert(self, entity_type, match_obj, camera_id, track_id, current_time):
        from app.services.video_ingestion import alert_queue
        
        title = ""
        detail = ""
        icon = ""
        
        if entity_type == "person":
            title = f"CRITICAL: Watchlist Face Match"
            detail = f"Identified: {match_obj.name}. {match_obj.description}"
            icon = "🚨"
        else:
            title = f"CRITICAL: Watchlist Plate Match"
            detail = f"License Plate: {match_obj.plate_number}. {match_obj.vehicle_description} ({match_obj.owner_name})"
            icon = "🚨"
            
        alert_queue.put({
            "id": f"evt_wl_{int(current_time)}_{track_id}",
            "camera_id": camera_id,
            "type": "watchlist_match",
            "severity": "critical",
            "level": "CRITICAL",
            "title": title,
            "detail": detail,
            "time": time.strftime("%H:%M:%S"),
            "icon": icon
        })

    def get_identity(self, camera_id, track_id):
        ident = self.checked_objects.get(camera_id, {}).get(track_id)
        if ident in ["pending", "checking", "unknown", "error", None]:
            return None
        return ident

recognition_service = RecognitionService()
