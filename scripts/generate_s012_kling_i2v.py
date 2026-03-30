"""
S012 — Kling 2.6 Pro I2V: **WS** wide **backs** — **Fern** | **Frieren** + case | **Stark** toward **full gilt** Weise
(Macht / El Dorado lore beat; ref `panels/panel_s012.png`; driver `Tests/Final/`).

Requires: `FAL_KEY` in `.env`, `fal-client`.
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

SHOT_ID = "S012"
MODEL_ID = "fal-ai/kling-video/v2.6/pro/image-to-video"

DEFAULT_START = ROOT / "Tests" / "Final" / "S012_nano-banana-2-edit_20260330T044018Z.png"

NEGATIVE = (
    "blur, distort, low quality, manga panel, speech bubble, halftone, watermark, text, "
    "fourth person, duplicate, wrong left-right order, mirrored composition, "
    "faces toward camera, turning to lens, frontal faces, eyes to camera, "
    "Frieren without case, green non-gold landscape only, whip zoom, drone, hectic camera, "
    "new camera angle, extreme reframing"
)

MOTION_PROMPT = (
    "Fantasy anime television, **bright clear daytime**, **epic wide** — **match reference**: "
    "**three figures from behind** on the overlook, **gazing** toward **Fortified City of Weise** across a **gilt valley** "
    "(trees, terrain, watercourse read **polished gold** per **S012** / **S010** material continuity). "
    "**Order left to right:** **Fern**, **Frieren** center with **rectangular travel case**, **Stark** right — **backs and shoulders** to camera; **do not** mirror; **do not** spin toward lens. "
    "**Motion — slow, lore-still:** **minimal** weight shifts; **purple hair**, **blue scarf**, **white pigtails** move with **soft breeze**; **gold river** and canopy **glint** and **sparkle** slowly. "
    "**Camera:** **near-locked anime plate** — optional **hairline** slow creep toward the citadel — **no** lateral orbit, **no** 3D fly-through, **no** whip moves; trio stays readable. "
    "One continuous beat, **no cuts**, **no halftone**, **no on-screen text**, **no new characters**."
)


def main() -> int:
    parser = argparse.ArgumentParser(description="S012 → Kling 2.6 Pro I2V (wide backs + gilt Weise)")
    parser.add_argument(
        "--start-image",
        type=Path,
        default=DEFAULT_START,
        help=f"Hero still PNG (default: Tests/Final/{DEFAULT_START.name})",
    )
    parser.add_argument(
        "--duration",
        choices=("5", "10"),
        default="5",
        help='Kling duration (default "5"; use "10" for slower lore read)',
    )
    parser.add_argument("--audio", action="store_true", help="generate_audio true (costlier)")
    parser.add_argument("--dry-run", action="store_true", help="Print args only")
    args = parser.parse_args()
    start_path = args.start_image.resolve()

    assert_model_allowed(MODEL_ID)

    key = read_fal_key()
    if not key:
        print("Missing FAL_KEY — set in .env at project root.", file=sys.stderr)
        return 1

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
    start_url = fal_client.upload_file(str(start_path))
    print(f"start_image_url: {start_url}", flush=True)

    arguments = {
        "prompt": MOTION_PROMPT,
        "start_image_url": start_url,
        "duration": args.duration,
        "generate_audio": args.audio,
        "negative_prompt": NEGATIVE,
    }

    meta_path = out_dir / f"{SHOT_ID}_kling_i2v_meta_{ts}.json"
    meta_path.write_text(
        json.dumps(
            {
                "shot": SHOT_ID,
                "model_id": MODEL_ID,
                "start_image_local": str(start_path),
                "start_image_url": start_url,
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

    log_path = out_dir / f"{SHOT_ID}_kling_i2v_{ts}.json"
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
    dest = video_dir / f"{SHOT_ID}_kling-v26-pro_i2v_{ts}{ext}"
    print(f"Downloading: {vurl}", flush=True)
    download_file(vurl, dest)
    print(f"Saved: {dest}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
