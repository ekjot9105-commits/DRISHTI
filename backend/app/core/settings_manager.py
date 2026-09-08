import json
import os
from pathlib import Path

SETTINGS_FILE = Path("data/settings.json")

DEFAULT_SETTINGS = {
    "confidence_threshold": 0.35,
    "intrusion_cooldown": 10.0,
    "dwelling_time": 10.0,
    "night_mode": False,
    "fleeing_threshold": 300.0, # px/sec
    "fleeing_duration": 1.5, # seconds
    "crowd_count": 3,
    "crowd_density": 150.0, # px distance
    "crowd_duration": 60.0,
    "webhook_url": "",
    # --- Detectors ---
    "fight_enabled": True,
    "fight_iou": 0.10,             # min box overlap between two persons
    "fight_motion_energy": 12.0,   # mean frame-diff inside the pair ROI
    "fight_duration": 1.2,         # seconds both conditions must hold
    "fight_cooldown": 20.0,        # seconds between alerts for the same pair
    "fire_enabled": True,
    "fire_area_ratio": 0.04,       # frame fraction matching the dual-band flame mask
    "fire_flicker": 12.0,          # min mean frame-diff INSIDE the flame mask
    "fire_duration": 1.5,          # seconds the signature must hold
    "fire_streak_tolerance": 3,    # consecutive sub-threshold frames forgiven
    "fire_min_hit_ratio": 0.6,     # streak must be >=60% actual hits to fire
    "fire_max_gap": 0.5,           # max seconds between real hits in a streak
    "fire_cooldown": 60.0,         # seconds between alerts per camera
    # The colour-only smoke gate also matches asphalt and overcast sky
    # (99.6% of a road scene), so it is opt-in. Smoke from real fire/smoke
    # weights is unaffected by this flag.
    "smoke_enabled": False,
    "smoke_area_ratio": 0.15,

    # --- Notification fan-out ---
    # Master switch, plus a per-channel enable + severity threshold.
    # Thresholds are one of: info < warning < high < critical.
    "notify_enabled": True,
    "notify_timeout": 10.0,           # seconds before a channel send is abandoned
    "notify_max_blocking_threads": 16,  # cap on hung blocking-channel threads
    "notify_null_enabled": True,      # log-only channel, safe to leave on
    "notify_null_min_severity": "info",
    # Email: credentials come from .env (SMTP_*), never from here.
    "notify_email_enabled": True,
    "notify_email_min_severity": "critical",
    "notify_email_evidence_wait": 3.0,   # bounded wait for the evidence JPEG
    "notify_email_smtp_timeout": 20.0,
    # --- Operator console (browser push + alarm) ---
    "alarm_muted": False,             # persisted mute toggle for the alarm tone
    "alarm_cooldown": 3.0,            # min seconds between alarm plays (anti-spam)
    "browser_push_enabled": True
}

def load_settings():
    if not SETTINGS_FILE.exists():
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
            # Merge with defaults to ensure all keys exist
            merged = DEFAULT_SETTINGS.copy()
            merged.update(data)
            return merged
    except:
        return DEFAULT_SETTINGS

def save_settings(settings: dict):
    os.makedirs(SETTINGS_FILE.parent, exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)
