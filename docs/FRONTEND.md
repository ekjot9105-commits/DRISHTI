# DRISHTI — Frontend Documentation

## Overview

| Property | Value |
|----------|-------|
| **Framework** | React 19.2.8 |
| **Build Tool** | Vite 8.2.2 |
| **Styling** | Tailwind CSS (CDN), custom design system |
| **Routing** | None — state-based page switching via `setActivePage` |
| **Entry Point** | `frontend/src/main.jsx` |
| **HTML Shell** | `frontend/index.html` |
| **Dev Server** | HTTPS (self-signed cert via `@vitejs/plugin-basic-ssl`) |

---

## Directory Structure

```
frontend/
├── index.html                         # HTML shell with Tailwind CDN + theme config
├── package.json                       # Dependencies
├── vite.config.js                     # Vite config with HTTPS and proxy
├── public/
│   └── favicon.svg                    # Browser favicon
├── src/
│   ├── main.jsx                       # Entry point, path-based routing
│   ├── App.jsx                        # Main application shell
│   ├── index.css                      # Tailwind imports, glitch animation, scrollbar
│   ├── components/
│   │   ├── Layout/
│   │   │   ├── Sidebar.jsx            # Navigation sidebar
│   │   │   └── Header.jsx             # Top header bar
│   │   ├── Dashboard/
│   │   │   ├── LiveFeedGrid.jsx       # Camera grid with live WebSocket frames
│   │   │   ├── LiveFeedPanel.jsx      # Individual camera feed viewer
│   │   │   ├── AlertTimeline.jsx      # Alert feed display
│   │   │   ├── KPICards.jsx           # Active cameras, humans, vehicles counters
│   │   │   ├── ThreatMeter.jsx        # 0-100 threat gauge with decay
│   │   │   └── QuickActions.jsx       # Shortcut buttons
│   │   ├── CameraManagement/
│   │   │   ├── AddCameraModal.jsx     # Modal for adding cameras
│   │   │   ├── CameraCard.jsx         # Camera card with controls
│   │   │   ├── CameraConfigModal.jsx  # Configuration modal
│   │   │   ├── TripwireModal.jsx      # Tripwire drawing canvas
│   │   │   └── DemoSection.jsx        # Demo video launcher
│   │   └── common/                    # Shared UI components
│   ├── pages/
│   │   ├── Dashboard.jsx              # Command Center page
│   │   ├── CameraManagement.jsx       # Camera CRUD page
│   │   ├── AlertCenter.jsx            # Alert management page
│   │   ├── AnalyticsDashboard.jsx     # Charts and statistics
│   │   ├── WatchlistManagement.jsx    # Face and plate watchlist
│   │   ├── MapView.jsx                # Leaflet map with camera markers
│   │   ├── EvidenceVault.jsx          # Evidence gallery with PDF reports
│   │   ├── Settings.jsx               # Runtime settings editor
│   │   ├── Landing.jsx                # Classic landing page
│   │   ├── LandingV2.jsx              # 3D globe landing page
│   │   └── PhoneCam.jsx               # Phone camera page (public)
│   ├── context/
│   │   └── LanguageContext.jsx        # i18n context (English/Hindi)
│   └── services/
│       └── api.js                     # API client functions + WebSocket creators
```

---

## Design System

### Theme

The design system is defined inline in `index.html` via a Tailwind CDN configuration script. It implements a **dark, military/cyberpunk-themed** Material Design 3 colour palette:

| Token | Hex | Usage |
|-------|-----|-------|
| `background` / `surface` | `#0b1326` | Main background |
| `primary` | `#8aebff` | Accent — cyan |
| `primary-container` | `#22d3ee` | Active elements |
| `secondary` | `#ffc640` | Gold accent |
| `error` | `#ffb4ab` | Error states |
| `on-surface` | `#dae2fd` | Primary text |
| `on-surface-variant` | `#bbc9cd` | Secondary text |
| `surface-container` | `#171f33` | Cards, panels |
| `surface-container-high` | `#222a3d` | Elevated surfaces |
| `outline-variant` | `#3c494c` | Subtle borders |

### Typography

| Token | Font | Size | Weight | Use Case |
|-------|------|------|--------|----------|
| `data-display` | JetBrains Mono | 18px | 500 | Numbers, metrics, codes |
| `headline-lg` | Inter | 32px | 700 | Page titles |
| `headline-md` | Inter | 24px | 600 | Section headers |
| `headline-sm` | Inter | 20px | 600 | Card titles |
| `body-md` | Inter | 14px | 400 | Default body text |
| `body-lg` | Inter | 16px | 400 | Larger body text |
| `label-caps` | JetBrains Mono | 11px | 700 | Tags, badges (uppercase) |
| `label-md` | JetBrains Mono | 12px | 400 | Labels, captions |

