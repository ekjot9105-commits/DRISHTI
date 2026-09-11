# DRISHTI — File-by-File Reference

Complete inventory of every source file in the DRISHTI project, with purpose, size, key exports, and relationships.

---

## Root Files

| File | Size | Purpose |
|------|------|---------|
| [`.env.example`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/.env.example) | 1 KB | Template for environment variables |
| [`README.md`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/README.md) | 8 KB | Complete project overview |
| [`CHANGELOG.md`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/CHANGELOG.md) | 2 KB | Development history (Phases 1–7) |
| [`.gitignore`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/.gitignore) | — | Git ignore rules |

---

## Backend — `backend/`

### Core (`backend/app/core/`)

| File | Lines | Exports | Purpose |
|------|-------|---------|---------|
| [`config.py`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/app/core/config.py) | ~40 | `BASE_DIR`, `DATA_DIR`, `EVIDENCE_DIR`, `FACES_DIR`, `SAMPLE_VIDEOS_DIR`, `DEMO_VIDEOS_DIR`, `DATABASE_URL`, `DEFAULT_FPS`, `FRAME_WIDTH`, `FRAME_HEIGHT`, `JPEG_QUALITY` | Environment loading, path constants, frame defaults. Creates data directories on import. |
| [`database.py`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/app/core/database.py) | ~90 | `engine`, `SessionLocal`, `get_db()`, `init_db()`, `Camera`, `Event`, `WatchlistFace`, `WatchlistPlate` | SQLAlchemy engine, session factory, all ORM models, table creation. |
| [`settings_manager.py`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/app/core/settings_manager.py) | ~100 | `load_settings()`, `save_settings()`, `DEFAULT_SETTINGS` | JSON-backed settings with comprehensive defaults. All detection thresholds defined here. |
| [`system_monitor.py`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/app/core/system_monitor.py) | ~100 | `sys_monitor` (singleton), `SystemMonitor` class | Background psutil thread (CPU, memory), FPS tracking, service status, inference latency. |

### Main Entry Point

| File | Lines | Exports | Purpose |
|------|-------|---------|---------|
| [`main.py`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/app/main.py) | ~180 | `app` (FastAPI instance) | App creation, lifespan handler, CORS, router registration, static file mounts, `/api/health` endpoint, `alert_dispatcher()` async loop, `_save_evidence()`, `_send_webhook()`. |

### API Routers (`backend/app/api/`)

| File | Lines | Prefix | Endpoints |
|------|-------|--------|-----------|
| [`cameras.py`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/app/api/cameras.py) | 250 | `/api/cameras` | List, add, start, stop, delete cameras. Tripwire update. Demo list/launch. Phone register. Stream status. |
| [`events.py`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/app/api/events.py) | 155 | `/api/events` | Query events (filters), update status, stats, heatmap, evidence download, blockchain verification. |
| [`reports.py`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/app/api/reports.py) | 188 | `/api/reports` | PDF report generation via ReportLab. Includes metadata table, evidence image, blockchain data, QR code. |
| [`settings.py`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/app/api/settings.py) | 16 | `/api/settings` | GET/PATCH settings.json. |
| [`system.py`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/app/api/system.py) | 78 | `/api/system` | System status, threat score, LAN URL discovery, QR code generation. |
| [`watchlist.py`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/app/api/watchlist.py) | 104 | `/api/watchlist` | Face CRUD (with DeepFace validation), plate CRUD. |

### WebSocket (`backend/app/ws/`)

| File | Lines | Exports | Purpose |
|------|-------|---------|---------|
| [`video_stream.py`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/app/ws/video_stream.py) | 167 | `router`, `alert_subscribers`, `broadcast_alert()` | Three WS endpoints: `/ws/camera/{id}` (frame stream at ~15 FPS), `/ws/alerts` (alert broadcast), `/ws/cameras/{id}/push` (phone frame receive). |

### Services (`backend/app/services/`)

