"""Evaluate ONE clip, in its own process, and print a JSON result.

One process per clip is deliberate: ByteTrack, the fire streaks, the fight pair
streaks and every detector cooldown are process-global state keyed by camera id.
Running two clips in one interpreter would let a streak or a cooldown from clip
A decide the verdict on clip B. The orchestrator (evaluate.py) spawns this.

Frames take the production path exactly: resized to 640x480, every third frame
handed to `ml_service.process_frame()`, which is what the ingestion thread
calls - so YOLO, ByteTrack and the whole detector registry run as they do live.

The frame clock is driven at a fixed rate rather than by wall clock. Detector
persistence is measured in seconds, so on a machine where YOLO runs at 6fps a
wall-clock run would silently apply different effective durations than the
10fps production pipeline. Freezing it makes runs reproducible and comparable.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import cv2

BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

FRAME_W, FRAME_H = 640, 480
STRIDE = 3          # ml_inference sends every 3rd frame to inference
FALLBACK_FPS = 30.0                 # used when the container reports no rate


def eval_fps(capture) -> float:
    """Inference-rate for this clip: its real frame rate divided by the stride.

    Detector persistence (fight_duration, fire_duration) is measured in
    seconds, so assuming 30fps for a 15fps clip would halve every effective
    duration and silently change verdicts. Read the real rate per clip.
    """
    raw = capture.get(cv2.CAP_PROP_FPS) or 0.0
    if not (1.0 < raw < 240.0):
        raw = FALLBACK_FPS
    return raw / STRIDE


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("clip", help="path to the video file")
    parser.add_argument("--camera-id", type=int, default=9001)
    parser.add_argument("--max-frames", type=int, default=0,
                        help="0 = whole clip")
    parser.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                        help="threshold override applied above data/settings.json")
    args = parser.parse_args()

    import app.core.config  # noqa: F401  - loads .env before anything reads it
    from eval.settings_source import parse_overrides, resolve
    from eval.features import FeatureCollector

    overrides = parse_overrides(args.set)
    settings, provenance = resolve(overrides)

    # Patch the settings reader that ml_inference calls, so overrides reach the
    # real pipeline without touching data/settings.json on disk.
    import app.services.ml_inference as mli
    mli.load_settings = lambda: dict(settings)

    from app.services.ml_inference import ml_service
    from app.services.detectors import base

    fire_detector = next((d for d in base.get_detectors() if d.name == "fire"), None)

    clip_path = Path(args.clip)
    capture = cv2.VideoCapture(str(clip_path))
    if not capture.isOpened():
        print(json.dumps({"clip": clip_path.name, "error": "could not open clip"}))
        return 2

    fps = eval_fps(capture)
    collector = FeatureCollector(fire_detector, settings, fps) if fire_detector else None

    started = time.time()
    base_clock = 1_000_000.0     # arbitrary fixed epoch; detectors only use deltas
    read = processed = 0
    alerts = []

    while True:
        ok, frame = capture.read()
        if not ok:
            break
        read += 1
        if read % STRIDE:
            continue
        frame = cv2.resize(frame, (FRAME_W, FRAME_H))
        processed += 1
        if args.max_frames and processed > args.max_frames:
            break

        stamp = base_clock + processed / fps
        real_time = time.time
        time.time = lambda _s=stamp: _s          # deterministic frame clock
        try:
            found, boxes = ml_service.process_frame(args.camera_id, frame)
        finally:
            time.time = real_time

        if collector is not None:
            collector.observe(frame, boxes)
        for alert in found:
            alerts.append({
                "type": alert.get("type"),
                "severity": alert.get("severity"),
                "t": round(processed / fps, 2),
                "detail": (alert.get("detail") or "")[:160],
            })

    capture.release()

    counts = {}
    for alert in alerts:
        counts[alert["type"]] = counts.get(alert["type"], 0) + 1

    result = {
        "clip": clip_path.name,
        "frames_read": read,
        "frames_processed": processed,
        "duration_s": round(processed / fps, 2),
        "eval_fps": round(fps, 2),
        "source_fps": round(fps * STRIDE, 2),
        "wall_s": round(time.time() - started, 1),
        "alert_counts": counts,
        "alerts": alerts[:40],
        "features": collector.summary() if collector else {},
        "pair_frames": collector.pair_frames() if collector else [],
        "settings_provenance": provenance,
    }
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
