# Phase 0 — Core Detection + Demo (Hours 0–8) · P0

Goal: fight + fire detection working, demoable from a phone and from canned videos.

| # | Task | Touch | Est |
|---|---|---|---|
| 0.0 | Detector registry — pluggable `Detector` base class, all detectors run per-frame and emit events | `services/detectors/base.py`, `ml_inference.py` | 45m |
| 0.1 | Fight detection — motion-energy + pose overlap on tracked person pairs, `FIGHT` event | `services/detectors/fight.py` | 2h |
| 0.2 | Fire & smoke detection — fire/smoke YOLO weights + HSV flame gate, `FIRE`/`SMOKE` event | `services/detectors/fire.py` | 1.5h |
| 0.3 | Demo mode — `backend/demo_videos/`, one-click buttons registering file-source cameras | `api/cameras.py`, `pages/Dashboard.jsx` | 1h |
| 0.4 | Phone-as-camera — `/phone` page streams webcam JPEGs over WS to `/api/cameras/{id}/push` | `ws/video_stream.py`, `pages/PhoneCam.jsx` | 2h |
| 0.5 | QR join — dashboard shows LAN QR that opens the phone page | `pages/CameraManagement.jsx` | 30m |

Exit: judges scan a QR, punch the air, and a FIGHT alert fires; demo video triggers FIRE.

Kickoff:
```
> Read plan/PHASE_0_CORE.md. Do task 0.0 then 0.1 only. Reuse the existing
> event + evidence pipeline. Stop and let me test before 0.2.
```
