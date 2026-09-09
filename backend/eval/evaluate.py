"""Run every clip in backend/eval_clips/ and report detector accuracy.

Usage (from backend/):
    python -m eval.evaluate
    python -m eval.evaluate --set fire_sat_std_min=18 --out results/try_a.json
    python -m eval.evaluate --only fight_01.mp4 --only neg_03.mp4

Each clip runs in its own subprocess (see runner.py) so tracker and streak
state cannot leak between clips. Results print as tables and are written to
JSON for diffing between tuning runs.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from eval import manifest as manifest_mod          # noqa: E402
from eval.features import ALL_FEATURES             # noqa: E402
from eval.settings_source import (format_provenance, parse_overrides,  # noqa: E402
                                  resolve)

CLIPS_DIR = BACKEND / "eval_clips"
MANIFEST_PATH = BACKEND / "eval" / "manifest.json"
DEFAULT_OUT = BACKEND / "eval" / "results" / "eval_results.json"

# Detectors scored. `smoke` is included because the fire detector can emit it.
DETECTORS = ["fight", "fire", "crash", "smoke"]


# ---------------------------------------------------------------- running ---
def run_clip(clip: Path, camera_id: int, overrides: List[str],
             max_frames: int) -> Dict[str, Any]:
    cmd = [sys.executable, "-m", "eval.runner", str(clip),
           "--camera-id", str(camera_id)]
    if max_frames:
        cmd += ["--max-frames", str(max_frames)]
    for pair in overrides:
        cmd += ["--set", pair]

    proc = subprocess.run(cmd, cwd=str(BACKEND), capture_output=True, text=True)
    stdout = (proc.stdout or "").strip().splitlines()
    for line in reversed(stdout):            # last line is the JSON payload
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return {"clip": clip.name,
            "error": f"runner failed (exit {proc.returncode})",
            "stderr": (proc.stderr or "")[-400:]}


# ---------------------------------------------------------------- scoring ---
def score(results: Dict[str, Dict[str, Any]],
          clips: Dict[str, Any]) -> Dict[str, Any]:
    per_detector: Dict[str, Dict[str, Any]] = {}

    for det in DETECTORS:
        tp = fp = fn = tn = 0
        fp_clips, fn_clips = [], []
        for name, result in results.items():
            if result.get("error"):
                continue
            expected = set(clips[name]["expected"])
            fired = (result.get("alert_counts", {}).get(det, 0) > 0)
            wanted = det in expected
            if wanted and fired:
                tp += 1
            elif wanted and not fired:
                fn += 1
                fn_clips.append(name)
            elif not wanted and fired:
                fp += 1
                fp_clips.append(name)
            else:
                tn += 1

        precision = tp / (tp + fp) if (tp + fp) else None
        recall = tp / (tp + fn) if (tp + fn) else None
        fpr = fp / (fp + tn) if (fp + tn) else None
        per_detector[det] = {
            "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": precision, "recall": recall, "false_positive_rate": fpr,
            "false_positive_clips": fp_clips,
            "false_negative_clips": fn_clips,
        }

    # Confusion matrix: actual clip label x event type actually emitted.
    labels = sorted({clips[n].get("label", "unlabelled") for n in results})
    columns = DETECTORS + ["none"]
    matrix = {label: {col: 0 for col in columns} for label in labels}
    for name, result in results.items():
        if result.get("error"):
            continue
        label = clips[name].get("label", "unlabelled")
        counts = result.get("alert_counts", {})
        fired_any = False
        for det in DETECTORS:
            if counts.get(det, 0) > 0:
                matrix[label][det] += 1
                fired_any = True
        if not fired_any:
            matrix[label]["none"] += 1

    return {"per_detector": per_detector,
            "confusion_matrix": matrix,
            "confusion_columns": columns}


# --------------------------------------------------------------- printing ---
def _fmt(value: Any, width: int = 8, places: int = 3) -> str:
    if value is None:
        return "-".rjust(width)
    if isinstance(value, float):
        return f"{value:.{places}f}".rjust(width)
    return str(value).rjust(width)


def print_report(results: Dict[str, Dict[str, Any]], clips: Dict[str, Any],
                 scored: Dict[str, Any], missing: List[str],
                 provenance: Dict[str, Any]) -> None:
    print()
    print(format_provenance(provenance))

    print()
    print("PER-CLIP RESULTS")
    header = f"  {'clip':26} {'expected':16} {'fired':22} {'frames':>7}  verdict"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for name in sorted(results):
        result = results[name]
        entry = clips[name]
        expected = ",".join(entry["expected"]) or "(none)"
        if result.get("error"):
            print(f"  {name:26} {expected:16} {'ERROR':22} {'-':>7}  {result['error']}")
            continue
        counts = result.get("alert_counts", {})
        fired = ",".join(f"{k}x{v}" for k, v in sorted(counts.items())) or "(none)"
        want = set(entry["expected"])
        got = {k for k, v in counts.items() if v}
        if got == want:
            verdict = "PASS"
        elif got - want:
            verdict = f"FALSE POSITIVE: {','.join(sorted(got - want))}"
        else:
            verdict = f"MISSED: {','.join(sorted(want - got))}"
        print(f"  {name:26} {expected:16} {fired:22} "
              f"{result.get('frames_processed', 0):>7}  {verdict}")

    print()
    print("DETECTOR METRICS (clip level)")
    print(f"  {'detector':10} {'TP':>4} {'FP':>4} {'FN':>4} {'TN':>4} "
          f"{'precision':>10} {'recall':>8} {'FPR':>8}")
    print("  " + "-" * 62)
    for det in DETECTORS:
        m = scored["per_detector"][det]
        print(f"  {det:10} {m['tp']:>4} {m['fp']:>4} {m['fn']:>4} {m['tn']:>4} "
              f"{_fmt(m['precision'], 10)} {_fmt(m['recall'], 8)} "
              f"{_fmt(m['false_positive_rate'], 8)}")
    for det in DETECTORS:
        m = scored["per_detector"][det]
        if m["false_positive_clips"]:
            print(f"    {det} FALSE POSITIVES : {', '.join(m['false_positive_clips'])}")
        if m["false_negative_clips"]:
            print(f"    {det} missed          : {', '.join(m['false_negative_clips'])}")

    print()
    print("CONFUSION MATRIX  (rows = actual clip class, cols = event emitted)")
    columns = scored["confusion_columns"]
    print(f"  {'actual':12} " + " ".join(c.rjust(7) for c in columns))
    print("  " + "-" * (12 + 8 * len(columns)))
    for label in sorted(scored["confusion_matrix"]):
        row = scored["confusion_matrix"][label]
        print(f"  {label:12} " + " ".join(str(row[c]).rjust(7) for c in columns))

    print()
    print("PER-CLIP FEATURE MEDIANS  (why a clip passes or fails)")
    short = {"flame_area_frac": "area", "core_frac": "core", "adj_frac": "adj",
             "sat_std": "sat_sd", "hue_std": "hue_sd",
             "in_region_flicker": "flick", "pair_iou": "pIoU",
             "motion_energy": "energy", "longest_contact_s": "contact_s"}
    print(f"  {'clip':26} " + " ".join(short[f].rjust(9) for f in ALL_FEATURES))
    print("  " + "-" * (26 + 10 * len(ALL_FEATURES)))
    for name in sorted(results):
        feats = results[name].get("features") or {}
        if not feats:
            continue
        cells = []
        for key in ALL_FEATURES:
            value = feats.get(key)
            cells.append("-".rjust(9) if value is None
                         else f"{value:.4f}".rjust(9) if abs(value) < 1
                         else f"{value:.2f}".rjust(9))
        print(f"  {name:26} " + " ".join(cells))

    if missing:
        print()
        print(f"MISSING FROM eval_clips/ ({len(missing)} listed in the manifest, "
              f"not on disk):")
        for name in missing:
            print(f"  - {name}")


# ------------------------------------------------------------------- main ---
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clips-dir", default=str(CLIPS_DIR))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--only", action="append", default=[],
                        help="evaluate just this clip (repeatable)")
    parser.add_argument("--max-frames", type=int, default=0)
    parser.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                        help="threshold override applied above data/settings.json")
    parser.add_argument("--label", default="", help="tag stored in the JSON output")
    args = parser.parse_args()

    clips_dir = Path(args.clips_dir)
    clips_dir.mkdir(parents=True, exist_ok=True)

    man = manifest_mod.load_or_create(MANIFEST_PATH, clips_dir)
    manifest_mod.save(MANIFEST_PATH, man)
    present, missing = manifest_mod.split_present_missing(man)

    if args.only:
        present = [n for n in present if n in set(args.only)]

    _, provenance = resolve(parse_overrides(args.set))

    if not present:
        print()
        print(format_provenance(provenance))
        print()
        print(f"No clips to evaluate. Put videos in {clips_dir} named "
              f"fight_NN.mp4 / fire_NN.mp4 / crash_NN.mp4 / neg_NN.mp4.")
        print(f"Manifest written to {MANIFEST_PATH}")
        if missing:
            print(f"Listed in the manifest but not on disk: {', '.join(missing)}")
        return 0

    print(f"Evaluating {len(present)} clip(s), one process each...")
    results: Dict[str, Dict[str, Any]] = {}
    for index, name in enumerate(sorted(present)):
        print(f"  [{index + 1}/{len(present)}] {name}", flush=True)
        results[name] = run_clip(clips_dir / name, 9000 + index,
                                 args.set, args.max_frames)

    scored = score(results, man["clips"])
    print_report(results, man["clips"], scored, missing, provenance)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "label": args.label,
        "settings_provenance": provenance,
        "clips_evaluated": sorted(present),
        "missing_clips": missing,
        "results": results,
        "scores": scored,
    }
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    print()
    print(f"JSON written to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