| File | Lines | Exports | Purpose |
|------|-------|---------|---------|
| [`video_ingestion.py`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/app/services/video_ingestion.py) | ~350 | `stream_manager` (singleton), `StreamManager`, `VideoStream`, `PushStream`, `alert_queue` | Video capture threads, frame buffering, JPEG encoding, inference thread dispatch, RTSP reconnect, video looping, ghost box rendering, tripwire drawing. |
| [`ml_inference.py`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/app/services/ml_inference.py) | ~300 | `ml_service` (singleton), `MLService` | YOLO model loading (priority: ONNX → PT), `process_frame()`: detection, tracking, confidence filter, tripwire intersection, dwelling, fleeing, crowd logic, detector dispatch, recognition dispatch. Night mode. |
| [`recognition.py`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/app/services/recognition.py) | 232 | `recognition_service` (singleton), `RecognitionService` | Lazy-loaded DeepFace (VGG-Face + RetinaFace) and EasyOCR. Track-and-check cache. Multi-observation confirmation. Watchlist DB matching. Alert triggering. |
| [`blockchain.py`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/app/services/blockchain.py) | 148 | `blockchain_service` (singleton), `BlockchainService`, `Block` | SHA-256 proof-of-work blockchain. Genesis block. Async mining queue with dedicated thread. JSON persistence. Chain verification. |
| [`threat_score.py`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/app/services/threat_score.py) | 165 | `threat_service` (singleton), `ThreatScoreService`, `classify()` | Rolling 0–100 threat meter. Exponential decay. Severity bands. Per-camera breakdown. Top contributors. Thread-safe. |

### Detectors (`backend/app/services/detectors/`)

| File | Lines | Exports | Purpose |
|------|-------|---------|---------|
| [`base.py`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/app/services/detectors/base.py) | ~80 | `Detector` (ABC), `DetectorContext` (dataclass), `register_detector()`, `run_all()` | Pluggable detector framework. Detectors self-register on import. `run_all()` runs every registered detector, isolating failures. |
| [`fight.py`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/app/services/detectors/fight.py) | ~130 | `FightDetector` | Proximity + motion energy heuristic. IoU overlap + frame diff in union ROI. Persistence with streak tolerance. Camera-level cooldown. |
| [`fire.py`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/app/services/detectors/fire.py) | ~240 | `FireDetector` | Two-stage: optional YOLO fire model + structural HSV flame analysis. 8+ simultaneous gates. Core/periphery adjacency. Flicker analysis. Persistence with streak tolerance. |
| [`crash.py`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/app/services/detectors/crash.py) | ~250 | `CrashDetector` | Two crash signatures: sudden deceleration + contact-then-stop. Ego-motion guard for moving cameras. Fixed-camera only. |
| [`__init__.py`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/app/services/detectors/__init__.py) | ~5 | *(side effects)* | Imports fight, fire, crash to trigger registration. |

### Notifications (`backend/app/services/notify/`)

| File | Lines | Exports | Purpose |
|------|-------|---------|---------|
| [`dispatcher.py`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/app/services/notify/dispatcher.py) | 304 | `Channel` (ABC), `NotificationEvent`, `dispatch()`, `dispatch_and_wait()`, `register`, `get_channels()` | Notification fan-out. Channel registry. Severity gating. Async/blocking dispatch with timeout. Daemon thread management for blocking channels. |
| [`email.py`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/app/services/notify/email.py) | 281 | `EmailChannel` | HTML incident report email. CID-attached evidence JPEG. SMTP with TLS/SSL. Bounded wait for evidence file. |
| [`null.py`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/app/services/notify/null.py) | 25 | `NullChannel` | Log-only channel. Always enabled at `info` threshold. Reference implementation. |
| [`__init__.py`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/app/services/notify/__init__.py) | 19 | Re-exports from dispatcher | Registers null and email channels on import. |

### Data Files

| Path | Purpose |
|------|---------|
| `backend/data/settings.json` | Persisted runtime settings |
| `backend/data/blockchain/ledger.json` | Blockchain ledger |
| `backend/data/evidence/` | Captured evidence JPEGs (`evt_*.jpg`) |
| `backend/data/faces/` | Watchlist face images |
| `backend/data/sample_videos/` | Uploaded video files |
| `backend/data/reports/` | Generated PDF reports |
| `backend/demo_videos/` | Canned demo video clips |
| `backend/ibvap.db` | SQLite database (runtime) |

### Model Files

| Path | Size | Description |
|------|------|-------------|
| `backend/yolov8n.pt` | 6.5 MB | YOLOv8 Nano weights |
| `backend/yolov8s.pt` | 22.6 MB | YOLOv8 Small weights |
| `backend/bytetrack_custom.yaml` | 144 B | ByteTrack tracker config |

---

## Frontend — `frontend/`

### Root Config

