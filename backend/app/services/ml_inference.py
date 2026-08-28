import time
import logging
from typing import Dict, List, Any

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

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
        
        # Track object history per camera: {camera_id: {track_id: {"first_seen": float, "last_seen": float}}}
        self.object_history: Dict[int, Dict[int, dict]] = {}
        
        # Classes of interest (COCO dataset: 0=person, 2=car, 3=motorcycle, 5=bus, 7=truck)
        self.target_classes = {0: 'person', 2: 'vehicle', 3: 'vehicle', 5: 'vehicle', 7: 'vehicle'}

    def process_frame(self, camera_id: int, frame):
        if not self.active or self.model is None:
            return [], []

        if camera_id not in self.object_history:
            self.object_history[camera_id] = {}

        alerts = []
        drawn_boxes = []
        current_time = time.time()
        
        try:
            # Run inference with tracking on CPU
            # device='cpu', verbose=False to reduce console spam
            # We use a lock because YOLOv8 tracker state is NOT thread-safe for concurrent calls
            with self.inference_lock:
                results = self.model.track(
                    frame, 
                    persist=True, 
                    device='cpu', 
                    verbose=False, 
                    tracker="bytetrack.yaml", 
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
                if conf < 0.25:
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
                        
                        # Check for prolonged dwelling (> 10 seconds)
                        first_seen = self.object_history[camera_id][track_id]["first_seen"]
                        dwelling_time = current_time - first_seen
                        
                        # Alert every 10s of continuous presence
                        if dwelling_time > 10.0:
                            alerts.append({
                                "id": f"evt_dw_{int(current_time)}_{track_id}",
                                "camera_id": camera_id,
                                "type": "dwelling",
                                "severity": "high",
                                "level": "PRIORITY ALPHA",
                                "title": "Prolonged Dwelling Alert",
                                "detail": f"A {obj_class} has been stationary/present for over 10 seconds.",
                                "time": time.strftime("%H:%M:%S"),
                                "icon": "⚠️"
                            })
                            # Reset first_seen so it only alerts every 10 seconds if they stay
                            self.object_history[camera_id][track_id]["first_seen"] = current_time
                    
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
