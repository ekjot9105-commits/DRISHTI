# DRISHTI — AI Safety Monitoring Platform

**Real-time AI-powered surveillance and anomaly detection for any CCTV infrastructure.**

DRISHTI is an AI safety monitoring platform that transforms existing CCTV cameras into active early-warning systems. Rather than passive footage reviewed after incidents, DRISHTI watches live video feeds and raises alarms as events happen — fights breaking out, fires starting, perimeter intrusions, suspicious loitering, crowd buildup, and vehicle crashes. It runs on commodity hardware (CPU-only) with no proprietary cameras required.

Originally developed as a border surveillance system for SIH, DRISHTI has been redesigned for the Manipal Hackathon into a general-purpose AI surveillance and anomaly detection platform suitable for schools, retail, hospitals, public infrastructure, and industrial facilities.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Fight Detection** | Heuristic detector using proximity (IoU overlap) + motion energy (frame differencing) with persistence. No extra model weights. |
| **Fire & Smoke Detection** | Two-stage: optional YOLO fire/smoke weights, plus structural HSV flame analysis with core/periphery adjacency, flicker, and saturation variance gates. |
| **Vehicle Crash Detection** | Fixed-camera heuristic: sudden deceleration and contact-then-stop signatures with ego-motion guard for moving cameras. |
| **Virtual Tripwires** | Draw multiple perimeter lines per camera. Line-crossing triggers critical alerts with geometric intersection math. |
| **Watchlist & Face Recognition** | DeepFace/VGG-Face with RetinaFace backend. Multi-frame confirmation (3+ observations) before alerting. |
| **ALPR (License Plate)** | EasyOCR with consensus (2+ identical reads) before watchlist matching. |
| **Behavioral Analytics** | Prolonged dwelling detection, fleeing/running subject detection, crowd gathering via density-based clustering. |
| **Phone-as-Camera** | Scan a QR code on any phone to turn it into a live CCTV feed via WebSocket frame push. |
| **Evidence Vault** | Automatic evidence frame capture with SHA-256 hashing and blockchain ledger for chain-of-custody. |
| **PDF Incident Reports** | Professional incident reports with metadata, evidence snapshot, QR code, and blockchain verification. |
| **Email Notifications** | HTML incident reports with embedded evidence frames sent via SMTP for critical events. |
| **Threat Score** | Rolling 0–100 threat meter with exponential decay, severity bands, and per-camera breakdown. |
| **Night Mode** | CLAHE contrast enhancement on the lightness channel for low-light feeds. |
| **Multi-language** | English and Hindi UI translations via React context. |

---

## Architecture

```
Frontend (React/Vite)
    ↓ REST API + WebSocket
Backend (FastAPI/Python)
    ├── Video Ingestion (OpenCV threads)
    │     ├── File / RTSP / Phone push
    │     └── Frame capture → resize → render
    ├── ML Inference (dedicated thread per camera)
    │     ├── YOLOv8 + ByteTrack (detection & tracking)
    │     ├── Tripwire intersection logic
    │     ├── Behavioral analytics (dwelling, fleeing, crowds)
    │     └── Pluggable detectors (fight, fire, crash)
    ├── Recognition (background thread pool)
    │     ├── DeepFace (face recognition)
    │     └── EasyOCR (plate recognition)
    ├── Alert Dispatcher (async loop)
    │     ├── Database persistence (SQLite/SQLAlchemy)
    │     ├── Evidence capture + blockchain hashing
    │     ├── WebSocket broadcast
    │     ├── Webhook dispatch
    │     ├── Threat score update
    │     └── Notification fan-out (email, null/log)
    └── System Monitor (psutil background thread)
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 19, Vite 8, Tailwind CSS (CDN), Recharts, React-Leaflet, Three.js/react-globe.gl, Framer Motion, Lucide icons |
| Backend | Python, FastAPI 0.115, Uvicorn, SQLAlchemy 2.0, SQLite |
| AI/ML | Ultralytics YOLOv8 (nano/small), ByteTrack, OpenCV, DeepFace (VGG-Face + RetinaFace), EasyOCR |
| Real-time | WebSockets (native FastAPI), asyncio |
| Reports | ReportLab (PDF), qrcode |
| Notifications | smtplib (email), httpx (webhooks) |

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
pip install reportlab psutil httpx
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open **https://localhost:5173** (self-signed cert for phone camera access).

---

## Environment Variables

Copy `.env.example` to `.env` in the project root or `backend/` directory:

| Variable | Default | Purpose |
|----------|---------|---------|
| `API_HOST` | `0.0.0.0` | Backend bind address |
| `API_PORT` | `8000` | Backend port |
| `DEFAULT_FPS` | `15` | Target frame rate for video processing |
| `FRAME_WIDTH` | `640` | Frame width for processing |
| `FRAME_HEIGHT` | `480` | Frame height for processing |
| `JPEG_QUALITY` | `70` | JPEG encoding quality (0–100) |
| `FRONTEND_URL` | `http://localhost:5173` | CORS origin |
| `LOG_LEVEL` | `INFO` | Logging level |
| `SMTP_HOST` | *(empty)* | SMTP server for email alerts |
| `SMTP_PORT` | `587` | SMTP port |
| `SMTP_USER` | *(empty)* | SMTP username |
| `SMTP_PASSWORD` | *(empty)* | SMTP password (App Password for Gmail) |
| `SMTP_FROM` | *(SMTP_USER)* | Display sender address |
| `SMTP_TO` | *(empty)* | Comma-separated recipient list |
| `FIRE_MODEL` | *(empty)* | Path to custom fire/smoke YOLO weights |

