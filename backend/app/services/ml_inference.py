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
                import os
                # Prefer optimized ONNX model if available
                if os.path.exists('yolov8n.onnx'):
                    self.model = YOLO('yolov8n.onnx', task='detect')
                    logger.info("YOLOv8n ONNX optimized model loaded successfully.")
                elif os.path.exists('yolov8s.onnx'):
                    self.model = YOLO('yolov8s.onnx', task='detect')
                    logger.info("YOLOv8s ONNX optimized model loaded successfully.")
                elif os.path.exists('yolov8s.pt'):
                    self.model = YOLO('yolov8s.pt')
                    logger.info("YOLOv8s PyTorch model loaded successfully.")
                else:
                    self.model = YOLO('yolov8s.pt') # Will download
                    
                self.active = True
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
                            "last_dwelling_time": 0,
                        }

                    else:
                        # Update last seen timestamp since they are currently in frame
                        self.object_history[camera_id][track_id]["last_seen"] = current_time
                        
                        # Check for prolonged dwelling
                        first_seen = self.object_history[camera_id][track_id]["first_seen"]
                        dwelling_time = current_time - first_seen
                        
                        dwelling_thresh = settings.get("dwelling_time", 10.0)
                        if dwelling_time > dwelling_thresh:
                            # Per-track dwelling cooldown (alert once per 60 seconds)
                            last_dw = self.object_history[camera_id][track_id].get("last_dwelling_time", 0)
                            if current_time - last_dw > 60.0:
                                self.object_history[camera_id][track_id]["last_dwelling_time"] = current_time
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

                    hist = self.object_history[camera_id][track_id]
                    
                    # --- BEHAVIORAL ANALYTICS (Running/Fleeing) ---
                    # Calculate centroid
                    cx = (xyxy[0] + xyxy[2]) / 2.0
                    cy = (xyxy[1] + xyxy[3]) / 2.0
                    
                    positions = hist.get("positions", [])
                    positions.append((cx, cy, current_time))
                    
                    # Keep only last 3 seconds of positions for smoothing
                    positions = [p for p in positions if current_time - p[2] <= 3.0]
                    hist["positions"] = positions
                    
                    if len(positions) >= 5 and obj_class == 'person':
                        # Calculate smoothed velocity over the window
                        oldest = positions[0]
                        newest = positions[-1]
                        dt = newest[2] - oldest[2]
                        if dt > 0:
                            dx = newest[0] - oldest[0]
                            dy = newest[1] - oldest[1]
                            dist = (dx**2 + dy**2)**0.5
                            speed = dist / dt # px/sec
                            
                            fleeing_thresh = settings.get("fleeing_threshold", 300.0)
                            fleeing_dur = settings.get("fleeing_duration", 1.5)
                            
                            if speed > fleeing_thresh:
                                if "fleeing_start" not in hist:
                                    hist["fleeing_start"] = current_time
                                elif current_time - hist["fleeing_start"] >= fleeing_dur:
                                    # Trigger Fleeing Alert
                                    fleeing_cooldown = current_time - hist.get("last_fleeing_time", 0)
                                    if fleeing_cooldown > 15.0:
                                        hist["last_fleeing_time"] = current_time
                                        alerts.append({
                                            "id": f"evt_run_{int(current_time)}_{track_id}",
                                            "camera_id": camera_id,
                                            "type": "behavioral",
                                            "severity": "high",
                                            "level": "PRIORITY ALPHA",
                                            "title": "Fleeing Subject Detected",
                                            "detail": f"A person is moving at high speed ({int(speed)} px/s).",
                                            "time": time.strftime("%H:%M:%S"),
                                            "icon": "🏃"
                                        })
                            else:
                                if "fleeing_start" in hist:
                                    del hist["fleeing_start"]

                    # --- TRIPWIRE INTRUSION LOGIC ---
                    if "last_box" in hist and camera_id in self.tripwires:
                        tripwires_data = self.tripwires[camera_id]
                        
                        # Normalize to list of lines
                        lines_to_check = []
                        if tripwires_data and isinstance(tripwires_data, list) and len(tripwires_data) > 0:
                            if isinstance(tripwires_data[0], list):
                                lines_to_check = [l for l in tripwires_data if len(l) == 2]
                            elif len(tripwires_data) == 2:
                                lines_to_check = [tripwires_data]
                                
                        if lines_to_check:
                            fh, fw = frame.shape[:2]
                            
                            # Previous bottom-center
                            p_x1, p_y1, p_x2, p_y2 = hist["last_box"]
                            C = {"x": (p_x1 + p_x2)/2.0, "y": p_y2}
                            
                            # Current bottom-center
                            c_x1, c_y1, c_x2, c_y2 = xyxy
                            D = {"x": (c_x1 + c_x2)/2.0, "y": c_y2}
                            
                            cooldown = current_time - hist.get("last_intrusion_time", 0)
                            
                            if cooldown > settings.get("intrusion_cooldown", 10.0):
                                crossed = False
                                for line in lines_to_check:
                                    A = {"x": line[0]["x"] * fw, "y": line[0]["y"] * fh}
                                    B = {"x": line[1]["x"] * fw, "y": line[1]["y"] * fh}
                                    if self._intersect(A, B, C, D):
                                        crossed = True
                                        break
                                        
                                if crossed:
                                    hist["last_intrusion_time"] = current_time
                                    alerts.append({
                                        "id": f"evt_int_{int(current_time)}_{track_id}",
                                        "camera_id": camera_id,
                                        "type": "intrusion",
                                        "severity": "critical",
                                        "level": "CRITICAL",
                                        "title": f"Tripwire Intrusion: {obj_class.capitalize()}",
                                        "detail": f"A {obj_class} crossed a virtual perimeter line.",
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
                        
            # --- CROWD GATHERING LOGIC ---
            crowd_count = settings.get("crowd_count", 3)
            crowd_density = settings.get("crowd_density", 150.0)
            crowd_duration = settings.get("crowd_duration", 60.0)
            
            # Extract all current person centroids
            person_centroids = []
            for tid, hist_data in self.object_history[camera_id].items():
                if tid in current_track_ids and hist_data.get("last_class") == "person":
                    pos = hist_data.get("positions", [])
                    if pos:
                        person_centroids.append((tid, pos[-1][0], pos[-1][1]))
            
            # Simple O(N^2) clustering for density
            clusters = []
            visited = set()
            for i, p1 in enumerate(person_centroids):
                if p1[0] in visited: continue
                cluster = [p1[0]]
                visited.add(p1[0])
                for j, p2 in enumerate(person_centroids):
                    if i != j and p2[0] not in visited:
                        dist = ((p1[1]-p2[1])**2 + (p1[2]-p2[2])**2)**0.5
                        if dist < crowd_density:
                            cluster.append(p2[0])
                            visited.add(p2[0])
                clusters.append(cluster)
            
            # Check if any cluster is >= crowd_count
            largest_cluster = max([len(c) for c in clusters]) if clusters else 0
            if largest_cluster >= crowd_count:
                if not hasattr(self, "crowd_start_time"):
                    self.crowd_start_time = {}
                if camera_id not in self.crowd_start_time:
                    self.crowd_start_time[camera_id] = current_time
                elif current_time - self.crowd_start_time[camera_id] >= crowd_duration:
                    crowd_cooldown = current_time - getattr(self, "last_crowd_alert", {}).get(camera_id, 0)
                    if crowd_cooldown > 60.0:
                        if not hasattr(self, "last_crowd_alert"): self.last_crowd_alert = {}
                        self.last_crowd_alert[camera_id] = current_time
                        alerts.append({
                            "id": f"evt_crowd_{int(current_time)}_{camera_id}",
                            "camera_id": camera_id,
                            "type": "behavioral",
                            "severity": "warning",
                            "level": "WARNING",
                            "title": "Crowd Gathering Detected",
                            "detail": f"A group of {largest_cluster} people detected gathering.",
                            "time": time.strftime("%H:%M:%S"),
                            "icon": "👥"
                        })
            else:
                if hasattr(self, "crowd_start_time") and camera_id in self.crowd_start_time:
                    del self.crowd_start_time[camera_id]


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
