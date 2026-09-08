# Phase 2 — AI Intelligence + Any Video In (Hours 16–24) · P2

Goal: the system explains what it saw, scores the danger, and eats any video.

| # | Task | Touch | Est |
|---|---|---|---|
| 2.0 | Threat meter — 0–100 rolling score from active severities with time decay, `/api/threat` | `api/system.py`, `services/threat_score.py` | 1h |
| 2.1 | Threat gauge UI — animated dial on dashboard, color bands green→red | `components/ThreatMeter.jsx` | 45m |
| 2.2 | AI scene description — evidence frame → vision model → `description` stored on event, cached | `services/scene_describer.py` | 1.5h |
| 2.3 | Description in UI — show caption on alert cards and evidence vault | `AlertPanel.jsx`, `pages/EvidenceVault.jsx` | 30m |
| 2.4 | Video upload — drag-drop `/api/analyze/upload`, offline pass, progress + event list back | `api/analyze.py`, `pages/VideoAnalysis.jsx` | 2h |
| 2.5 | Public stream URL — yt-dlp / RTSP resolver feeding existing ingestion | `services/video_ingestion.py` | 1h |

Exit: paste a YouTube street cam, get live alerts with English captions and a live threat score.

Kickoff:
```
> Read plan/PHASE_2_INTELLIGENCE.md. Start with 2.0 + 2.1 (self-contained),
> then 2.2. Keep the vision call async so it never blocks the frame loop.
```
