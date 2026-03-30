"""
S003 — Kling 2.6 Pro **image-to-video** with **start + end** frames.

Animates from **camp plate without** foreground courier → **same camp with** messenger squirrel and Fern's attention on it.

Defaults ( **`Tests/Final/`** approved keyframes):
  start: Tests/Final/S003_extendcamp_nano-banana-2-edit_20260326T143552Z.png
  end:   Tests/Final/S003_extendcampsquirrel_nano-banana-2-edit_20260326T150111Z.png

Pass `--dry-run` to print arguments only. Requires `FAL_KEY` in project `.env`.
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
MODEL_ID = "fal-ai/kling-video/v2.6/pro/image-to-video"

DEFAULT_START = (
    ROOT
    / "Tests"
    / "Final"
    / "S003_extendcamp_nano-banana-2-edit_20260326T143552Z.png"
)
DEFAULT_END = (
    ROOT
    / "Tests"
    / "Final"
    / "S003_extendcampsquirrel_nano-banana-2-edit_20260326T150111Z.png"
)

NEGATIVE = (
    "blur, distort, low quality, manga panel, speech bubble, halftone, "
    "extra limbs, morphing face, duplicate person, text, watermark, "
    "looking at camera, fourth wall, eye contact with lens, heads snapping to viewer"
)

# Motion-first: evolve start → end layout; background cast stays shallow motion only.
MOTION_PROMPT = (
    "Fantasy anime television, cool Northern forest camp — match the **first frame** layout, then **ease into** the **second frame** pose over the clip. "
    "**Camera:** tripod-locked wide **16:9**, almost no pan or zoom. "
    "**Stark** mid-camp by the fire: small tending motions only — adjusting a log, gloved hand near embers, flames **flickering** in reply; his attention stays **down on the fire**, never at the lens. "
    "**Frieren** at her tree: **calm reading** — eyes mostly on the open book, **subtle** finger shift on pages or a **tiny** head steadying motion; she **does not** stand or swing the axe. "
    "**Fern** foreground: she **meets** the small **grey messenger squirrel** — **gentle** lean forward, **soft** head turn and gaze tracking the critter on the leaves; **hands** may lift **slightly** toward it as if acknowledging the visit; motion finishes **matching** the **end** still (squirrel upright with tiny satchel, Fern clearly engaged with it). "
    "**Squirrel** path: **smooth** arrival or settle into the leaf patch **between Fern and the fire** — **no** pop-in jump cut inside one frame. "
    "Environment: light breeze on hair and scarf, thin campfire sparkle, faint leaf drift. **One continuous beat**, no hard cuts, **no new people**, **no manga texture** or on-screen text."
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="S003 extend-camp → courier beat, Kling 2.6 Pro I2V (start + end URLs).",
    )
    parser.add_argument(
        "--start-image",
        type=Path,
        default=DEFAULT_START,
        help="First keyframe (camp without squirrel foreground)",
    )
    parser.add_argument(
        "--end-image",
        type=Path,
        default=DEFAULT_END,
        help="Second keyframe (with squirrel; Fern attending)",
    )
    parser.add_argument(
        "--duration",
        choices=("5", "10"),
        default="10",
        help='Duration seconds — prefer "10" for start→end courier beat (default "10")',
    )
    parser.add_argument(
        "--audio",
        action="store_true",
        help="Set generate_audio true (higher cost; default off)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned arguments and exit without calling Fal",
    )
    args = parser.parse_args()
    start_path = args.start_image.resolve()
    end_path = args.end_image.resolve()

    assert_model_allowed(MODEL_ID)

    key = read_fal_key()
    if not key:
        print("Missing FAL_KEY — set in .env at project root.", file=sys.stderr)
        return 1

    if not start_path.is_file():
        print(f"Start image not found: {start_path}", file=sys.stderr)
        return 1
    if not end_path.is_file():
        print(f"End image not found: {end_path}", file=sys.stderr)
        return 1

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "outputs" / "fal"
    video_dir = ROOT / "outputs" / "video"
    out_dir.mkdir(parents=True, exist_ok=True)
    video_dir.mkdir(parents=True, exist_ok=True)

    os.environ["FAL_KEY"] = key

    print(f"Uploading start frame: {start_path}", flush=True)
    start_url = fal_client.upload_file(str(start_path))
    print(f"start_image_url: {start_url}", flush=True)

    print(f"Uploading end frame: {end_path}", flush=True)
    end_url = fal_client.upload_file(str(end_path))
    print(f"end_image_url: {end_url}", flush=True)

    arguments = {
        "prompt": MOTION_PROMPT,
        "start_image_url": start_url,
        "end_image_url": end_url,
        "duration": args.duration,
        "generate_audio": args.audio,
        "negative_prompt": NEGATIVE,
    }

    meta_path = out_dir / f"{SHOT_ID}_kling_i2v_startend_meta_{ts}.json"
    meta_path.write_text(
        json.dumps(
            {
                "shot": SHOT_ID,
                "model_id": MODEL_ID,
                "start_image_local": str(start_path),
                "end_image_local": str(end_path),
                "start_image_url": start_url,
                "end_image_url": end_url,
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

    print(f"Submitting {MODEL_ID} …", flush=True)
    try:
        result = fal_client.subscribe(
            MODEL_ID,
            arguments=arguments,
            with_logs=True,
        )
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    log_path = out_dir / f"{SHOT_ID}_kling_i2v_startend_{ts}.json"
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
    dest = video_dir / f"{SHOT_ID}_kling-v26-pro_i2v_startend_{ts}{ext}"
    print(f"Downloading: {vurl}", flush=True)
    download_file(vurl, dest)
    print(f"Saved: {dest}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