### Animations
- **Glitch effect**: CSS pseudo-element glitch on titles (red/blue offset + clip-rect animation)
- **Pipeline flow**: CSS `@keyframes pipelineFlow` for landing page step connector
- **Scrollbar**: Custom thin scrollbar matching the dark theme
- Respects `prefers-reduced-motion` for animations

---

## Page-by-Page Detail

### Landing Page (LandingV2)
- **Route**: `/` or `/landing-v2`
- **Layout**: Standalone (no Sidebar/Header)
- **Features**: 3D interactive globe (`react-globe.gl` / Three.js), "How It Works" pipeline, feature cards
- **Navigation**: "Enter Command Center" button → sets `activePage='dashboard'`

### Classic Landing (Landing)
- **Route**: `/classic`
- **Layout**: Standalone
- **Features**: Text/image-based landing with use cases

### Command Center Dashboard
- **State**: `activePage='dashboard'`
- **Components**:
  - `KPICards` — Active cameras, humans detected, vehicles detected, alerts today (animated CountUp)
  - `ThreatMeter` — Polls `/api/system/threat` every 3s, displays dial with colour bands
  - `LiveFeedGrid` — Shows all active camera feeds via WebSocket
  - `LiveFeedPanel` — Single camera feed with bounding box overlay
  - `AlertTimeline` — Real-time scrolling alert feed from WebSocket
  - `QuickActions` — Add camera, view analytics, manage watchlist shortcuts
- **Data**: `cameras` and `alerts` state from App.jsx, polled every 5s

### Camera Management
- **State**: `activePage='cameras'`
- **Features**:
  - Camera card grid showing status, FPS, source type
  - Add Camera modal (file upload, RTSP URL, or phone QR code)
  - Start/Stop camera buttons
  - Configure button → opens CameraConfigModal
  - Tripwire drawing canvas → saves to `PATCH /api/cameras/{id}/tripwire`
  - Demo section: lists `demo_videos/` files, one-click launch
  - Phone QR: fetches LAN URL → renders QR code

### Alert Center
- **State**: `activePage='alerts'`
- **Features**:
  - Fetches from `GET /api/events/` with filters (severity, camera, status)
  - Status management: new → acknowledged → resolved → archived
  - Evidence frame preview
  - Download evidence JPEG
  - Blockchain verification status

### Analytics Dashboard
- **State**: `activePage='analytics'`
- **Features**:
  - Detection timeline chart (hourly, last 24h) via Recharts
  - Severity breakdown pie chart
  - Camera activity bar chart
  - Data from `GET /api/events/stats`

### Watchlist Management
- **State**: `activePage='watchlist'`
- **Features**:
  - Faces tab: Add face (name, description, image upload, authorized flag) / Delete
  - Plates tab: Add plate (number, vehicle desc, owner) / Delete
  - Image preview for uploaded faces
  - Authorized face flag for suppressing alerts

### Geospatial Map View
- **State**: `activePage='map'`
- **Library**: React-Leaflet with OpenStreetMap tiles
- **Features**:
  - Camera markers at configured lat/lng
  - Event heatmap overlay from `GET /api/events/heatmap`
  - Fallback demo coordinates (Delhi) if camera has no configured position

### Evidence Vault
- **State**: `activePage='evidence'`
- **Features**:
  - Gallery of evidence JPEGs (loaded from `/evidence/evt_*.jpg`)
  - Filter by severity, camera, date
  - Download evidence JPEG
  - Generate PDF incident report → `GET /api/reports/{id}/download`
  - Blockchain verification badge

### Settings
- **State**: `activePage='settings'`
- **Features**:
  - Read/write all runtime settings via `GET/PATCH /api/settings/`
  - Grouped by section: detection thresholds, behavioral rules, fight/fire/crash toggles, notification config, threat score tuning
  - Real-time apply (no restart needed — settings are read from `settings.json` on each inference frame)

