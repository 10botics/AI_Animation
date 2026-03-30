"""
S002 — Kling 2.6 Pro **image-to-video** from an approved Final still.

Default start frame: `Tests/Final/S002_nano-banana-2-edit_20260326T094158Z.png`.
Motion prompt is **short** (Stage 5); pass `--dry-run` to print arguments only.

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

SHOT_ID = "S002"
MODEL_ID = "fal-ai/kling-video/v2.6/pro/image-to-video"

DEFAULT_START = (
    ROOT / "Tests" / "Final" / "S002_nano-banana-2-edit_20260326T094158Z.png"
)

NEGATIVE = (
    "blur, distort, low quality, manga panel, speech bubble, halftone, "
    "extra limbs, morphing face, duplicate person, text, watermark, "
    "looking at camera, fourth wall, facing viewer, heads turning to lens, eye contact with camera"
)

# Motion-only; still = beat B2 wide (`002.jpg` row 1). Light camp business: Fern ↔ Frieren talk, Stark tends fire.
MOTION_PROMPT = (
    "Fantasy anime television wide establishing shot, cool Northern forest day — storyboard S002, exact layout and figure placement as the first frame. "
    "Character motion stays gentle: Stark stays seated by the fire on the viewer’s left — he tends the campfire, "
    "small practical motions only: nudging a log with a stick or gloved hand, brushing embers, flame flaring slightly in reply; "
    "his attention on the fire, not the camera. "
    "Frieren stays against the tree reading — eyes mostly on the book; she may lift her gaze briefly toward Fern or give a tiny nod, "
    "still holding the book open, no standing. "
    "Fern in the foreground keeps the same general facing as the reference (storyboard: mostly back to camera); "
    "only a subtle conversation — slight shoulder shift, small head turn toward Frieren and the fire, minimal mouth movement as if mid-sentence; "
    "do not spin her to face the viewer or break the wide composition. "
    "Continuity mood: still the quiet beat before the messenger and letter panels — no envelope, no animal courier in frame unless already painted. "
    "Tripod-locked camera. Environment: soft breeze on hair and coats, thin smoke, drifting embers, light on leaves. "
    "No cuts, no new characters, no manga texture or on-screen text. "
    "No one looks into the lens."
)


def main() -> int:
    parser = argparse.ArgumentParser(description="S002 → Kling 2.6 Pro I2V")
    parser.add_argument(
        "--start-image",
        type=Path,
        default=DEFAULT_START,
        help=f"Local PNG/JPEG to upload (default: {DEFAULT_START})",
    )
    parser.add_argument(
        "--duration",
        choices=("5", "10"),
        default="5",
        help='Kling duration seconds (default "5")',
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
        print(f"No video URL in response keys: {list(result.keys()) if isinstance(result, dict) else type(result)}", file=sys.stderr)
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
