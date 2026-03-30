"""
S006 — Kling 2.6 Pro **image-to-video** from an approved Stage 4 still.

Default start frame: **approved** still under **`Tests/Final/`** (Frieren at tree, Fern by fire; **camera locked** MS).
Beat B2 **MS** camp debate — default **`duration` \"5\"** (use **`10`** only if you want slower argument pacing).

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

SHOT_ID = "S006"
MODEL_ID = "fal-ai/kling-video/v2.6/pro/image-to-video"

DEFAULT_START = (
    ROOT / "Tests" / "Final" / "S006_nano-banana-2-edit_20260330T035743Z.png"
)

NEGATIVE = (
    "blur, distort, low quality, manga panel, speech bubble, halftone, "
    "extra limbs, morphing face, duplicate Frieren, duplicate Fern, text, watermark, "
    "looking at camera, fourth wall, eye contact with lens, "
    "wide establishing reframe, pulling back to S002, drone zoom out, new camera angle, "
    "characters on log seats, stark replacing composition center, squirrel, third traveler in focus"
)

# MS Weise camp — same lens as still; fire + subtle debate motion only.
MOTION_PROMPT = (
    "Fantasy anime television, cool Northern forest day — **same medium shot composition as the reference**, **panel-locked** framing — "
    "**do not** pull back to a wide camp establish or change lens. "
    "**Frieren:** seated **against the large tree**, **open book or grimoire**; **calm flat** affect with **tiny** living read — "
    "eyes lift **slightly** from the page toward **Fern** once, or a **small** finger shift on the paper; **silver-white pigtails** and white coat move with **soft breeze**. "
    "She **does not** stand, **does not** walk toward camera. "
    "**Fern:** **near the small campfire**, body **engaged toward Frieren** — **subtle forward lean**, **small** hand gesture or shift of weight on **forest floor**; "
    "**purple hair**, **blue scarf**, and gray jacket respond to the same breeze; **minimal** mouth motion only, **no** spin to face the viewer. "
    "**Stark:** if a **partial** figure reads at **frame edge**, keep him **minimal** — **no** stepping in to dominate frame. "
    "**Campfire:** gentle **flame flicker**, thin **smoke** drift, **warm** light **pulse** on nearby bark and fabric. "
    "**Camera:** **tripod-locked** — **no zoom**, **no orbit**, **no** dramatic moves; at most an imperceptible stability drift. "
    "Environment: leaves and distant bokeh **whisper** in wind. "
    "**One continuous debate beat**, no cuts, **no manga texture**, **no on-screen text**, **no new characters**."
)


def main() -> int:
    parser = argparse.ArgumentParser(description="S006 → Kling 2.6 Pro I2V (locked MS camp debate)")
    parser.add_argument(
        "--start-image",
        type=Path,
        default=DEFAULT_START,
        help=f"Hero still PNG (default: {DEFAULT_START.name})",
    )
    parser.add_argument(
        "--duration",
        choices=("5", "10"),
        default="5",
        help='Kling duration: default "5" for MS beat (use "10" for slower Fern/Frieren pacing)',
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