| File | Purpose |
|------|---------|
| [`index.html`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/frontend/index.html) | HTML shell. Tailwind CDN with full theme config. Google Fonts. Material Symbols. |
| [`package.json`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/frontend/package.json) | Dependencies and scripts (dev, build, lint, preview). |
| [`vite.config.js`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/frontend/vite.config.js) | Vite config: React plugin, HTTPS, host binding, proxy rules. |

### Source Entry

| File | Lines | Purpose |
|------|-------|---------|
| [`main.jsx`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/frontend/src/main.jsx) | 40 | Entry point. Path-based split: `/phone` → PhoneCam (standalone), all else → `<App>` inside `<LanguageProvider>`. |
| [`App.jsx`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/frontend/src/App.jsx) | 167 | Main app shell. Camera polling (5s), alert WebSocket, page routing, KPI state. |
| [`index.css`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/frontend/src/index.css) | 89 | Tailwind imports, JetBrains Mono font, glitch animation, scrollbar, pipeline flow animation. |

### Services

| File | Lines | Purpose |
|------|-------|---------|
| [`api.js`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/frontend/src/services/api.js) | 272 | All API client functions, WebSocket creators, URL resolution. 30+ exported functions. |

### Context

| File | Lines | Purpose |
|------|-------|---------|
| [`LanguageContext.jsx`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/frontend/src/context/LanguageContext.jsx) | 59 | i18n context provider. English + Hindi translations. `useLanguage()` hook. |

### Pages

| File | Page | Key Features |
|------|------|-------------|
| `Dashboard.jsx` | Command Center | KPIs, threat meter, live feed grid, alert timeline |
| `CameraManagement.jsx` | Cameras | Camera cards, add/start/stop, tripwire, demo, phone QR |
| `AlertCenter.jsx` | Alerts | Event list with filters, status management, evidence |
| `AnalyticsDashboard.jsx` | Analytics | Recharts: timeline, severity pie, camera bar |
| `WatchlistManagement.jsx` | Watchlist | Face and plate CRUD with image upload |
| `MapView.jsx` | Map | React-Leaflet OSM, camera markers, event heatmap |
| `EvidenceVault.jsx` | Evidence | Evidence gallery, PDF download, blockchain status |
| `Settings.jsx` | Settings | Full settings editor grouped by category |
| `Landing.jsx` | Classic Landing | Text-based landing with use cases |
| `LandingV2.jsx` | 3D Landing | Three.js globe, pipeline animation, feature cards |
| `PhoneCam.jsx` | Phone Camera | getUserMedia → JPEG → WebSocket push |

### Components

| Directory | Components |
|-----------|------------|
| `Layout/` | `Sidebar.jsx`, `Header.jsx` |
| `Dashboard/` | `LiveFeedGrid.jsx`, `LiveFeedPanel.jsx`, `AlertTimeline.jsx`, `KPICards.jsx`, `ThreatMeter.jsx`, `QuickActions.jsx` |
| `CameraManagement/` | `AddCameraModal.jsx`, `CameraCard.jsx`, `CameraConfigModal.jsx`, `TripwireModal.jsx`, `DemoSection.jsx` |

---

## Evaluation Framework — `backend/eval/`

| File | Purpose |
|------|---------|
| `evaluate.py` | Test runner for detection features |
| `features.py` | Feature test definitions |
| `manifest.json` | Test manifest configuration |
| `manifest.py` | Manifest loader |
| `runner.py` | Test execution engine |
| `settings_source.py` | Settings for evaluation runs |

---

## Scripts — `scripts/`

| File | Purpose |
|------|---------|
| Various test scripts | Performance benchmarks, stream tests (moved from root during Phase 7 cleanup) |

---

## Documentation — `docs/`

| File | Purpose |
|------|---------|
| `README.md` | Complete project documentation (this docs suite) |
| `ARCHITECTURE.md` | System architecture with Mermaid diagrams |
| `AI_ML.md` | AI/ML models, detectors, algorithms |
| `BACKEND_API.md` | Backend structure and complete API reference |
| `FRONTEND.md` | Frontend architecture, design system, pages |
| `ALERT_PIPELINE.md` | Alert dispatch, notifications, threat score, blockchain |
| `CONFIGURATION.md` | All settings and configuration reference |
| `FILE_REFERENCE.md` | This file — complete file inventory |
| `ROADMAP.md` | Current project roadmap and future plans |
| `CUSTOM_MODEL.md` | Guide for integrating custom ML models |
