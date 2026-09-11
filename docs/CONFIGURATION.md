# DRISHTI — Configuration & Settings Reference

## Overview

DRISHTI uses three layers of configuration:

1. **Environment variables** (`.env` file) — server and infrastructure settings
2. **`data/settings.json`** — runtime ML/detection tuning (modifiable via Settings UI)
3. **`bytetrack_custom.yaml`** — tracker parameters

---

## Environment Variables

File: [`.env.example`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/.env.example)

Loaded by `python-dotenv` on startup. Sources: `backend/.env` first, then project root `.env`.

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./ibvap.db` | SQLAlchemy database URL |
| `HOST` | `0.0.0.0` | Uvicorn bind address |
| `PORT` | `8000` | Uvicorn port |
| `WEBHOOK_URL` | *(empty)* | Webhook endpoint for alerts (can also set in UI) |
| `USE_GPU` | `false` | Enable CUDA if available |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `FRONTEND_URL` | `http://localhost:5173` | Allowed CORS origin |
| `FIRE_MODEL` | *(empty)* | Path to custom fire YOLO weights |
| `SMTP_HOST` | *(empty)* | SMTP server hostname |
| `SMTP_PORT` | `587` | SMTP server port |
| `SMTP_USER` | *(empty)* | SMTP login username |
| `SMTP_PASSWORD` | *(empty)* | SMTP login password |
| `SMTP_FROM` | *(SMTP_USER)* | Display sender address |
| `SMTP_TO` | *(empty)* | Comma-separated recipient list |
| `SMTP_USE_TLS` | `true` | STARTTLS on port 587 |
| `SMTP_USE_SSL` | `false` | Implicit TLS on port 465 |

---

## Runtime Settings (`settings.json`)

File: [`backend/data/settings.json`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/data/settings.json)

Managed by: [`backend/app/core/settings_manager.py`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/app/core/settings_manager.py)

These settings are read on every inference frame and can be changed at runtime via the Settings UI (`PATCH /api/settings/`). No restart required.

### Detection Core

| Key | Default | Type | Description |
|-----|---------|------|-------------|
| `confidence_threshold` | `0.35` | float | Min YOLO confidence to accept a detection |
| `night_mode` | `true` | bool | Enable CLAHE contrast enhancement for dark feeds |

### Tripwire / Intrusion

| Key | Default | Type | Description |
|-----|---------|------|-------------|
| `intrusion_cooldown` | `1` | int (seconds) | Per-track cooldown between intrusion alerts |

### Behavioral Analytics

| Key | Default | Type | Description |
|-----|---------|------|-------------|
| `dwelling_time` | `20` | int (seconds) | Time before a stationary person triggers dwelling alert |
| `fleeing_threshold` | `300.0` | float (px/s) | Speed threshold for fleeing subject detection |
| `fleeing_duration` | `1.5` | float (seconds) | Min duration of sustained speed to confirm fleeing |
| `crowd_count` | `3` | int | Min persons in proximity to flag a crowd |
| `crowd_density` | `150.0` | float (pixels) | Max centroid distance for clustering |
| `crowd_duration` | `60.0` | float (seconds) | Cooldown between crowd alerts |

### Fight Detection

| Key | Default | Type | Description |
|-----|---------|------|-------------|
| `fight_enabled` | `true` | bool | Master toggle |
| `fight_iou` | `0.05` | float | Min bounding box overlap (IoU) |
| `fight_motion_energy` | `30.0` | float | Mean frame-diff threshold in union ROI |
| `fight_duration` | `0.3` | float (seconds) | Required persistence duration |
| `fight_cooldown` | `20.0` | float (seconds) | Per-camera cooldown |
| `fight_streak_tolerance` | `2` | int | Consecutive misses forgiven in persistence |
| `fight_min_hit_ratio` | `0.6` | float | Min fraction of hits in persistence window |
| `fight_max_gap` | `0.5` | float (seconds) | Max wall-clock gap between hits |

### Fire & Smoke Detection

| Key | Default | Type | Description |
|-----|---------|------|-------------|
| `fire_enabled` | `true` | bool | Master toggle |
| `fire_area_ratio` | `0.004` | float | Min fraction of frame covered |
| `fire_min_region_px` | `250` | int | Min region size in pixels |
| `fire_core_frac_min` | `0.01` | float | Min fraction of region that is bright core |
| `fire_core_frac_max` | `0.95` | float | Max fraction (prevents sky/glare) |
| `fire_adjacency_min` | `0.15` | float | Min contact between core and periphery |
| `fire_sat_std_min` | `48.0` | float | Min saturation standard deviation |
| `fire_hue_std_min` | `1.5` | float | Min hue standard deviation |
| `fire_flicker` | `6.0` | float | Min mean frame-diff in region |
| `fire_duration` | `1.5` | float (seconds) | Required persistence duration |
| `fire_streak_tolerance` | `3` | int | Consecutive misses forgiven |
| `fire_min_hit_ratio` | `0.6` | float | Min fraction of hits |
| `fire_max_gap` | `0.5` | float (seconds) | Max wall-clock gap |
| `fire_cooldown` | `60.0` | float (seconds) | Per-camera cooldown |
| `smoke_enabled` | `false` | bool | Toggle smoke heuristic (off by default) |
| `smoke_area_ratio` | `0.15` | float | Min frame coverage for smoke |

