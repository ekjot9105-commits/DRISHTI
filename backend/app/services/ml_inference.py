import time
import logging
from typing import Dict, List, Any

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

from app.core.settings_manager import load_settings

logger = logging.getLogger(__name__)

class MLService:
    def __init__(self):
        self.model = None
        self.active = False
        import threading
        self.inference_lock = threading.Lock()
        
        if YOLO:
            try:
                # Load YOLOv8 small for better accuracy in crowded/dark scenes
                self.model = YOLO('yolov8s.pt')
                self.active = True
                logger.info("YOLOv8s model loaded successfully for CPU inference.")
            except Exception as e:
                logger.error(f"Failed to load YOLO model: {e}")
        else:
            logger.warning("ultralytics not installed. ML inference is disabled.")
        
        # Track object history per camera: {camera_id: {track_id: {"first_seen": float, "last_seen": float, "crossed_tripwire": bool}}}
        self.object_history: Dict[int, Dict[int, dict]] = {}
        
        # Classes of interest (COCO dataset: 0=person, 2=car, 3=motorcycle, 5=bus, 7=truck)
        self.target_classes = {0: 'person', 2: 'vehicle', 3: 'vehicle', 5: 'vehicle', 7: 'vehicle'}
        
        # Tripwire caching
        self.tripwires = {}
        self.last_tripwire_sync = 0.0

    def _sync_tripwires(self):
        try:
            from app.core.database import SessionLocal, Camera
            import json
            db = SessionLocal()
            cams = db.query(Camera).all()
            for cam in cams:
                if cam.tripwire_line:
                    try:
                        self.tripwires[cam.id] = json.loads(cam.tripwire_line)
                    except:
                        pass
            db.close()
        except:
            pass

    def _ccw(self, A, B, C):
        """Helper for line intersection math. Checks if A,B,C are counterclockwise."""
        return (C['y'] - A['y']) * (B['x'] - A['x']) > (B['y'] - A['y']) * (C['x'] - A['x'])

    def _intersect(self, A, B, C, D):
        """Return true if line segments AB and CD intersect."""
        return self._ccw(A, C, D) != self._ccw(B, C, D) and self._ccw(A, B, C) != self._ccw(A, B, D)

    def process_frame(self, camera_id: int, frame):
        if not self.active or self.model is None:
            return [], []

        settings = load_settings()
        current_time = time.time()
        # Sync tripwires every 5 seconds
        if current_time - self.last_tripwire_sync > 5.0:
            self._sync_tripwires()
            self.last_tripwire_sync = current_time

        if camera_id not in self.object_history:
            self.object_history[camera_id] = {}

        alerts = []
        drawn_boxes = []
        
        try:
            # Apply optional night_mode contrast enhancement before tracking if enabled
            if settings.get("night_mode"):
                import cv2
                import numpy as np
                # fast CLAHE on lightness channel
                lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                cl = clahe.apply(l)
                enhanced_frame = cv2.cvtColor(cv2.merge((cl,a,b)), cv2.COLOR_LAB2BGR)
            else:
                enhanced_frame = frame

            with self.inference_lock:
                results = self.model.track(
                    enhanced_frame, 
                    persist=True, 
                    device='cpu', 
                    verbose=False, 
                    tracker="bytetrack_custom.yaml", 
                    iou=0.6,
                    classes=list(self.target_classes.keys())
                )
            
            if not results or not results[0].boxes:
                # Clean up tracks that haven't been seen for 2 seconds (grace period to prevent flickering)
                for tid in list(self.object_history.get(camera_id, {}).keys()):
                    if current_time - self.object_history[camera_id][tid]["last_seen"] > 2.0:
                        del self.object_history[camera_id][tid]
                return alerts, drawn_boxes
                
            boxes = results[0].boxes
            
            # If tracking failed to assign IDs but we have detections, fallback so we still draw boxes
            if boxes.id is None:
                track_ids = ["?"] * len(boxes.cls)
            else:
                track_ids = boxes.id.int().cpu().tolist()
                
            cls_ids = boxes.cls.int().cpu().tolist()
            confs = boxes.conf.cpu().tolist()
            xyxys = boxes.xyxy.cpu().tolist()
            
            current_track_ids = set()
            
            for track_id, cls_id, conf, xyxy in zip(track_ids, cls_ids, confs, xyxys):
                if conf < settings.get("confidence_threshold", 0.35):
                    continue
                    
                obj_class = self.target_classes.get(cls_id, 'unknown')
                current_track_ids.add(track_id)
                
                # ALPR / Face Recognition Integration
                identity = None
                if track_id != "?":
                    from app.services.recognition import recognition_service
                    
                    # 1. Dispatch background recognition job (crops frame, non-blocking)
                    x1, y1, x2, y2 = [int(v) for v in xyxy]
                    h, w = frame.shape[:2]
                    x1, y1, x2, y2 = max(0, x1), max(0, y1), min(w, x2), min(h, y2)
                    
                    if x2 > x1 and y2 > y1:
                        # Only dispatch if crop is somewhat reasonable size
                        if (x2 - x1) > 30 and (y2 - y1) > 30:
                            cropped = frame[y1:y2, x1:x2].copy()
                            recognition_service.async_recognize(camera_id, track_id, obj_class, cropped, current_time)
                    
                    # 2. Retrieve identity if ALPR/FaceRec has completed it
                    identity = recognition_service.get_identity(camera_id, track_id)

                # Append box info for drawing later
                drawn_boxes.append({
                    "id": track_id,
                    "class": obj_class,
                    "conf": conf,
                    "box": xyxy,
                    "identity": identity
                })
                
                # Check if new object or dwelling (only for valid track IDs)
                if track_id != "?":
                    if track_id not in self.object_history[camera_id]:
                        # New object detected -> Routine Alert
                        self.object_history[camera_id][track_id] = {
                            "first_seen": current_time, 
                            "last_seen": current_time,
                        }
                        alerts.append({
                            "id": f"evt_{int(current_time)}_{track_id}",
                            "camera_id": camera_id,
                            "type": "detection",
                            "severity": "info",
                            "level": "ROUTINE",
                            "title": f"New {obj_class.capitalize()} Detected",
                            "detail": f"A {obj_class} entered the camera feed.",
                            "time": time.strftime("%H:%M:%S"),
                            "icon": "👤" if obj_class == 'person' else "🚗"
                        })
                    else:
                        # Update last seen timestamp since they are currently in frame
                        self.object_history[camera_id][track_id]["last_seen"] = current_time
                        
                        # Check for prolonged dwelling
                        first_seen = self.object_history[camera_id][track_id]["first_seen"]
                        dwelling_time = current_time - first_seen
                        
                        dwelling_thresh = settings.get("dwelling_time", 10.0)
                        if dwelling_time > dwelling_thresh:
                            alerts.append({
                                "id": f"evt_dw_{int(current_time)}_{track_id}",
                                "camera_id": camera_id,
                                "type": "dwelling",
                                "severity": "high",
                                "level": "PRIORITY ALPHA",
                                "title": "Prolonged Dwelling Alert",
                                "detail": f"A {obj_class} has been stationary/present for over {dwelling_thresh} seconds.",
                                "time": time.strftime("%H:%M:%S"),
                                "icon": "⚠️"
                            })
                            # Reset first_seen so it only alerts every 10 seconds if they stay
                            self.object_history[camera_id][track_id]["first_seen"] = current_time
                    
                    hist = self.object_history[camera_id][track_id]
                    # --- TRIPWIRE INTRUSION LOGIC ---
                    if "last_box" in hist and camera_id in self.tripwires:
                        tripwire = self.tripwires[camera_id]
                        if tripwire and len(tripwire) == 2:
                            fh, fw = frame.shape[:2]
                            A = {"x": tripwire[0]["x"] * fw, "y": tripwire[0]["y"] * fh}
                            B = {"x": tripwire[1]["x"] * fw, "y": tripwire[1]["y"] * fh}
                            
                            # Previous bottom-center
                            p_x1, p_y1, p_x2, p_y2 = hist["last_box"]
                            C = {"x": (p_x1 + p_x2)/2.0, "y": p_y2}
                            
                            # Current bottom-center
                            c_x1, c_y1, c_x2, c_y2 = xyxy
                            D = {"x": (c_x1 + c_x2)/2.0, "y": c_y2}
                            
                            # Check intersection and cooldown
                            cooldown = current_time - hist.get("last_intrusion_time", 0)
                            if cooldown > settings.get("intrusion_cooldown", 10.0) and self._intersect(A, B, C, D):
                                hist["last_intrusion_time"] = current_time
                                alerts.append({
                                    "id": f"evt_int_{int(current_time)}_{track_id}",
                                    "camera_id": camera_id,
                                    "type": "intrusion",
                                    "severity": "critical",
                                    "level": "CRITICAL",
                                    "title": f"Tripwire Intrusion: {obj_class.capitalize()}",
                                    "detail": f"A {obj_class} crossed the virtual perimeter.",
                                    "time": time.strftime("%H:%M:%S"),
                                    "icon": "🚨",
                                    "frame_data": frame # Passed internally for evidence vault
                                })
                    # --------------------------------
                    
                    # Store latest tracking features for ghosting
                    self.object_history[camera_id][track_id].update({
                        "last_box": xyxy,
                        "last_class": obj_class,
                        "last_conf": conf,
                        "last_identity": identity
                    })
                        
            # Clean up old tracks that left the frame (grace period of 2 seconds)
            # Also inject 'Ghost Boxes' for objects that momentarily disappeared but are still in grace period
            for tid in list(self.object_history[camera_id].keys()):
                if tid not in current_track_ids:
                    time_since_seen = current_time - self.object_history[camera_id][tid]["last_seen"]
                    if time_since_seen > 2.0:
                        del self.object_history[camera_id][tid]
                    elif time_since_seen > 0.05: # if it missed at least one frame
                        hist = self.object_history[camera_id][tid]
                        drawn_boxes.append({
                            "id": tid,
                            "class": hist.get("last_class", "unknown"),
                            "conf": hist.get("last_conf", 0.0),
                            "box": hist.get("last_box", [0, 0, 0, 0]),
                            "identity": hist.get("last_identity", None)
                        })
                    
            return alerts, drawn_boxes
            
        except Exception as e:
            logger.error(f"Inference error on camera {camera_id}: {e}")
            return [], []

ml_service = MLService()
