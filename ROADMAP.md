# IBVAP Project Roadmap

This document outlines the master implementation plan for the Intelligent Border Video Analytics Platform (IBVAP). It serves as the single source of truth for tracking phase progression and completed tasks.

## 🟢 Phase 1: Foundation & Command Center UI (Completed)
- [x] Basic React frontend shell and navigation.
- [x] FastAPI backend boilerplate with SQLite database.
- [x] Camera Management module (Add, Start, Stop, Delete sources via RTSP or File).
- [x] WebSocket infrastructure for streaming video frames to the frontend.
- [x] **UI Overhaul**: Redesign using Stitch AI's "Zenith Sentinel" design system (Dark mode, professional Command Center aesthetic, KPI stats bar).

## 🟢 Phase 2: Real-time AI Alerts & Visual Tracking (Completed)
- [x] Integrate YOLOv8 ML pipeline for CPU-based object detection (human/vehicle).
- [x] Implement backend tracking and "Prolonged Dwelling" alert logic.
- [x] Create WebSocket infrastructure for real-time alert broadcasting.
- [x] Wire live alerts into the frontend UI (Incident Log & KPI Bar).
- [x] Visually draw AI bounding boxes and tracking IDs directly onto the live camera feeds.

## ⚪ Phase 3: Watchlist Management (Planned)
- [ ] Implement facial recognition pipeline.
- [ ] Implement Automated License Plate Recognition (ALPR).
- [ ] Create UI for adding/managing individuals and vehicles on a watchlist.
- [ ] Trigger CRITICAL alerts when watchlist entities are detected in the camera feeds.

## ⚪ Phase 4: Analytics Dashboard (Planned)
- [ ] Store historical detection events and alert logs in the database.
- [ ] Create data visualization charts (hourly detection frequency, common alert types).
- [ ] Generate geospatial heatmaps to identify high-activity zones.

## ⚪ Phase 5: Advanced Features & Deployment (Planned)
- [ ] Geospatial Map View (plot camera locations and live alerts on a map).
- [ ] Evidence Vault (securely save short video clips of high-priority alerts).
- [ ] System Settings & User Roles (Admin vs Operator permissions).
- [ ] Production deployment Dockerization and optimization.
