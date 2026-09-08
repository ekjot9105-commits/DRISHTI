import time
import logging
from typing import Dict, List, Any

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

from app.core.settings_manager import load_settings

logger = logging.getLogger(__name__)

from app.services.recognition import recognition_service
from app.services.detectors import base as detector_base
import app.services.detectors  # noqa: F401  (registers built-in detectors)

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
        self.incident_cache = {}  # { "camera_id_type_zone": last_trigger_time }
        
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
        return (C['y'] - A['y']) * (B['x'] - A['x']) > (B['y'] - A['y']) * (C['x'] - A['x'])

    def _intersect(self, A, B, C, D):
        """Return true if line segments AB and CD intersect."""
        return self._ccw(A, C, D) != self._ccw(B, C, D) and self._ccw(A, B, C) != self._ccw(A, B, D)

    def _get_side(self, A, B, P, tolerance_px=5.0):
        # Calculate cross product (B.x - A.x)*(P.y - A.y) - (B.y - A.y)*(P.x - A.x)
        cp = (B["x"] - A["x"]) * (P["y"] - A["y"]) - (B["y"] - A["y"]) * (P["x"] - A["x"])
        # Distance from point P to line AB
        l2 = (B["x"] - A["x"])**2 + (B["y"] - A["y"])**2
        if l2 == 0: return 0
        import math
        dist = abs(cp) / math.sqrt(l2)
        if dist <= tolerance_px:
            return 0 # Within buffer zone
        return 1 if cp > 0 else -1

    def _run_detectors(self, camera_id, frame, drawn_boxes, settings, current_time, path="main"):
        """Run every registered detector for this frame (fight, fire, ...)."""
        logger.debug(f"[detectors] cam={camera_id} path={path} boxes={len(drawn_boxes)} "
                     f"registry={[d.name for d in detector_base.get_detectors()]}")
        ctx = detector_base.DetectorContext(
            camera_id=camera_id,
            frame=frame,
            boxes=drawn_boxes,
            history=self.object_history.get(camera_id, {}),
            settings=settings,
            now=current_time,
        )
        return detector_base.run_all(ctx)

    def process_frame(self, camera_id: int, frame):
        if not self.active or self.model is None:
            # NOTE: this also disables every registered detector (fire/fight),
            # none of which actually need the YOLO model.
            logger.debug(f"[detectors] cam={camera_id} SKIPPED ENTIRELY — "
                         f"ml active={self.active} model={self.model is not None}")
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
                # Detectors still run on empty frames (fire/smoke need no objects)
                alerts.extend(self._run_detectors(camera_id, frame, drawn_boxes,
                                                  settings, current_time, path="no-detections"))
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
                    "identity": identity,
                    "ghost": False
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
                            # Incident-Level deduplication
                            incident_key = f"{camera_id}_dwelling_{obj_class}"
                            last_inc = self.incident_cache.get(incident_key, 0)
                            if current_time - last_inc > 30.0:
                                if not recognition_service.is_authorized(camera_id, track_id):
                                    self.incident_cache[incident_key] = current_time
                                    # Still update per-track so it doesn't fire immediately again if track is isolated
                                    self.object_history[camera_id][track_id]["last_dwelling_time"] = current_time
                                    
                                    # Create mathematically unique incident ID
                                    import uuid
                                    incident_id = f"inc_{int(current_time)}_{uuid.uuid4().hex[:6]}"
                                    alerts.append({
                                        "id": incident_id,
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
                    bx = (xyxy[0] + xyxy[2]) / 2.0
                    by = xyxy[3]
                    positions.append((cx, cy, current_time, bx, by))
                    
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
                                    incident_key = f"{camera_id}_fleeing"
                                    last_inc = self.incident_cache.get(incident_key, 0)
                                    if current_time - last_inc > 15.0:
                                        if not recognition_service.is_authorized(camera_id, track_id):
                                            self.incident_cache[incident_key] = current_time
                                            hist["last_fleeing_time"] = current_time
                                            
                                            import uuid
                                            incident_id = f"inc_{int(current_time)}_{uuid.uuid4().hex[:6]}"
                                            alerts.append({
                                                "id": incident_id,
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
                    if "positions" in hist and len(hist["positions"]) >= 2 and camera_id in self.tripwires:
                        tripwires_data = self.tripwires[camera_id]
                        lines_to_check = []
                        if tripwires_data and isinstance(tripwires_data, list) and len(tripwires_data) > 0:
                            if isinstance(tripwires_data[0], list):
                                lines_to_check = [l for l in tripwires_data if len(l) == 2]
                            elif len(tripwires_data) == 2:
                                lines_to_check = [tripwires_data]
                                
                        if lines_to_check:
                            fh, fw = frame.shape[:2]
                            cooldown = current_time - hist.get("last_intrusion_time", 0)
                            
                            if cooldown > settings.get("intrusion_cooldown", 10.0):
                                crossed = False
                                pos_history = hist["positions"]
                                
                                for line in lines_to_check:
                                    A = {"x": line[0]["x"] * fw, "y": line[0]["y"] * fh}
                                    B = {"x": line[1]["x"] * fw, "y": line[1]["y"] * fh}
                                    
                                    # Ultra-resilient geometric check: check every single segment in history
                                    for i in range(len(pos_history) - 1):
                                        C = {"x": pos_history[i][3], "y": pos_history[i][4]}
                                        D = {"x": pos_history[i+1][3], "y": pos_history[i+1][4]}
                                        if self._intersect(A, B, C, D):
                                            crossed = True
                                            break
                                            
                                    if crossed:
                                        break
                                        
                                if crossed:
                                    incident_key = f"{camera_id}_intrusion_{obj_class}"
                                    last_inc = self.incident_cache.get(incident_key, 0)
                                    if current_time - last_inc > 5.0:
                                        if not recognition_service.is_authorized(camera_id, track_id):
                                            self.incident_cache[incident_key] = current_time
                                            hist["last_intrusion_time"] = current_time
                                            
                                            import uuid
                                            incident_id = f"inc_{int(current_time)}_{uuid.uuid4().hex[:6]}"
                                            alerts.append({
                                                "id": incident_id,
                                                "camera_id": camera_id,
                                                "type": "intrusion",
                                                "severity": "critical",
                                                "level": "CRITICAL",
                                                "title": f"Tripwire Intrusion: {obj_class.capitalize()}",
                                                "detail": f"A {obj_class} crossed a virtual perimeter line.",
                                                "time": time.strftime("%H:%M:%S"),
                                                "icon": "🚨",
                                                "frame_data": frame
                                            })                    # --------------------------------
                    
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
                        
                        import uuid
                        incident_id = f"inc_{int(current_time)}_{uuid.uuid4().hex[:6]}"
                        alerts.append({
                            "id": incident_id,
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


            # --- PLUGGABLE DETECTORS (fight, fire, ...) ---
            alerts.extend(self._run_detectors(camera_id, frame, drawn_boxes, settings, current_time))

            # Clean up old tracks that left the frame (grace period of 2 seconds)
            # Also inject 'Ghost Boxes' for objects that momentarily disappeared but are still in grace period
            for tid in list(self.object_history[camera_id].keys()):
                if tid not in current_track_ids:
                    time_since_seen = current_time - self.object_history[camera_id][tid]["last_seen"]
                    if time_since_seen > 2.0:
                        del self.object_history[camera_id][tid]
                    elif time_since_seen > 0.05: # if it missed at least one frame
                        hist = self.object_history[camera_id][tid]
                        # Frozen replay of the last known box. Flagged so motion
                        # detectors do not read the frozen position as "stopped".
                        drawn_boxes.append({
                            "id": tid,
                            "class": hist.get("last_class", "unknown"),
                            "conf": hist.get("last_conf", 0.0),
                            "box": hist.get("last_box", [0, 0, 0, 0]),
                            "identity": hist.get("last_identity", None),
                            "ghost": True
                        })
                    
            return alerts, drawn_boxes
            
        except Exception as e:
            # Anything raised above this point (tracking, recognition, tripwire)
            # also prevents the detectors from ever running for this frame.
            logger.exception(f"Inference error on camera {camera_id} — detectors did NOT run: {e}")
            return [], []

ml_service = MLService()
