# DRISHTI — AI/ML Documentation

## Overview

DRISHTI's AI pipeline is built around two layers:

1. **Primary Detection & Tracking** — YOLOv8 with ByteTrack for person and vehicle detection, producing tracked bounding boxes every frame.
2. **Pluggable Anomaly Detectors** — A registry-based framework where independent detectors (fight, fire, crash) receive the same per-frame context and emit alerts without coupling to each other.

Both layers run in a dedicated inference thread per camera, separate from the frame capture thread.

---

## Model 1: YOLOv8 Object Detection + ByteTrack Tracking

### Model Details

| Property | Value |
|----------|-------|
| **Model** | YOLOv8 (nano or small variant) |
| **Framework** | Ultralytics (`ultralytics` Python package) |
| **Formats supported** | `.pt` (PyTorch), `.onnx` (ONNX Runtime) |
| **Model files present** | `backend/yolov8n.pt` (6.5 MB), `backend/yolov8s.pt` (22.6 MB) |
| **Loading priority** | `yolov8n.onnx` → `yolov8s.onnx` → `yolov8s.pt` → download |
| **Inference device** | CPU (`device='cpu'`) |
| **Tracker** | ByteTrack (`bytetrack_custom.yaml`) |
| **Target classes** | COCO: 0=person, 2=car, 3=motorcycle, 5=bus, 7=truck |
| **Mapped labels** | `person`, `vehicle` (all vehicle classes unified) |

### ByteTrack Configuration

File: [`backend/bytetrack_custom.yaml`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/bytetrack_custom.yaml)

```yaml
tracker_type: bytetrack
track_high_thresh: 0.5
track_low_thresh: 0.1
new_track_thresh: 0.6
track_buffer: 150       # frames a lost track is remembered
match_thresh: 0.8
fuse_score: True
```

### Inference Pipeline

1. **Night mode** (optional): CLAHE contrast enhancement on LAB lightness channel
2. **YOLO `model.track()`**: `persist=True`, `iou=0.6`, classes filtered to target set
3. **Confidence filtering**: detections below `confidence_threshold` (default 0.35) are discarded
4. **Track IDs**: ByteTrack assigns persistent integer IDs; untracked detections fallback to `"?"`
5. **Ghost boxes**: Tracks that disappear for <2 seconds get their last known box replayed (flagged `ghost: True`) to prevent flicker

### Output

For each frame, `ml_service.process_frame()` returns:
- `alerts: List[dict]` — any triggered events
- `drawn_boxes: List[dict]` — `{id, class, conf, box, identity, ghost}`

---

## Model 2: Fire & Smoke Detection

### Architecture

File: [`backend/app/services/detectors/fire.py`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/app/services/detectors/fire.py)

**Two-stage detection** (runs every frame regardless of YOLO detections):

#### Stage 1: Optional YOLO Fire/Smoke Model
- Looks for weight files: `fire.pt`, `fire_smoke.pt`, `fire.onnx`, or `$FIRE_MODEL` env var
- If found, its bounding boxes drive candidate regions
- **Currently**: No fire/smoke weights are present in the repository; this stage is inactive

#### Stage 2: Structural HSV Analysis (Active)
The default detection method uses colour analysis with multiple structural gates:

