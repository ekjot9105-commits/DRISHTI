from app.services.video_ingestion import stream_manager
import time
stream_manager.start_stream(1, 'car-detection.mp4', 'file')
for _ in range(20):
    time.sleep(1)
    s = stream_manager.get_stream(1)
    if s:
        print(f"fps: {s.fps_actual:.1f}, boxes: {len(s.latest_boxes)}, active: {s.is_active()}, err: {s.error}")
    else:
        print("no stream")
