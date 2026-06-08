"""
S003 — ByteDance **Seedance 2.0** image-to-video (`bytedance/seedance-2.0/image-to-video`).

**Motion** is derived from **Chapter-81** stage_02: **MCU profile**, **present** camp beat **B2** —
**Fern** (left-facing profile in layout terms) + **squirrel-like messenger** with **bag** at her side,
**before** the sealed-envelope beat (**S004**). Driver still should match **`generate_s003_ref_edit.py --variant full`**.

Default start: latest full-color still from Nano Banana (`Tests/…`). Optional **`--end-image`** uploads
`end_image_url` if you have a second keyframe (e.g. extend-camp → courier) — same API as S002 script.

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

SHOT_ID = "S003"
MODEL_STANDARD = "bytedance/seedance-2.0/image-to-video"
MODEL_FAST = "bytedance/seedance-2.0/fast/image-to-video"

# Approved full MCU (panel_s003 beat); override with --start-image (e.g. Final extendcampsquirrel).
DEFAULT_START = (
    ROOT / "Tests" / "S003_full_nano-banana-2-edit_20260410T111047Z.png"
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

# Motion-first: stage_02 S003 MCU + PREFIX_PRESENT cool Northern; chirality must match still (no mirror).
MOTION_PROMPT = (
    "Fantasy anime television medium close-up profile, cool Northern forest camp daylight — storyboard S003, "
    "same composition as the first frame: Fern seated on leaf-strewn ground in left-facing profile "
    "(face toward frame left — do not mirror her); her gaze on the small squirrel messenger with travel bag "
    "on the ground beside her — subtle eyes tracking the animal, minimal mouth movement, slight forward lean; "
    "no full turn to camera. Messenger: tiny ear flick, tail micro-twitch, satchel strap settling, paws on leaves; "
    "no new animal, no duplicate Fern. Tripod-locked camera, almost no pan; soft breeze on hair and coat, leaf drift. "
    "One beat before the letter exchange — no sealed envelope, no Frieren or Stark taking over the frame. "
    "No cuts, no manga halftone or on-screen text, no fourth wall. "
    "Ambient forest camp audio: soft wind in leaves, distant campfire crackle, light cloth rustle, "
    "small leaf scuff foley; no speech, no dialogue, no singing, no music score."
)


def main() -> int:
    parser = argparse.ArgumentParser(description="S003 → Seedance 2.0 image-to-video")
    parser.add_argument(
        "--start-image",
        type=Path,
        default=DEFAULT_START,
        help=f"Driver still PNG/JPEG/WebP (default: {DEFAULT_START})",
    )
    parser.add_argument("--fast", action="store_true", help=f"Use {MODEL_FAST}")
    parser.add_argument(
        "--duration",
        choices=DURATION_CHOICES,
        default="5",
        help='Fal duration string (default "5" for MCU beat)',
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
        help="generate_audio true (default off)",
    )
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument(
        "--end-image",
        type=Path,
        default=None,
        help="Optional last frame (end_image_url), e.g. courier emphasis still",
    )
    parser.add_argument("--client-timeout", type=float, default=900.0)
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

    print(f"Uploading start frame: {start_path}", flush=True)
    image_url = fal_client.upload_file(str(start_path))
    print(f"image_url: {image_url}", flush=True)

    arguments: dict = {
        "prompt": MOTION_PROMPT,
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
    meta_path = out_dir / f"{SHOT_ID}_{variant}_meta_{ts}.json"
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

    log_path = out_dir / f"{SHOT_ID}_{variant}_{ts}.json"
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
    dest = video_dir / f"{SHOT_ID}_{variant}_{ts}{ext}"
    print(f"Downloading: {vurl}", flush=True)
    download_file(vurl, dest)
    print(f"Saved: {dest}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