---

## API Overview

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/cameras/` | List all cameras with stream status |
| POST | `/api/cameras/` | Add camera (file upload, RTSP, or phone) |
| POST | `/api/cameras/{id}/start` | Start camera stream |
| POST | `/api/cameras/{id}/stop` | Stop camera stream |
| DELETE | `/api/cameras/{id}` | Delete camera |
| PATCH | `/api/cameras/{id}/tripwire` | Set tripwire coordinates |
| GET | `/api/cameras/demo/list` | List demo video files |
| POST | `/api/cameras/demo/{filename}/launch` | Launch demo video as camera |
| POST | `/api/cameras/phone/register` | Register phone camera |
| GET | `/api/events/` | Query events (paginated, filterable) |
| PATCH | `/api/events/{id}/status` | Update event status |
| GET | `/api/events/stats` | Event statistics (timeline, severity, camera) |
| GET | `/api/events/heatmap` | Heatmap data for geospatial view |
| GET | `/api/events/{id}/evidence/download` | Download evidence JPEG |
| GET | `/api/events/{id}/blockchain` | Blockchain verification status |
| GET | `/api/reports/{id}/download` | Generate and download PDF report |
| GET/PATCH | `/api/settings/` | Read/update runtime settings |
| GET | `/api/system/status` | System resource stats |
| GET | `/api/system/threat` | Rolling threat score |
| GET | `/api/system/lan-url` | LAN URL for phone joining |
| GET | `/api/system/qr` | Generate QR code PNG |
| GET | `/api/watchlist/faces` | List watchlist faces |
| POST | `/api/watchlist/faces` | Add face to watchlist |
| DELETE | `/api/watchlist/faces/{id}` | Remove face |
| GET | `/api/watchlist/plates` | List watchlist plates |
| POST | `/api/watchlist/plates` | Add plate to watchlist |
| DELETE | `/api/watchlist/plates/{id}` | Remove plate |
| WS | `/ws/camera/{id}` | Live JPEG frame stream |
| WS | `/ws/alerts` | Real-time alert notifications |
| WS | `/ws/cameras/{id}/push` | Receive pushed frames (phone camera) |
| GET | `/api/health` | Health check |

---

## Demonstration Workflow

1. Open DRISHTI Command Center at `https://localhost:5173`
2. Add a camera (upload video, enter RTSP URL, or scan QR for phone)
3. Start the camera — observe real-time bounding boxes on persons and vehicles
4. Draw tripwire lines → wait for crossing → Critical Alert
5. Add a face to the watchlist → system confirms identity across 3 frames
6. Open Evidence Vault → download PDF incident report with SHA-256 hash
7. Monitor the Threat Meter for rolling situational awareness

---

## Known Limitations

- PTZ cameras invalidate tripwire coordinates (designed for fixed cameras)
- Vehicle crash detection works on fixed cameras only; dashcam footage is deliberately suppressed
- Face recognition and ALPR are computationally heavy on CPU; recommended GPU for >4 simultaneous streams
- No authentication/authorization implemented (designed for trusted LAN/control room)
- Base YOLO model detects persons and vehicles only; custom weights needed for weapons, drones, etc.
- Smoke heuristic disabled by default (high false positive rate on roads/sky)
- Single-server architecture with no horizontal scaling

---

## License

This project was developed for the Manipal Hackathon. Licensing terms are not specified in the repository.
