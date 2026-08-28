from app.services.video_ingestion import stream_manager
import time
stream_manager.start_stream(1, 'car-detection.mp4', 'file')
time.sleep(10)
print(stream_manager.get_status())
