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
    "webhook_url": ""
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
