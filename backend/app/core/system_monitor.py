import psutil
import time
import threading

class SystemMonitor:
    def __init__(self):
        self.stats = {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "source_fps": 0.0,
            "rendered_fps": 0.0,
            "inference_fps": 0.0,
            "inference_latency_ms": 0.0,
            "processing_latency_ms": 0.0,
            "services": {
                "yolo": "idle",
                "tracker": "idle",
                "face_recognition": "idle",
                "alpr": "idle",
                "tripwire": "idle",
                "night_mode": "disabled"
            }
        }
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def _monitor_loop(self):
        while not self._stop_event.is_set():
            try:
                cpu = psutil.cpu_percent(interval=1.0)
                mem = psutil.virtual_memory().percent
                with self._lock:
                    self.stats["cpu_usage"] = cpu
                    self.stats["memory_usage"] = mem
            except Exception:
                pass

    def update_inference_stats(self, latency_sec: float):
        with self._lock:
            self.stats["inference_latency_ms"] = round(latency_sec * 1000, 2)
            self.stats["inference_fps"] = round(1.0 / latency_sec, 2) if latency_sec > 0 else 0.0
            
    def update_processing_stats(self, processing_latency_sec: float, source_fps: float, rendered_fps: float):
        with self._lock:
            self.stats["processing_latency_ms"] = round(processing_latency_sec * 1000, 2)
            self.stats["source_fps"] = round(source_fps, 2)
            self.stats["rendered_fps"] = round(rendered_fps, 2)

    def set_service_status(self, service: str, status: str):
        with self._lock:
            if service in self.stats["services"]:
                self.stats["services"][service] = status

    def get_stats(self):
        with self._lock:
            return dict(self.stats)

sys_monitor = SystemMonitor()
