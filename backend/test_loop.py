import cv2
from ultralytics import YOLO
model = YOLO('yolov8n.pt')
cap = cv2.VideoCapture('car-detection.mp4')
for i in range(10): cap.read()
ret, frame = cap.read()
res = model.track(frame, persist=True)
print('Classes detected:', res[0].boxes.cls.tolist() if res[0].boxes else 'none')
res2 = model.track(frame, persist=True, classes=[0, 2, 3, 5, 7])
print('Classes detected with filter:', res2[0].boxes.cls.tolist() if res2[0].boxes else 'none')
