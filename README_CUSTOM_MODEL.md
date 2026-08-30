# Integrating Custom ML Models into DRISHTI

The DRISHTI platform is designed to be modular. While it ships with YOLOv8 for rapid deployment, you can easily swap the object detection engine for your own custom PyTorch, TensorFlow, or ONNX models without breaking the tracking, tripwires, or Alert Center.

## 1. Where to inject your model

The entire Machine Learning pipeline lives in `backend/app/services/ml_inference.py`. 

### The `MLService` Class
Inside `ml_inference.py`, locate the `MLService.__init__` method. This is where models are loaded into memory:

```python
class MLService:
    def __init__(self):
        # 1. REMOVE the YOLO loading:
        # self.model = YOLO('yolov8s.pt')
        
        # 2. INSERT your custom model loading here:
        import torch
        self.model = torch.load("my_custom_model.pth")
        self.model.eval()
        
        # 3. Define the classes your model predicts
        self.classes = {0: "person", 1: "vehicle", 2: "drone"}
```

## 2. Formatting the Output

The DRISHTI engine relies on the **ByteTrack** multi-object tracker to assign permanent IDs to targets over time. ByteTrack strictly expects detection boxes in a specific format.

Locate the `_inference_loop` method, specifically this section:

```python
# --- REPLACE THIS ---
results = self.model(frame, stream=True, verbose=False)
detections = []
for r in results:
    for box in r.boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        conf = box.conf[0].item()
        cls_id = int(box.cls[0].item())
        detections.append([x1, y1, x2, y2, conf, cls_id])
```

You must replace that logic with your model's inference code. Ensure that your output perfectly matches the `[x1, y1, x2, y2, conf, cls_id]` structure.

```python
# --- WITH YOUR CUSTOM MODEL ---
input_tensor = self.preprocess(frame)
raw_output = self.model(input_tensor)

detections = []
for obj in raw_output:
    # 1. Extract coordinates (ensure they are absolute pixel values, not normalized)
    x1, y1, x2, y2 = obj.box
    
    # 2. Extract confidence score (0.0 to 1.0)
    conf = obj.score
    
    # 3. Extract integer class ID
    cls_id = obj.class_index
    
    # 4. Append to array in EXACTLY this order:
    detections.append([x1, y1, x2, y2, conf, cls_id])
```

### Critical Requirements for Custom Models:
1. **Coordinate Scale:** Bounding boxes must be absolute coordinates corresponding to the `frame` array dimensions (e.g., `0` to `1920` for a 1080p feed), not normalized `0.0` to `1.0`.
2. **Synchronous Execution:** The `_inference_loop` must return detections relatively fast. If your custom model takes >100ms per frame, the video queue will automatically start dropping frames to keep the pipeline real-time.
3. **Class Mapping:** Make sure the `cls_id` integer properly maps to a string in your `self.classes` dictionary. DRISHTI specifically looks for `"person"` and `"vehicle"` strings when triggering face recognition, ALPR, and behavioral analytics.

## 3. Advanced: GPU Acceleration

If you are deploying DRISHTI on a production server with an NVIDIA GPU, ensure your custom model explicitly moves to CUDA:

```python
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
self.model.to(device)
```

The rest of the pipeline (WebSockets, Database, File Saving, and Alerting) runs completely asynchronously on separate threads, so your inference loop gets maximum dedicated CPU/GPU priority.
