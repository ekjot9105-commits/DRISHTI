"""Resolve evaluation thresholds from the SAME source the running system uses.

Last night three fight tuning attempts had no effect because data/settings.json
stored an older `fight_duration` that silently shadowed the code default. The
harness must not be able to hit that trap, so it does two things:

  1. It calls `app.core.settings_manager.load_settings()` - the exact function
     `ml_inference.process_frame()` calls on every frame. There is no second
     code path and no copy of the defaults here.
  2. It reports provenance: which file was read, and precisely which keys the
     file is shadowing (present in the file AND different from the code
     default). A shadowed key is printed on every run, so a stale stored value
     can never quietly decide a result again.

`--set key=value` overrides are applied on top and reported separately, so a
threshold sweep never has to write to data/settings.json.
"""
from typing import Any, Dict, List, Tuple

from app.core.settings_manager import (DEFAULT_SETTINGS, SETTINGS_FILE,
                                       load_settings)


def _coerce(raw: str) -> Any:
    """Parse a CLI override value into bool / int / float / str."""
    low = raw.strip().lower()
    if low in ("true", "false"):
        return low == "true"
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        return raw


def parse_overrides(pairs: List[str]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for pair in pairs or []:
        if "=" not in pair:
            raise SystemExit(f"--set expects key=value, got {pair!r}")
        key, value = pair.split("=", 1)
        out[key.strip()] = _coerce(value)
    return out


def resolve(overrides: Dict[str, Any] | None = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Return (effective settings, provenance)."""
    live = load_settings()
    overrides = overrides or {}

    stored: Dict[str, Any] = {}
    exists = SETTINGS_FILE.exists()
    if exists:
        import json
        try:
            with open(SETTINGS_FILE, "r") as handle:
                stored = json.load(handle)
        except Exception:
            stored = {}

    # Keys the stored file overrides a code default with a DIFFERENT value.
    shadowed = sorted(
        key for key, value in stored.items()
        if key in DEFAULT_SETTINGS and DEFAULT_SETTINGS[key] != value
    )
    unknown = sorted(key for key in stored if key not in DEFAULT_SETTINGS)

    effective = dict(live)
    effective.update(overrides)

    provenance = {
        "source": "app.core.settings_manager.load_settings()",
        "settings_file": str(SETTINGS_FILE),
        "settings_file_exists": exists,
        "precedence": "DEFAULT_SETTINGS <- data/settings.json <- --set overrides",
        "shadowed_by_file": {k: {"default": DEFAULT_SETTINGS[k], "file": stored[k]}
                             for k in shadowed},
        "keys_only_in_file": unknown,
        "cli_overrides": dict(overrides),
    }
    return effective, provenance


def format_provenance(prov: Dict[str, Any]) -> str:
    lines = [
        "THRESHOLD SOURCE",
        f"  reader     : {prov['source']}",
        f"  file       : {prov['settings_file']}"
        f"{'' if prov['settings_file_exists'] else '  (MISSING - code defaults only)'}",
        f"  precedence : {prov['precedence']}",
    ]
    shadowed = prov["shadowed_by_file"]
    if shadowed:
        lines.append(f"  SHADOWED by data/settings.json ({len(shadowed)} keys) - "
                     f"the file wins over the code default:")
        for key, pair in shadowed.items():
            lines.append(f"      {key:26} default={pair['default']!r:>10}  file={pair['file']!r}")
    else:
        lines.append("  no stored key differs from the code defaults")
    if prov["cli_overrides"]:
        lines.append(f"  --set overrides (highest precedence): {prov['cli_overrides']}")
    return "\n".join(lines)
