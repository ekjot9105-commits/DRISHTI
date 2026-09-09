"""Clip manifest: expected event types per clip, derived from the filename.

Naming convention (backend/eval_clips/):
    fight_NN.mp4  -> expects ["fight"]
    fire_NN.mp4   -> expects ["fire"]
    crash_NN.mp4  -> expects ["crash"]
    neg_NN.mp4    -> expects []            (negative: nothing may fire)

Entries are generated from those prefixes, but hand edits win. Set
`"source": "manual"` on an entry (or just edit `expected`, which flips it to
manual automatically on the next write) and regeneration will never clobber it.
"""
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

PREFIX_EXPECTS: Dict[str, List[str]] = {
    "fight": ["fight"],
    "fire": ["fire"],
    "crash": ["crash"],
    "smoke": ["smoke"],
    "neg": [],
}

VIDEO_SUFFIXES = (".mp4", ".avi", ".mov", ".mkv", ".webm")
_NAME = re.compile(r"^([a-zA-Z]+)[_-]?(\d+)?")


def expected_for(filename: str) -> Tuple[List[str], str]:
    """(expected event types, class label) inferred from the filename prefix."""
    match = _NAME.match(Path(filename).stem.lower())
    prefix = match.group(1) if match else ""
    if prefix in PREFIX_EXPECTS:
        return list(PREFIX_EXPECTS[prefix]), prefix
    return [], "unlabelled"


def discover(clips_dir: Path) -> List[str]:
    if not clips_dir.exists():
        return []
    return sorted(p.name for p in clips_dir.iterdir()
                  if p.suffix.lower() in VIDEO_SUFFIXES and p.is_file())


def load_or_create(manifest_path: Path, clips_dir: Path) -> Dict[str, Any]:
    """Merge the on-disk manifest with whatever clips are present.

    Never deletes an entry (a clip may simply not have downloaded yet) and
    never overwrites one marked manual.
    """
    existing: Dict[str, Any] = {}
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as handle:
                existing = json.load(handle).get("clips", {})
        except Exception:
            existing = {}

    present = discover(clips_dir)
    clips: Dict[str, Any] = {}

    for name in sorted(set(present) | set(existing)):
        prior = existing.get(name)
        if prior and prior.get("source") == "manual":
            entry = dict(prior)
        else:
            auto_expected, label = expected_for(name)
            entry = {
                "expected": auto_expected,
                "label": label,
                "source": "auto",
                "note": (prior or {}).get("note", ""),
            }
            # A hand-edited `expected` that no longer matches the prefix is
            # treated as deliberate and promoted to manual.
            if prior and prior.get("expected") != auto_expected:
                entry["expected"] = prior["expected"]
                entry["label"] = prior.get("label", label)
                entry["source"] = "manual"
        entry["present"] = name in present
        clips[name] = entry

    return {
        "_comment": ("Generated from filename prefixes; edit any entry and set "
                     "\"source\": \"manual\" to protect it from regeneration."),
        "conventions": {k: v for k, v in PREFIX_EXPECTS.items()},
        "clips": clips,
    }


def save(manifest_path: Path, manifest: Dict[str, Any]) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")


def split_present_missing(manifest: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    clips = manifest["clips"]
    present = [n for n, e in clips.items() if e.get("present")]
    missing = [n for n, e in clips.items() if not e.get("present")]
    return present, missing
