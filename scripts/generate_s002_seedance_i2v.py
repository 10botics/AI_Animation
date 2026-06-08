"""
S002 — ByteDance **Seedance 2.0** image-to-video (`bytedance/seedance-2.0/image-to-video`).

Uses the same default **start frame** and **motion prompt** as `generate_s002_kling_i2v.py`.
Fal schema: **`image_url`** (uploaded local PNG/JPEG), **`prompt`**, optional **`duration`** (string
`"4"`–`"15"` or `"auto"`), **`resolution`** (`480p`/`720p`), **`aspect_ratio`**, **`generate_audio`**.

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

SHOT_ID = "S002"
MODEL_STANDARD = "bytedance/seedance-2.0/image-to-video"
MODEL_FAST = "bytedance/seedance-2.0/fast/image-to-video"

DEFAULT_START = (
    ROOT / "Tests" / "Final" / "S002_nano-banana-2-edit_20260326T094158Z.png"
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

# Motion-only; same beats as Kling S002 script (camp wide, no fourth-wall).
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
    "No one looks into the lens. "
    "Ambient forest day audio: soft wind in trees, campfire crackle and thin smoke hiss, light cloth rustle, "
    "ember pops when the fire flares; no speech, no dialogue, no singing, no music score, no voiceover."
)


def main() -> int:
    parser = argparse.ArgumentParser(description="S002 → Seedance 2.0 image-to-video")
    parser.add_argument(
        "--start-image",
        type=Path,
        default=DEFAULT_START,
        help=f"Local PNG/JPEG/WebP (default: {DEFAULT_START})",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help=f"Use {MODEL_FAST} instead of standard",
    )
    parser.add_argument(
        "--duration",
        choices=DURATION_CHOICES,
        default="5",
        help='Clip length (Fal string enum; default "5")',
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
        help="Set generate_audio true (Seedance may add sync audio/SFX; default off)",
    )
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument(
        "--end-image",
        type=Path,
        default=None,
        help="Optional last frame image (uploaded as end_image_url)",
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