### Phone Camera (Public)
- **Route**: `/phone`
- **Layout**: Standalone (outside `<App>`, no sidebar/header/polling)
- **Features**:
  - Captures rear camera via `getUserMedia`
  - Encodes JPEG at 12 FPS, quality 0.6
  - Pushes binary frames via WebSocket to `/ws/cameras/{id}/push`
  - Back-pressure: drops frames if `ws.bufferedAmount > 512 KB`
  - Displays frame counter and connection status
  - Self-signed cert warning explanation

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `react` | ^19.2.8 | UI framework |
| `react-dom` | ^19.2.8 | React DOM renderer |
| `framer-motion` | ^13.2.0 | Animations and transitions |
| `leaflet` | ^1.9.4 | Map rendering |
| `react-leaflet` | ^5.0.0 | React bindings for Leaflet |
| `lucide-react` | ^1.35.0 | Icon library |
| `react-countup` | ^6.5.3 | Animated number counters |
| `react-globe.gl` | ^2.38.0 | 3D globe visualization |
| `recharts` | ^3.10.1 | Charts and graphs |
| `three` | ^0.185.1 | 3D rendering (globe) |
| `@vitejs/plugin-basic-ssl` | ^2.3.0 | HTTPS dev server |
| `@vitejs/plugin-react` | ^6.1.0 | React Fast Refresh |
| `oxlint` | ^1.79.0 | Linter |
| `vite` | ^8.2.2 | Build tool / dev server |

---

## API Client

File: [`frontend/src/services/api.js`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/frontend/src/services/api.js)

### URL Resolution
- `API_BASE` defaults to empty string (same-origin) — all requests go through the Vite proxy
- `WS_BASE` resolves `ws://` or `wss://` based on page protocol
- `VITE_API_HOST` env var overrides for production deployments

### Functions Exported

| Function | Endpoint | Method |
|----------|----------|--------|
| `fetchCameras()` | `/api/cameras/` | GET |
| `addCamera(formData)` | `/api/cameras/` | POST |
| `startCamera(id)` | `/api/cameras/{id}/start` | POST |
| `stopCamera(id)` | `/api/cameras/{id}/stop` | POST |
| `deleteCamera(id)` | `/api/cameras/{id}` | DELETE |
| `fetchStreamStatus()` | `/api/cameras/streams/status` | GET |
| `fetchHealth()` | `/api/health` | GET |
| `fetchThreat()` | `/api/system/threat` | GET |
| `fetchSettings()` | `/api/settings/` | GET |
| `updateSettings(patch)` | `/api/settings/` | PATCH |
| `fetchDemoVideos()` | `/api/cameras/demo/list` | GET |
| `launchDemoVideo(filename)` | `/api/cameras/demo/{filename}/launch` | POST |
| `registerPhoneCamera(name, location)` | `/api/cameras/phone/register` | POST |
| `fetchLanUrl(path, port)` | `/api/system/lan-url` | GET |
| `qrImageUrl(data)` | `/api/system/qr` | GET (URL) |
| `createPushWebSocket(id)` | `/ws/cameras/{id}/push` | WS |
| `createCameraWebSocket(id, onMsg, onErr)` | `/ws/camera/{id}` | WS |
| `createAlertWebSocket(onAlert)` | `/ws/alerts` | WS |
| `getFaces()` | `/api/watchlist/faces` | GET |
| `addFace(name, desc, file, auth)` | `/api/watchlist/faces` | POST |
| `deleteFace(id)` | `/api/watchlist/faces/{id}` | DELETE |
| `getPlates()` | `/api/watchlist/plates` | GET |
| `addPlate(num, desc, owner)` | `/api/watchlist/plates` | POST |
| `deletePlate(id)` | `/api/watchlist/plates/{id}` | DELETE |
| `getEvents(skip, limit, cam, sev, status)` | `/api/events/` | GET |
| `updateEventStatus(id, status)` | `/api/events/{id}/status` | PATCH |
| `getEventStats()` | `/api/events/stats` | GET |
| `getEventHeatmap()` | `/api/events/heatmap` | GET |
| `getBlockchainStatus(eventId)` | `/api/events/{id}/blockchain` | GET |

---

## Internationalization

File: [`frontend/src/context/LanguageContext.jsx`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/frontend/src/context/LanguageContext.jsx)

**Languages**: English (`en`), Hindi (`hi`)

Translation keys cover navigation labels and KPI card titles. The `useLanguage()` hook provides `{language, setLanguage, t}` where `t(key)` returns the translated string.

**Coverage**: Partial — only core navigation and KPI labels are translated. Page content, alerts, and settings remain English-only.

---

## Build & Development

### Development
```bash
cd frontend
npm install
npm run dev
```
- Runs on `https://localhost:5173` (self-signed HTTPS)
- Bound to `0.0.0.0` (`host: true`) for LAN access
- Proxies `/api`, `/ws`, `/evidence`, `/data` → `http://localhost:8000`

### Production Build
```bash
npm run build      # Outputs to dist/
npm run preview    # Serves the built bundle locally
```

### Linting
```bash
npm run lint       # Runs oxlint
```
