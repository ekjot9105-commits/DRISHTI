"""
Video Ingestion Service — Captures frames from video files and RTSP streams.
Supports both pre-recorded videos (for demo) and live CCTV cameras.
"""
import cv2
import numpy as np
import time
import threading
import logging
from pathlib import Path
from typing import Optional

from app.core.config import DEFAULT_FPS, FRAME_WIDTH, FRAME_HEIGHT, JPEG_QUALITY
import queue

logger = logging.getLogger(__name__)

# Global queue to bridge sync OpenCV thread to async FastAPI websocket
alert_queue = queue.Queue()


class VideoStream:
    """
    Manages a single video source (file or RTSP).
    Captures frames in a background thread for non-blocking operation.
    """

    def __init__(self, source: str, source_type: str, camera_id: int,
                 target_fps: int = DEFAULT_FPS):
        self.source = source
        self.source_type = source_type
        self.camera_id = camera_id
        self.target_fps = target_fps
        self.cap: Optional[cv2.VideoCapture] = None
        self.frame = None
        self.jpeg_frame: Optional[bytes] = None
        self.running = False
        self.lock = threading.Lock()
        self.thread: Optional[threading.Thread] = None
        self.inference_thread: Optional[threading.Thread] = None
        self.inference_queue = queue.Queue(maxsize=1)
        self.latest_boxes = []
        self.error: Optional[str] = None
        self.frame_count = 0
        self.fps_actual = 0.0

    def start(self) -> bool:
        """Open the video source and start capturing frames."""
        try:
            if self.source_type == "rtsp":
                self.cap = cv2.VideoCapture(self.source, cv2.CAP_FFMPEG)
            else:
                # File source
                path = Path(self.source)
                if not path.exists():
                    self.error = f"Video file not found: {self.source}"
                    logger.error(self.error)
                    return False
                self.cap = cv2.VideoCapture(str(path))

            if not self.cap.isOpened():
                self.error = f"Failed to open video source: {self.source}"
                logger.error(self.error)
                return False

            # Lock to native FPS to prevent file streams from playing in fast-forward
            if self.source_type == "file":
                native_fps = self.cap.get(cv2.CAP_PROP_FPS)
                if native_fps > 0:
                    self.target_fps = native_fps

            self.running = True
            self.error = None
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()
            
            self.inference_thread = threading.Thread(target=self._inference_loop, daemon=True)
            self.inference_thread.start()
            
            logger.info(f"Camera {self.camera_id}: Started stream from {self.source}")
            return True

        except Exception as e:
            self.error = str(e)
            logger.error(f"Camera {self.camera_id}: Error starting stream: {e}")
            return False

    def _render(self, frame):
        """Queue the frame for inference, draw overlays, and publish it as JPEG.

        Shared by the capture loop (file/RTSP) and by PushStream (phone camera).
        """
        # Send every 3rd frame to the async inference queue
        if self.frame_count % 3 == 0:
            try:
                if self.inference_queue.full():
                    self.inference_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self.inference_queue.put_nowait(frame.copy())
            except queue.Full:
                pass

        with self.lock:
            current_boxes = list(self.latest_boxes)

        # Draw Tripwires if exist
        from app.services.ml_inference import ml_service
        tripwires = ml_service.tripwires.get(self.camera_id)
        if tripwires and isinstance(tripwires, list) and len(tripwires) > 0:
            h, w = frame.shape[:2]
            
            # Check if new multi-line format
            if isinstance(tripwires[0], list):
                for line in tripwires:
                    if len(line) == 2:
                        pt1 = (int(line[0]['x'] * w), int(line[0]['y'] * h))
                        pt2 = (int(line[1]['x'] * w), int(line[1]['y'] * h))
                        cv2.line(frame, pt1, pt2, (0, 0, 255), 2)
                        # Security Boundary UI Enhancements
                        cx, cy = (pt1[0] + pt2[0]) // 2, (pt1[1] + pt2[1]) // 2
                        cv2.putText(frame, f"MONITORED BOUNDARY [ACTIVE]", (cx - 100, cy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
                        # Direction arrows (simple offset)
                        cv2.arrowedLine(frame, (cx, cy), (cx, cy - 30), (0, 255, 255), 1, tipLength=0.3)
            # Fallback for old single-line format
            elif len(tripwires) == 2:
                pt1 = (int(tripwires[0]['x'] * w), int(tripwires[0]['y'] * h))
                pt2 = (int(tripwires[1]['x'] * w), int(tripwires[1]['y'] * h))
                cv2.line(frame, pt1, pt2, (0, 0, 255), 2)

        # Draw bounding boxes onto the frame
        for obj in current_boxes:
            x1, y1, x2, y2 = [int(v) for v in obj['box']]
            
            identity = obj.get('identity')
            if identity:
                label = f"[{identity}]"
                color = (0, 0, 255) # Red for identified matches
            else:
                conf_pct = int(obj.get('conf', 0.0) * 100)
                label = f"{obj['class']} {conf_pct}%"
                # Cyan color for person, Amber for vehicle (BGR format for OpenCV)
                color = (255, 235, 138) if obj['class'] == 'person' else (0, 165, 255)
            
            # Draw box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw label background
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(frame, (x1, y1 - th - 5), (x1 + tw, y1), color, -1)
            
            # Draw label text
            cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

        # Encode as JPEG for streaming
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
        _, jpeg = cv2.imencode('.jpg', frame, encode_params)

        with self.lock:
            self.frame = frame
            self.jpeg_frame = jpeg.tobytes()
            self.frame_count += 1

    def _capture_loop(self):
        """Background thread that continuously captures frames."""
        frame_interval = 1.0 / self.target_fps
        fps_timer = time.time()
        fps_count = 0

        while self.running:
            start_time = time.time()

            if self.cap is None or not self.cap.isOpened():
                self.error = "Video source disconnected"
                self.running = False
                break

            ret, frame = self.cap.read()

            if not ret:
                if self.source_type == "file":
                    # Loop video files by rewinding to frame 0 (fast and prevents thread blocking)
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = self.cap.read()
                    if not ret:
                        self.error = "Failed to rewind video file"
                        self.running = False
                        break
                else:
                    # RTSP stream lost — attempt reconnect
                    logger.warning(f"Camera {self.camera_id}: Stream lost, reconnecting...")
                    time.sleep(2)
                    self.cap = cv2.VideoCapture(self.source, cv2.CAP_FFMPEG)
                    continue

            # Resize frame to standard dimensions
            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

            self._render(frame)

            # Calculate actual FPS
            fps_count += 1
            elapsed = time.time() - fps_timer
            if elapsed >= 1.0:
                self.fps_actual = fps_count / elapsed
                fps_count = 0
                fps_timer = time.time()

            # Throttle to target FPS
            processing_time = time.time() - start_time
            sleep_time = frame_interval - processing_time
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _inference_loop(self):
        """Background thread specifically for running ML inference asynchronously."""
        from app.services.ml_inference import ml_service
        from app.core.system_monitor import sys_monitor
        import time
        
        while self.running:
            try:
                frame = self.inference_queue.get(timeout=1.0)
                if frame is None:
                    break
                
                start_time = time.time()
                alerts, drawn_boxes = ml_service.process_frame(self.camera_id, frame)
                latency = time.time() - start_time
                
                sys_monitor.update_inference_stats(latency)
                sys_monitor.update_processing_stats(latency + 0.05, self.fps_actual, self.fps_actual)
                sys_monitor.set_service_status("yolo", "active")
                sys_monitor.set_service_status("tracker", "active")
                sys_monitor.set_service_status("tripwire", "active")
                
                for alert in alerts:
                    alert_queue.put(alert)
                    
                with self.lock:
                    self.latest_boxes = drawn_boxes
                    
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Camera {self.camera_id} Inference error: {e}")

    def get_frame(self):
        """Get the latest raw frame (numpy array)."""
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

    def get_jpeg_frame(self) -> Optional[bytes]:
        """Get the latest JPEG-encoded frame bytes."""
        with self.lock:
            return self.jpeg_frame

    def stop(self):
        """Stop capturing and release resources."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3)
            
        if self.inference_thread and self.inference_thread.is_alive():
            try:
                if self.inference_queue.full():
                    self.inference_queue.get_nowait()
            except queue.Empty:
                pass
            self.inference_queue.put(None)
            self.inference_thread.join(timeout=3)
            
        if self.cap:
            self.cap.release()
            self.cap = None
        logger.info(f"Camera {self.camera_id}: Stream stopped")

    def is_active(self) -> bool:
        return self.running and self.error is None

    def get_status(self) -> dict:
        return {
            "camera_id": self.camera_id,
            "active": self.is_active(),
            "fps": round(self.fps_actual, 1),
            "frame_count": self.frame_count,
            "error": self.error,
        }


class PushStream(VideoStream):
    """A camera whose frames are pushed in over a WebSocket (phone-as-camera).

    There is no cv2.VideoCapture: the browser on the phone sends JPEG frames to
    /ws/cameras/{id}/push, and each one goes through the exact same render +
    inference path as a file or RTSP source.
    """

    STALE_AFTER = 15.0  # seconds without a pushed frame before we call it dead

    def __init__(self, camera_id: int, target_fps: int = DEFAULT_FPS):
        super().__init__(source="push", source_type="phone",
                         camera_id=camera_id, target_fps=target_fps)
        self.last_push = 0.0
        self._fps_timer = time.time()
        self._fps_count = 0

    def start(self) -> bool:
        """No capture thread — only the inference worker."""
        self.running = True
        self.error = None
        self.last_push = 0.0
        self._fps_timer = time.time()
        self.inference_thread = threading.Thread(target=self._inference_loop, daemon=True)
        self.inference_thread.start()
        logger.info(f"Camera {self.camera_id}: Awaiting pushed frames (phone source)")
        return True

    def push_jpeg(self, data: bytes) -> bool:
        """Decode and publish one pushed JPEG frame. Returns False if undecodable."""
        if not self.running:
            return False
        frame = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            return False

        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
        self._render(frame)

        self.last_push = time.time()
        self._fps_count += 1
        elapsed = self.last_push - self._fps_timer
        if elapsed >= 1.0:
            self.fps_actual = self._fps_count / elapsed
            self._fps_count = 0
            self._fps_timer = self.last_push
        return True

    def is_active(self) -> bool:
        if not self.running or self.error:
            return False
        if self.last_push == 0.0:
            return True  # connected, first frame not in yet
        return (time.time() - self.last_push) < self.STALE_AFTER


class StreamManager:
    """
    Manages all active video streams.
    Provides central access point for starting/stopping camera feeds.
    """

    def __init__(self):
        self.streams: dict[int, VideoStream] = {}
        self.lock = threading.Lock()

    def start_stream(self, camera_id: int, source: str,
                     source_type: str, target_fps: int = 10) -> bool:
        """Start a new video stream for a camera."""
        with self.lock:
            # Stop existing stream if any
            if camera_id in self.streams:
                self.streams[camera_id].stop()

            stream = VideoStream(source, source_type, camera_id, target_fps)
            success = stream.start()

            if success:
                self.streams[camera_id] = stream
            return success

    def start_push_stream(self, camera_id: int) -> "PushStream":
        """Create (or restart) a phone-pushed stream and return it."""
        with self.lock:
            if camera_id in self.streams:
                self.streams[camera_id].stop()
            stream = PushStream(camera_id)
            stream.start()
            self.streams[camera_id] = stream
            return stream

    def stop_stream(self, camera_id: int):
        """Stop a camera stream."""
        with self.lock:
            if camera_id in self.streams:
                self.streams[camera_id].stop()
                del self.streams[camera_id]

    def get_stream(self, camera_id: int) -> Optional[VideoStream]:
        """Get a specific camera stream."""
        return self.streams.get(camera_id)

    def get_all_streams(self) -> dict[int, VideoStream]:
        """Get all active streams."""
        return dict(self.streams)

    def get_jpeg_frame(self, camera_id: int) -> Optional[bytes]:
        """Get latest JPEG frame from a specific camera."""
        stream = self.streams.get(camera_id)
        if stream:
            return stream.get_jpeg_frame()
        return None

    def stop_all(self):
        """Stop all streams."""
        with self.lock:
            for stream in self.streams.values():
                stream.stop()
            self.streams.clear()

    def get_status(self) -> list[dict]:
        """Get status of all streams."""
        return [stream.get_status() for stream in self.streams.values()]


# Singleton stream manager
stream_manager = StreamManager()
