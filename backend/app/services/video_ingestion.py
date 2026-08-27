"""
Video Ingestion Service — Captures frames from video files and RTSP streams.
Supports both pre-recorded videos (for demo) and live CCTV cameras.
"""
import cv2
import time
import threading
import logging
from pathlib import Path
from typing import Optional

from app.core.config import DEFAULT_FPS, FRAME_WIDTH, FRAME_HEIGHT, JPEG_QUALITY

logger = logging.getLogger(__name__)


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

            self.running = True
            self.error = None
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()
            logger.info(f"Camera {self.camera_id}: Started stream from {self.source}")
            return True

        except Exception as e:
            self.error = str(e)
            logger.error(f"Camera {self.camera_id}: Error starting stream: {e}")
            return False

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
                    # Loop video files for demo purposes
                    # Releasing and reopening is safer for all video codecs
                    self.cap.release()
                    self.cap = cv2.VideoCapture(str(Path(self.source)))
                    if not self.cap.isOpened():
                        self.error = "Failed to restart video file"
                        self.running = False
                        break
                    time.sleep(0.1)
                    continue
                else:
                    # RTSP stream lost — attempt reconnect
                    logger.warning(f"Camera {self.camera_id}: Stream lost, reconnecting...")
                    time.sleep(2)
                    self.cap = cv2.VideoCapture(self.source, cv2.CAP_FFMPEG)
                    continue

            # Resize frame to standard dimensions
            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

            # Encode as JPEG for streaming
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
            _, jpeg = cv2.imencode('.jpg', frame, encode_params)

            with self.lock:
                self.frame = frame
                self.jpeg_frame = jpeg.tobytes()
                self.frame_count += 1

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


class StreamManager:
    """
    Manages all active video streams.
    Provides central access point for starting/stopping camera feeds.
    """

    def __init__(self):
        self.streams: dict[int, VideoStream] = {}
        self.lock = threading.Lock()

    def start_stream(self, camera_id: int, source: str,
                     source_type: str, target_fps: int = DEFAULT_FPS) -> bool:
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
