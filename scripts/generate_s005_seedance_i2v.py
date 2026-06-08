"""
S005 — ByteDance **Seedance 2.0** image-to-video (`bytedance/seedance-2.0/image-to-video`).

**Stage_02:** **`present`** **CU** **B2** — foreground traveler with letter; soft memory portrait of elder mage in bokeh background.

Default driver: **`Tests/Final/S005_nano-banana-2-edit_20260330T034325Z.png`** (same as Kling script).

**Policy:** CU + face — use near-static §4b wording; silent default; `--audio` for native SFX after a clean pass.

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

SHOT_ID = "S005"
MODEL_STANDARD = "bytedance/seedance-2.0/image-to-video"
MODEL_FAST = "bytedance/seedance-2.0/fast/image-to-video"

DEFAULT_START = (
    ROOT / "Tests" / "Final" / "S005_nano-banana-2-edit_20260330T034325Z.png"
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

# Plain text only — CU near-static per anime-scene-i2v-prompting §4b (no names, no mouth emphasis).
NEAR_STATIC_MOTION_PROMPT = (
    "Fantasy anime television production shot, PG adventure, locked-off close-up, 35mm soft grain, "
    "2.39:1, shallow depth of field, cool Northern forest daylight, overcast diffused light, "
    "same composition as the reference still. "
    "Foreground figure in three-quarter profile holding folded letter or paper: eyes lowered toward the page, "
    "only subtle finger shift on the paper, purple hair and blue scarf drift in breeze, "
    "no head turn to camera, no mouth motion. "
    "Background soft translucent portrait of elder mage: barely perceptible dreamlike opacity shimmer only, "
    "stays out of focus, never becomes a second sharp person in the room. "
    "Gentle forest bokeh, one continuous contemplative beat, no cuts, no on-screen text, no manga texture, "
    "no fourth wall."
)

AUDIO_TAIL = (
    " Ambient forest day: soft wind, light cloth rustle, faint paper handling; "
    "no speech, no dialogue, no singing, no music score."
)

MOTION_PROMPT = NEAR_STATIC_MOTION_PROMPT


def main() -> int:
    parser = argparse.ArgumentParser(description="S005 → Seedance 2.0 image-to-video")
    parser.add_argument("--start-image", type=Path, default=DEFAULT_START, help="Driver still")
    parser.add_argument("--fast", action="store_true", help=f"Use {MODEL_FAST}")
    parser.add_argument(
        "--duration",
        choices=DURATION_CHOICES,
        default="8",
        help='Fal duration (default "8" for slow CU beat)',
    )
    parser.add_argument("--resolution", choices=("480p", "720p"), default="720p")
    parser.add_argument(
        "--aspect-ratio",
        dest="aspect_ratio",
        choices=("auto", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16"),
        default="16:9",
    )
    parser.add_argument("--audio", action="store_true", help="generate_audio true (default off)")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--end-image", type=Path, default=None)
    parser.add_argument("--client-timeout", type=float, default=900.0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--prompt", default=None, help="Override motion prompt")
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

    prompt_text = (args.prompt.strip() if args.prompt else MOTION_PROMPT).strip()
    if args.audio and AUDIO_TAIL.strip() not in prompt_text:
        prompt_text = prompt_text + AUDIO_TAIL

    arguments: dict = {
        "prompt": prompt_text,
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
