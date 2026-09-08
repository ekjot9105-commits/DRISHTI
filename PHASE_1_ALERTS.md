# Phase 1 — Weapons + Alert Fan-out (Hours 8–16) · P1

Goal: any critical event reaches the judge's phone, inbox, and eardrums.

| # | Task | Touch | Est |
|---|---|---|---|
| 1.0 | Notification dispatcher — one event → all enabled channels, severity threshold, async + non-blocking | `services/notify/dispatcher.py` | 1h |
| 1.1 | Telegram alerts — bot token in `.env`, send evidence photo + caption | `services/notify/telegram.py` | 45m |
| 1.2 | Email alerts — SMTP HTML incident template with inline thumbnail | `services/notify/email.py` | 1h |
| 1.3 | Browser push — Web Notification API off the existing alert WS | `components/AlertPanel/AlertPanel.jsx` | 30m |
| 1.4 | Alarm sound — severity-based tone, mute toggle persisted | `AlertPanel.jsx`, `public/alarm.mp3` | 30m |
| 1.5 | Weapon detection — knife/gun/bat classes + confidence gate, `WEAPON` event | `services/detectors/weapon.py` | 2h |
| 1.6 | Alert settings UI — per-channel toggles + test-send button | `pages/Settings.jsx`, `api/settings.py` | 1h |

Exit: trigger one fight → Telegram ping, email, desktop popup, alarm, all within 3s.

Kickoff:
```
> Read plan/PHASE_1_ALERTS.md. Build 1.0 first as the single fan-out point,
> then 1.1. Every later channel plugs into the dispatcher, no direct calls.
```