| Gate | Setting Key | Default | Description |
|------|-------------|---------|-------------|
| Area ratio | `fire_area_ratio` | 0.004 | Min fraction of frame for a candidate region |
| Min region px | `fire_min_region_px` | 250 | Ignore specks smaller than this |
| Core fraction min | `fire_core_frac_min` | 0.01 | Must have some bright core |
| Core fraction max | `fire_core_frac_max` | 0.95 | Must not be all core (sky/glare) |
| Adjacency min | `fire_adjacency_min` | 0.15 | Core must physically touch orange surround |
| Saturation std min | `fire_sat_std_min` | 48.0 | Fire is a gradient; uniform → reject |
| Hue std min | `fire_hue_std_min` | 1.5 | Hue must vary (flame shifts, panels don't) |
| Flicker min | `fire_flicker` | 6.0 | Mean frame-diff inside the region |

**All gates must pass simultaneously.** No single gate separates fire from daylight scenes.

#### Flame Colour Bands (OpenCV HSV)
- **Core**: H[0–35], S[0–90], V[220–255] — blown-out yellow-white centre
- **Periphery**: H[0–35], S[90–255], V[120–255] — saturated red-orange
- **Smoke**: H[0–180], S[0–45], V[80–210] — desaturated grey (opt-in, `smoke_enabled=False`)

#### Persistence
The fire signature must hold for `fire_duration` (default 1.5s) with:
- `fire_streak_tolerance` = 3 consecutive sub-threshold frames forgiven
- `fire_min_hit_ratio` = 0.6 (60% of frames in window must be hits)
- `fire_max_gap` = 0.5s max wall-clock silence between hits
- `fire_cooldown` = 60s between alerts per camera

### Output
- **Fire**: severity `critical`, level `CRITICAL`, icon 🔥
- **Smoke**: severity `high`, level `PRIORITY ALPHA`, icon 💨

---

## Model 3: Fight Detection

File: [`backend/app/services/detectors/fight.py`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/app/services/detectors/fight.py)

### Architecture
**Pure heuristic — no extra model weights.** Uses three signals:

1. **Proximity**: Two tracked persons' boxes overlap (IoU ≥ `fight_iou`, default 0.05)
2. **Motion energy**: Mean absolute frame-difference inside the pair's union ROI
3. **Persistence**: Both conditions held for `fight_duration` (default 0.3s)

### Algorithm
```
For every pair of tracked persons:
  1. Compute IoU of their bounding boxes
  2. If IoU >= threshold:
     - Compute union ROI (clamped to frame)
     - Calculate mean |frame_diff| inside union ROI
  3. hit = (IoU >= threshold) AND (energy >= fight_motion_energy)
  4. Advance persistence streak:
     - Tolerance: 2 consecutive misses forgiven
     - Min hit ratio: 60% of frames must be actual hits
     - Max gap: 0.5s wall-clock between hits
  5. If streak held for fight_duration:
     - Check camera-level cooldown (20s, NOT per-pair — track ID churn during scuffles)
     - Emit CRITICAL alert with frame evidence
```

### Key Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `fight_enabled` | true | Master toggle |
| `fight_iou` | 0.05 | Min box overlap |
| `fight_motion_energy` | 30.0 | Mean frame-diff threshold |
| `fight_duration` | 0.3s | Persistence window |
| `fight_streak_tolerance` | 2 | Consecutive misses forgiven |
| `fight_min_hit_ratio` | 0.60 | Min hit fraction |
| `fight_max_gap` | 0.5s | Wall-clock gap limit |
| `fight_cooldown` | 20.0s | Per-camera alert cooldown |

---

## Model 4: Vehicle Crash Detection

File: [`backend/app/services/detectors/crash.py`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/app/services/detectors/crash.py)

### Scope
**Fixed cameras only.** Dashcam/moving-camera feeds are deliberately suppressed via an ego-motion guard.

### Two Signatures

#### Signature 1: Sudden Deceleration
A tracked vehicle that was genuinely moving loses most of its speed within a fraction of a second:
- `prior_speed` averaged over `crash_prior_window` (0.8s)
- `recent_speed` averaged over `crash_recent_window` (0.5s)
- Crash = `recent < prior * crash_decel_ratio` (0.25) AND `prior >= crash_min_speed` (0.45)
- Speeds in box-diagonals/second (camera-distance invariant)

#### Signature 2: Contact Then Stop
Two vehicle boxes' overlap jumps from separate to touching, then both vehicles stop:
- Overlap must rise from < `crash_iou_prior` (0.08) to ≥ `crash_iou_spike` (0.25) within `crash_iou_lookback` (0.6s)
- Both vehicles must then be stationary (`max(speed_a, speed_b) <= max(crash_stopped_speed, crash_stopped_ratio * peak_speed)`)
- Contact latched and confirmed within `crash_contact_window` (4.0s)

#### Ego-Motion Guard
If ≥50% of tracked vehicles decelerate simultaneously (3+ vehicles), it's camera motion, not a crash. All deceleration streaks are suppressed.

### Known Limitation (documented in code)
The dashcam crash demo clip (`backend/demo_videos/car_crash.mp4`) is NOT detected because:
- Motion blur wipes out detections at impact
- ByteTrack loses identity through collision
- Post-collision IoU peaks at 0.159 while normal traffic reaches 0.100

---

## Model 5: Face Recognition

File: [`backend/app/services/recognition.py`](file:///c:/Users/Ekjot%20singh/Desktop/SIH_2026/backend/app/services/recognition.py)

| Property | Value |
|----------|-------|
| **Library** | DeepFace |
| **Model** | VGG-Face |
| **Detector** | RetinaFace |
| **Confirmation** | 3 consecutive frame matches required |
| **Threading** | ThreadPoolExecutor (2 workers), non-blocking |

### Pipeline
1. YOLO detects a `person` with a valid track ID
2. Frame crop (>30×30 px) is dispatched to `recognition_service.async_recognize()`
3. Background thread saves temp JPEG → calls `DeepFace.find()` against `data/faces/` directory
4. If match found: increment observation counter for `(camera_id, track_id, match_path)`
5. After 3 observations: confirmed match
   - If authorized: suppress dwelling/intrusion alerts for this track
   - If unauthorized: trigger `watchlist_match` CRITICAL alert

---

## Model 6: License Plate Recognition (ALPR)

| Property | Value |
|----------|-------|
| **Library** | EasyOCR |
| **Languages** | English (`['en']`) |
| **Mode** | CPU, quantized |
| **Confirmation** | 2 identical reads (consensus) |

### Pipeline
1. YOLO detects a `vehicle` with a valid track ID
2. Frame crop dispatched to `recognition_service._recognize_plate()`
3. EasyOCR `readtext()` on crop → extract alphanumeric text > 4 chars
4. Collect hits in `alpr_hits[camera_id_track_id]`
5. After 2 identical reads: query `WatchlistPlate` table for match
6. Match → trigger `watchlist_match` CRITICAL alert

---

## Anomaly Detection Capabilities Summary

### ML-Model-Based
| Capability | Model | Type |
|------------|-------|------|
| Person detection | YOLOv8 (COCO) | Verified |
| Vehicle detection | YOLOv8 (COCO) | Verified |
| Object tracking | ByteTrack | Verified |
| Face recognition | DeepFace VGG-Face | Verified |
| Plate recognition | EasyOCR | Verified |
| Fire detection (model) | Optional YOLO fire weights | NOT present |

### Heuristic / Rule-Based
| Capability | Method | Status |
|------------|--------|--------|
| Tripwire intrusion | Line segment intersection | Implemented |
| Prolonged dwelling | Track duration > threshold | Implemented |
| Fleeing/running | Velocity > threshold over duration | Implemented |
| Crowd gathering | Centroid density clustering | Implemented |
| Fight detection | IoU + motion energy + persistence | Implemented |
| Fire detection (HSV) | Structural flame analysis | Implemented |
| Smoke detection (HSV) | Colour-only heuristic | Implemented (opt-in, off by default) |
| Vehicle crash (decel) | Speed ratio analysis | Implemented |
| Vehicle crash (contact) | IoU jump + stop | Implemented |

### NOT Implemented (despite being common in surveillance)
- Weapon detection
- Drone detection
- Facial expression analysis
- Predictive analytics
- Audio analysis
- Abandoned object detection
