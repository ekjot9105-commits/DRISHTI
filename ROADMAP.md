# IBVAP Project Roadmap (SIH 2026 - PS 26187)

This document outlines the master implementation plan for the Intelligent Border Video Analytics Platform (IBVAP). It maps directly to the Ministry of Home Affairs (SSB) requirements for cost-effective, AI-driven border surveillance using existing IP CCTV networks.

## ✅ Phase 1: Foundation & Command Center UI (Completed)
- [x] Basic React frontend shell and navigation.
- [x] FastAPI backend boilerplate with SQLite database.
- [x] Camera Management module (Add, Start, Stop, Delete sources via RTSP or File).
- [x] WebSocket infrastructure for streaming video frames to the frontend.
- [x] **UI Overhaul**: Redesign using "Zenith Sentinel" design system (Dark mode, professional Command Center aesthetic, KPI stats bar).

## ✅ Phase 2: Real-time AI Alerts & Visual Tracking (Completed)
- [x] Integrate YOLOv8 ML pipeline for CPU-based object detection (human/vehicle).
- [x] Implement backend tracking and "Prolonged Dwelling" alert logic.
- [x] Create WebSocket infrastructure for real-time alert broadcasting.
- [x] Wire live alerts into the frontend UI (Incident Log & KPI Bar).
- [x] Visually draw AI bounding boxes and tracking IDs directly onto the live camera feeds.

## ✅ Phase 3: Watchlist & Recognition Modules (Completed)
- [x] Integrate Facial Recognition using `DeepFace` (VGG-Face model with CLAHE night-vision preprocessing).
- [x] Implement Automated License Plate Recognition (ALPR) via OCR (`EasyOCR`).
- [x] Create UI for adding/managing individuals and vehicles on a watchlist.
- [x] Trigger CRITICAL alerts when watchlist entities are detected in the camera feeds.
- [x] Tracking Optimizations: Ghost boxes, ByteTrack tracking, and dynamic FPS pacing for files.

## ✅ Phase 4: Audit & Analytics Dashboard (Completed)
- [x] **Alert Center**: Immutable evidence and audit log for acknowledging, resolving, and archiving historical incidents.
- [x] **Analytics Dashboard**: Time-series charts for detection volume, severity breakdowns, and camera-by-camera activity.
- [x] **Geospatial Heatmap**: Dark-mode OpenStreetMap plotting hotspot activity zones along the border based on detection frequency.

## 🚀 Phase 5: Intrusion Detection & Evidence Vault (Planned)
*Directly addresses the "Virtual fence Intrusion detection" and "event logging" requirements in PS 26187.*
- [ ] **Virtual Tripwires / Fences**: Allow operators to draw lines/polygons on the live video feed in the UI.
- [ ] **Intrusion Alerts**: Backend logic to detect if a tracked human/vehicle bounding box crosses the defined polygon coordinates.
- [ ] **Evidence Vault**: Automatically save the physical image frame (or a 5-second video buffer) when a CRITICAL alert (intrusion or watchlist match) is triggered.
- [ ] **Live Geospatial Tracking**: Plot active camera statuses and live pinging alerts on a geospatial map view.

## 🔮 Phase 6: SIH Gold Standard Polish & Advanced Behaviors (Future)
*Directly addresses "Suspicious activity", "Night-time movement", and "Command and Control integration" in PS 26187.*
- [ ] **Suspicious Behavioral Analytics**: Detect fast-paced movement (running/fleeing) or crowd gatherings (3+ people congregating for > 1 min).
- [ ] **Low-Light / Thermal Enhancement**: Add a user-toggled "Night Mode" that applies Zero-DCE (Deep Curve Estimation) to drastically brighten pitch-black feeds.
- [ ] **Webhooks for C2 Integration**: Expose a REST webhook settings page so the platform can push JSON alerts to the SSB's centralized command servers.
- [ ] **UI Localization (Hindi/English)**: Add a language toggle to ensure the UI is fully accessible to field operators.
- [ ] **Edge Optimization (TensorRT)**: Export the ML models to ONNX/TensorRT to minimize CPU/GPU load, heavily satisfying the "cost-effective" requirement.
