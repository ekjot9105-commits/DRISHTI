# Phase 4 — Stretch + Freeze (Hours 31–36) · P4

Only start an item if ≥2h remain. Anything unfinished at H-2 gets reverted, not debugged.

| # | Task | Touch | Est |
|---|---|---|---|
| 4.0 | Dark / light toggle — CSS variables + persisted theme | `index.css`, `Header.jsx` | 45m |
| 4.1 | Responsive mobile view — landing + alert center breakpoints | `Landing.jsx`, `AlertCenter.jsx` | 1h |
| 4.2 | Webhook integration — configurable POST URL per event type | `services/notify/webhook.py` | 45m |
| 4.3 | ONVIF auto-discovery — WS-Discovery LAN scan → suggested camera list | `services/onvif_discovery.py` | 1.5h |
| 4.4 | JWT auth — Admin / Operator / Auditor roles + route guards | `core/auth.py`, `api/*`, `App.jsx` | 2h |

## Freeze checklist (last 2 hours — do this regardless)
- Merge everything to `main`, cold-boot the whole stack from scratch once.
- Run the full demo script end to end twice; time it.
- Pre-load demo videos, pre-connect the phone camera, pre-open the Telegram channel.
- Seed the DB with a few past events so analytics/timeline aren't empty.
- Screen-record a backup demo in case the venue WiFi dies.
- Update `README.md` with the new name, features, and 3-command setup.

Kickoff:
```
> Read plan/PHASE_4_STRETCH.md. Do 4.0 only. Do not refactor anything.
```
