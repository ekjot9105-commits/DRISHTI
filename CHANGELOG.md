# Changelog

## [Phase 7] - Final Stabilization
- Fixed multiple tripwire intersection logic in `ml_inference.py`.
- Rewrote `TripwireModal.jsx` to dynamically support unlimited virtual perimeters per camera.
- Resolved Windows file-locking permission crash during Watchlist Face representation deletions.
- Restructured repository layout, moving auxiliary test scripts to `/scripts`.
- Removed obsolete placeholder components and generated `.env.example`.

## [Phase 6] - MHA Readiness & Evidence Integrity
- Implemented `reportlab` async PDF generator for military-grade incident reports.
- Integrated SHA-256 evidence hashing for chain-of-custody validity.
- Rebranded entire application UI to "DRISHTI".
- Replaced buggy `cv2.CascadeClassifier` with robust DeepFace/RetinaFace enforcement.

## [Phase 5] - Alert De-Spamming & Cooldowns
- Stripped routine object detection alerts to prevent alert fatigue.
- Implemented per-track `last_dwelling_time` deduplication (60s cooldown).
- Added multi-frame observation requirement (3 hits) before triggering Watchlist alerts.
- Injected SQL `Camera` context directly into WebSocket alert dispatcher.

## [Phase 4] - Geospatial & Behavioral Analytics
- Replaced watermarked CARTO maps with reliable OpenStreetMap Leaflet layers.
- Added O(N^2) centroid clustering to identify suspicious Crowd Gatherings based on density.
- Implemented velocity/trajectory tracking for Fleeing Subject detection.

## [Phase 3] - Watchlist & Tripwires
- Added `WatchlistManagement.jsx` frontend.
- Added DeepFace VGG-Face embedding generation upon image upload.
- Added Virtual Tripwire drawing canvas overlay on real-time JPEG stream.
- Implemented `_ccw` vector cross-product math for line intersection detection.

## [Phase 2] - Asynchronous ML Pipeline
- Separated FastAPI API endpoints from `cv2.VideoCapture` background thread pool.
- Initialized Ultralytics YOLOv8s and ByteTrack for multi-object tracking.
- Set up SQLite Database and SQLAlchemy ORM models (`Camera`, `Event`, `WatchlistFace`).

## [Phase 1] - Initial Scaffolding
- Bootstrapped React/Vite frontend with Tailwind CSS.
- Designed Cyberpunk/Military dark mode Command Center layout (`Sidebar`, `Header`).
- Established WebSocket (`/ws/alerts`) connection for real-time reactivity.
