"""
S009 — ByteDance **Seedance 2.0** image-to-video (`bytedance/seedance-2.0/image-to-video`).

**WS** present forest path: trio walking toward camera — warrior left, mage center with rectangular
travel case, traveler right. §4b production prompt (visual facts, no Flux paste).

Default still: `Tests/Final/S009_nano-banana-2-edit_20260527T084918Z.png`.

Docs: https://fal.ai/models/bytedance/seedance-2.0/image-to-video

Requires: `FAL_KEY` in project `.env`, package `fal-client`.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import fal_client

from fal_common import (
    ROOT,
    assert_model_allowed,
    download_file,
    extension_from_url,
    read_fal_key,
    video_url_from_result,
)

SHOT_ID = "S009"
MODEL_STANDARD = "bytedance/seedance-2.0/image-to-video"
MODEL_FAST = "bytedance/seedance-2.0/fast/image-to-video"

DEFAULT_START = (
    ROOT / "Tests" / "Final" / "S009_nano-banana-2-edit_20260527T084918Z.png"
)

DURATION_CHOICES = (
    "auto",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "11",
    "12",
    "13",
    "14",
    "15",
)

# §4b WS path — production register, role labels, gentle walk (stage_02 B3 present).
MOTION_PROMPT = (
    "Fantasy anime television production shot, PG adventure, locked-off wide shot, 35mm soft grain, "
    "2.39:1, bright sun-flecked Northern forest path, overcast diffused daylight, same layout as the reference still. "
    "Three travelers on the dirt trail toward camera: warrior figure left in frame order, "
    "mage figure center carrying rectangular travel case, traveler figure right — left-to-right order unchanged, do not mirror. "
    "Slow casual forward walk with soft heel-to-toe steps, each figure half a beat out of sync, knees flex naturally, "
    "no sprint or lockstep march; rectangular case swings slightly at center figure's side; "
    "coats, scarf, and hair drift and follow through in a gentle woodland breeze. "
    "Dappled sunlight slides across path bark and leaves; background trees hold layered depth, subtle shimmer only. "
    "Tripod-locked camera with imperceptible slow push forward only, no orbital move, no whip zoom, no crane rise. "
    "One continuous journey beat, no cuts, no on-screen text, no manga texture, no fourth wall, no new people. "
    "Ambient forest trail day: soft footsteps on dirt, light leaf rustle, canopy breeze, cloth and case creak; "
    "no speech, no dialogue, no vocalizations, no singing, no music score."
)


def main() -> int:
    parser = argparse.ArgumentParser(description="S009 → Seedance 2.0 image-to-video (WS path)")
    parser.add_argument(
        "--start-image",
        type=Path,
        default=DEFAULT_START,
        help=f"Driver still (default: {DEFAULT_START.name})",
    )
    parser.add_argument("--fast", action="store_true", help=f"Use {MODEL_FAST}")
    parser.add_argument(
        "--duration",
        choices=DURATION_CHOICES,
        default="5",
        help='Fal duration string (default "5")',
    )
    parser.add_argument(
        "--resolution",
        choices=("480p", "720p"),
        default="720p",
    )
    parser.add_argument(
        "--aspect-ratio",
        dest="aspect_ratio",
        choices=("auto", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16"),
        default="16:9",
    )
    parser.add_argument(
        "--audio",
        action="store_true",
        help="Set generate_audio true (foley steered in prompt; default off)",
    )
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument(
        "--end-image",
        type=Path,
        default=None,
        help="Optional last frame (end_image_url)",
    )
    parser.add_argument(
        "--client-timeout",
        type=float,
        default=900.0,
        help="fal_client.subscribe timeout seconds (default 900)",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    model_id = MODEL_FAST if args.fast else MODEL_STANDARD
    assert_model_allowed(model_id)

    key = read_fal_key()
    if not key:
        print("Missing FAL_KEY — set in .env at project root.", file=sys.stderr)
        return 1

    start_path = args.start_image.resolve()
    if not start_path.is_file():
        print(f"Start image not found: {start_path}", file=sys.stderr)
        return 1

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "outputs" / "fal"
    video_dir = ROOT / "outputs" / "video"
    out_dir.mkdir(parents=True, exist_ok=True)
    video_dir.mkdir(parents=True, exist_ok=True)

    os.environ["FAL_KEY"] = key

    prompt = MOTION_PROMPT
    if not args.audio:
        # Strip audio clause when silent (last two sentences).
        prompt = (
            "Fantasy anime television production shot, PG adventure, locked-off wide shot, 35mm soft grain, "
            "2.39:1, bright sun-flecked Northern forest path, overcast diffused daylight, same layout as the reference still. "
            "Three travelers on the dirt trail toward camera: warrior figure left in frame order, "
            "mage figure center carrying rectangular travel case, traveler figure right — left-to-right order unchanged, do not mirror. "
            "Slow casual forward walk with soft heel-to-toe steps, each figure half a beat out of sync, knees flex naturally, "
            "no sprint or lockstep march; rectangular case swings slightly at center figure's side; "
            "coats, scarf, and hair drift and follow through in a gentle woodland breeze. "
            "Dappled sunlight slides across path bark and leaves; background trees hold layered depth, subtle shimmer only. "
            "Tripod-locked camera with imperceptible slow push forward only, no orbital move, no whip zoom, no crane rise. "
            "One continuous journey beat, no cuts, no on-screen text, no manga texture, no fourth wall, no new people."
        )

    print(f"Uploading start frame: {start_path}", flush=True)
    image_url = fal_client.upload_file(str(start_path))
    print(f"image_url: {image_url}", flush=True)

    arguments: dict = {
        "prompt": prompt,
        "image_url": image_url,
        "resolution": args.resolution,
        "duration": args.duration,
        "aspect_ratio": args.aspect_ratio,
        "generate_audio": bool(args.audio),
    }
    if args.seed is not None:
        arguments["seed"] = int(args.seed)

    if args.end_image is not None:
        ep = args.end_image.resolve()
        if not ep.is_file():
            print(f"--end-image not found: {ep}", file=sys.stderr)
            return 1
        print(f"Uploading end frame: {ep}", flush=True)
        arguments["end_image_url"] = fal_client.upload_file(str(ep))

    variant = "seedance-2-fast-i2v" if args.fast else "seedance-2-i2v"
    audio_tag = "-audio" if args.audio else ""
    meta_path = out_dir / f"{SHOT_ID}_{variant}_meta_{ts}{audio_tag}.json"
    meta_path.write_text(
        json.dumps(
            {
                "shot": SHOT_ID,
                "model_id": model_id,
                "start_image_local": str(start_path),
                "arguments": arguments,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Meta: {meta_path}", flush=True)

    if args.dry_run:
        print(json.dumps(arguments, indent=2))
        return 0

    print(f"Submitting {model_id} …", flush=True)
    try:
        result = fal_client.subscribe(
            model_id,
            arguments=arguments,
            with_logs=True,
            client_timeout=args.client_timeout,
        )
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    log_path = out_dir / f"{SHOT_ID}_{variant}_{ts}{audio_tag}.json"
    log_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(f"Log: {log_path}", flush=True)

    vurl = video_url_from_result(result)
    if not vurl:
        print(
            f"No video URL in response keys: {list(result.keys()) if isinstance(result, dict) else type(result)}",
            file=sys.stderr,
        )
        return 1

    ext = extension_from_url(vurl)
    if ext not in (".mp4", ".webm", ".mov"):
        ext = ".mp4"
    dest = video_dir / f"{SHOT_ID}_{variant}{audio_tag}_{ts}{ext}"
    print(f"Downloading: {vurl}", flush=True)
    download_file(vurl, dest)
    print(f"Saved: {dest}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