### Crash Detection

| Key | Default | Type | Description |
|-----|---------|------|-------------|
| `crash_enabled` | `true` | bool | Master toggle |
| `crash_min_speed` | `0.45` | float | Min prior speed (box-diags/s) |
| `crash_decel_ratio` | `0.25` | float | Recent/prior speed ratio threshold |
| `crash_recent_window` | `0.5` | float (seconds) | Recent speed averaging window |
| `crash_prior_window` | `0.8` | float (seconds) | Prior speed averaging window |
| `crash_iou_spike` | `0.25` | float | IoU threshold for contact |
| `crash_iou_prior` | `0.08` | float | IoU baseline (separate vehicles) |
| `crash_pair_min_speed` | `0.3` | float | Min pair speed for contact signature |
| `crash_iou_lookback` | `0.6` | float (seconds) | IoU history window |
| `crash_contact_window` | `4.0` | float (seconds) | Time to confirm stop after contact |
| `crash_stopped_ratio` | `0.3` | float | Stopped = speed < peak × ratio |
| `crash_stopped_speed` | `0.1` | float | Absolute stopped speed floor |
| `crash_duration` | `0.7` | float (seconds) | Required persistence |
| `crash_cooldown` | `30.0` | float (seconds) | Per-camera cooldown |

### Notification System

| Key | Default | Type | Description |
|-----|---------|------|-------------|
| `notify_enabled` | `true` | bool | Master switch for all notifications |
| `notify_timeout` | `10.0` | float (seconds) | Per-channel timeout |
| `notify_max_blocking_threads` | `16` | int | Max zombie blocking threads |
| `notify_null_enabled` | `true` | bool | Toggle log channel |
| `notify_null_min_severity` | `"info"` | string | Min severity for log channel |
| `notify_email_enabled` | `true` | bool | Toggle email channel |
| `notify_email_min_severity` | `"critical"` | string | Min severity for email |
| `notify_email_evidence_wait` | `3.0` | float (seconds) | Wait for evidence JPEG |
| `notify_email_smtp_timeout` | `20.0` | float (seconds) | SMTP socket timeout |

### UI / Alert

| Key | Default | Type | Description |
|-----|---------|------|-------------|
| `alarm_muted` | `false` | bool | Mute UI alarm sounds |
| `alarm_cooldown` | `3.0` | float (seconds) | Min time between alarm sounds |
| `browser_push_enabled` | `true` | bool | Enable browser push notifications |
| `webhook_url` | `""` | string | External webhook endpoint |

### Threat Score

| Key | Default | Type | Description |
|-----|---------|------|-------------|
| `threat_half_life` | `120.0` | float (seconds) | Decay half-life for threat score |

---

## ByteTrack Configuration

File: [`backend/bytetrack_custom.yaml`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/bytetrack_custom.yaml)

| Key | Value | Description |
|-----|-------|-------------|
| `tracker_type` | `bytetrack` | Tracker algorithm |
| `track_high_thresh` | `0.5` | High confidence threshold for first association |
| `track_low_thresh` | `0.1` | Low confidence threshold for second association |
| `new_track_thresh` | `0.6` | Min confidence to initialize a new track |
| `track_buffer` | `150` | Frames before a lost track is deleted |
| `match_thresh` | `0.8` | IoU threshold for matching detections to tracks |
| `fuse_score` | `True` | Fuse detection score with IoU for association |

---

## Config Constants (Hardcoded)

These are defined in [`backend/app/core/config.py`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/app/core/config.py) and are not user-modifiable:

| Constant | Value | Description |
|----------|-------|-------------|
| `DEFAULT_FPS` | 15 | Target FPS for video processing |
| `FRAME_WIDTH` | 640 | Frame resize width |
| `FRAME_HEIGHT` | 480 | Frame resize height |
| `JPEG_QUALITY` | 70 | JPEG encoding quality |
| `BASE_DIR` | `backend/` | Backend root directory |
| `DATA_DIR` | `data/` | Data directory |
| `EVIDENCE_DIR` | `data/evidence/` | Evidence storage |
| `FACES_DIR` | `data/faces/` | Watchlist face images |
| `SAMPLE_VIDEOS_DIR` | `data/sample_videos/` | Uploaded video storage |
| `DEMO_VIDEOS_DIR` | `demo_videos/` | Canned demo clips |

---

## Frontend Configuration

File: [`frontend/vite.config.js`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/frontend/vite.config.js)

| Setting | Value | Description |
|---------|-------|-------------|
| Backend target | `http://localhost:8000` | Proxy target |
| HTTPS | Enabled via `@vitejs/plugin-basic-ssl` | Self-signed cert |
| Host | `true` (0.0.0.0) | LAN accessible |
| Proxy paths | `/api`, `/ws`, `/evidence`, `/data` | Forwarded to backend |

### Frontend Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_HOST` | *(empty)* | Override API host (for non-Vite deployments) |
