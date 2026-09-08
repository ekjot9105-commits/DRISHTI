# Phase 3 — Analytics, Rebrand, Extra Channels (Hours 24–31) · P3

Goal: it stops looking like a border project and starts looking like a product.

| # | Task | Touch | Est |
|---|---|---|---|
| 3.0 | Rebrand landing — universal safety copy, new name/logo, new hero | `pages/Landing.jsx`, `public/` | 1.5h |
| 3.1 | Use-case showcase — school / ATM / street / home / factory cards with icons | `pages/Landing.jsx` | 45m |
| 3.2 | Animated toasts — slide-in notification with thumbnail, severity color, auto-dismiss | `components/Toast.jsx` | 45m |
| 3.3 | Incident timeline — chronological multi-camera scrubber, click to jump to evidence | `pages/Timeline.jsx` | 1.5h |
| 3.4 | CSV / Excel export — `/api/events/export` streaming download with filters | `api/events.py` | 45m |
| 3.5 | Movement heatmap — accumulate track centroids, PNG overlay toggle per camera | `services/heatmap.py`, `CameraFeed.jsx` | 1.5h |
| 3.6 | SMS alerts (Twilio) — critical-only, via dispatcher | `services/notify/sms.py` | 30m |
| 3.7 | WhatsApp alerts — Twilio sandbox, same dispatcher hook | `services/notify/whatsapp.py` | 30m |

Exit: landing page sells the product in 10 seconds; timeline + heatmap + export cover the "so what" question.

Kickoff:
```
> Read plan/PHASE_3_POLISH.md. Do 3.0 and 3.1 first — visual impact per minute
> is highest there. Match the existing design system, don't introduce a new one.
```
