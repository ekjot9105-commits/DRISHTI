import time
import os
try:
    from ultralytics import YOLO
    import numpy as np
except ImportError:
    print("Please install ultralytics to run benchmarks.")
    exit(1)

def benchmark(model_path, iterations=100):
    try:
        model = YOLO(model_path)
    except Exception as e:
        print(f"Failed to load {model_path}: {e}")
        return None
        
    print(f"\n--- Benchmarking {os.path.basename(model_path)} ---")
    
    # Warmup
    dummy_img = np.zeros((640, 640, 3), dtype=np.uint8)
    for _ in range(5):
        model(dummy_img, verbose=False, device='cpu')
        
    # Benchmark
    start = time.time()
    for _ in range(iterations):
        model(dummy_img, verbose=False, device='cpu')
    end = time.time()
    
    avg_latency = (end - start) / iterations
    fps = 1.0 / avg_latency
    
    print(f"Total time: {end - start:.2f} s")
    print(f"Avg Latency: {avg_latency*1000:.2f} ms")
    print(f"FPS: {fps:.2f}")
    return fps

if __name__ == "__main__":
    print("Preparing models for benchmark...")
    
    models = {
        "yolov8n_pt": "yolov8n.pt",
        "yolov8s_pt": "yolov8s.pt"
    }
    
    # Download/Load base models
    for name, path in models.items():
        if not os.path.exists(path):
            print(f"Downloading {path}...")
            YOLO(path) # downloads automatically
            
    # Export to ONNX
    print("Exporting models to ONNX...")
    yolo_n = YOLO("yolov8n.pt")
    if not os.path.exists("yolov8n.onnx"):
        yolo_n.export(format="onnx")
        
    yolo_s = YOLO("yolov8s.pt")
    if not os.path.exists("yolov8s.onnx"):
        yolo_s.export(format="onnx")
        
    print("\nStarting benchmarks on Intel Core Ultra 5 CPU...")
    
    results = {}
    results['yolov8n.pt'] = benchmark("yolov8n.pt")
    results['yolov8n.onnx'] = benchmark("yolov8n.onnx")
    results['yolov8s.pt'] = benchmark("yolov8s.pt")
    results['yolov8s.onnx'] = benchmark("yolov8s.onnx")
    
    print("\n================ BENCHMARK RESULTS ================")
    for model, fps in results.items():
        if fps:
            print(f"{model.ljust(15)} : {fps:.2f} FPS")
    print("===================================================")
    print("Note: If ONNX is faster, update backend/app/services/ml_inference.py to use the .onnx model.")
