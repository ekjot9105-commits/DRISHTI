import time
import urllib.request
import urllib.error
import json

API_BASE = "http://localhost:8000"

print("==================================================")
print("  DRISHTI END-TO-END SYSTEM PERFORMANCE TEST  ")
print("==================================================\n")

print("Checking if backend is active...")
try:
    res = urllib.request.urlopen(f"{API_BASE}/api/system/status")
    if res.getcode() != 200:
        print("Failed to reach system status endpoint.")
        exit(1)
except Exception as e:
    print(f"Backend not reachable: {e}")
    exit(1)

print("Backend is alive. Monitoring performance for 30 seconds...\n")
print(f"{'Time':<5} | {'Source FPS':<10} | {'ML FPS':<8} | {'Latency (ML)':<12} | {'Latency (E2E)':<13} | {'CPU %':<8} | {'RAM %':<8}")
print("-" * 80)

metrics = {
    'source_fps': [],
    'inference_fps': [],
    'inference_latency': [],
    'processing_latency': [],
    'cpu': [],
    'ram': []
}

for i in range(30):
    try:
        res = urllib.request.urlopen(f"{API_BASE}/api/system/status", timeout=2)
        if res.getcode() == 200:
            data = json.loads(res.read().decode('utf-8'))
            
            src_fps = data.get('source_fps', 0)
            ml_fps = data.get('inference_fps', 0)
            ml_lat = data.get('inference_latency_ms', 0)
            e2e_lat = data.get('processing_latency_ms', 0)
            cpu = data.get('cpu_usage', 0)
            ram = data.get('memory_usage', 0)
            
            metrics['source_fps'].append(src_fps)
            metrics['inference_fps'].append(ml_fps)
            metrics['inference_latency'].append(ml_lat)
            metrics['processing_latency'].append(e2e_lat)
            metrics['cpu'].append(cpu)
            metrics['ram'].append(ram)
            
            print(f"{i+1:<4}s | {src_fps:<10} | {ml_fps:<8} | {ml_lat:<10} ms | {e2e_lat:<11} ms | {cpu:<6} % | {ram:<6} %")
    except Exception as e:
        print(f"Error fetching data: {e}")
        
    time.sleep(1)

def avg(lst):
    return sum(lst)/len(lst) if lst else 0

print("\n==================================================")
print("  FINAL PERFORMANCE REPORT (30s AVERAGE)  ")
print("==================================================")
print(f"Average Source FPS      : {avg(metrics['source_fps']):.2f}")
print(f"Average Inference FPS   : {avg(metrics['inference_fps']):.2f}")
print(f"Average Inference Lat   : {avg(metrics['inference_latency']):.2f} ms")
print(f"Average E2E Latency     : {avg(metrics['processing_latency']):.2f} ms")
print(f"Average CPU Usage       : {avg(metrics['cpu']):.2f} %")
print(f"Average RAM Usage       : {avg(metrics['ram']):.2f} %")
print("==================================================")

if avg(metrics['processing_latency']) < 200:
    print("✅ TEST PASSED: Pipeline is highly responsive and asynchronous.")
else:
    print("⚠️ WARNING: E2E latency is high. Backlog may be accumulating.")

if avg(metrics['inference_fps']) >= 10:
    print("✅ TEST PASSED: ML FPS is sufficient for real-time tracking.")
else:
    print("⚠️ WARNING: ML FPS is dropping below acceptable real-time bounds.")
