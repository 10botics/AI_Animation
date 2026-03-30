"""
S005 — Kling 2.6 Pro **image-to-video** from an approved Stage 4 still.

Default start frame: **`Tests/Final/`** approved S005 still (Fern CU + Lernen memory telegraph).
Beat B2 — slower **CU** + ghost portrait → default **`duration` \"10\"** (vs MS S004 **5s**).

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
MODEL_ID = "fal-ai/kling-video/v2.6/pro/image-to-video"

DEFAULT_START = ROOT / "Tests" / "Final" / "S005_nano-banana-2-edit_20260330T034325Z.png"

NEGATIVE = (
    "blur, distort, low quality, manga panel, speech bubble, halftone, "
    "extra limbs, morphing face, duplicate solid Lernen, second Fern, text, watermark, "
    "looking at camera, fourth wall, Denken, wrong elder face, "
    "memory portrait turning into solid blocking figure, harsh jump cut"
)

# CU + ethereal flashback — minimal camera; breath, letter, dreamlike BG drift.
MOTION_PROMPT = (
    "Fantasy anime television, cool Northern forest day — **same composition as the reference**: "
    "**Fern** in **close foreground** **three-quarter or profile**, eyes lowered toward **letter or paper** in her hands; "
    "**soft translucent memory portrait** of elder mage **Lernen** in the **background** — ghostly, out of focus. "
    "**Camera:** **locked** CU — **no zoom**, **no pan**; at most an imperceptible stability drift. "
    "**Fern:** **subtle** living read — **slow** blink, **very slight** shift of gaze along the lines, **fingers** adjust grip on the paper; "
    "**purple hair** and **blue scarf** move with a **light breeze**; she **does not** snap her head to the camera. "
    "**Lernen telegraph:** **barely** moving — **micro** drift or **soft** opacity **pulse** like remembered light, **stays** dreamlike, "
    "**never** becomes a second sharp body beside her. "
    "**No** dialogue mouth flaps required. Environment: gentle forest bokeh, cool daylight, shallow depth. "
    "**One continuous contemplative beat**, no cuts, **no manga texture**, **no on-screen text**, **no new characters**."
)


def main() -> int:
    parser = argparse.ArgumentParser(description="S005 → Kling 2.6 Pro I2V (CU + memory telegraph)")
    parser.add_argument(
        "--start-image",
        type=Path,
        default=DEFAULT_START,
        help=f"Hero still PNG (default: {DEFAULT_START.name})",
    )
    parser.add_argument(
        "--duration",
        choices=("5", "10"),
        default="10",
        help='Kling duration: default "10" for slow CU + memory beat (use "5" for a tighter test)',
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
