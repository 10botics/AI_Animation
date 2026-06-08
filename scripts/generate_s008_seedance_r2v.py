"""
S008 — ByteDance **Seedance 2.0 reference-to-video** (`bytedance/seedance-2.0/reference-to-video`).

Uses **`image_urls`** + **@Image1** (and optional **@Image2**) instead of I2V `image_url`.
Default: approved Final as @Image1; optional `--camp-ref` adds S002 Final for camp palette only.

**Stage_02:** present MS B3 — daytime camp grimoire trio.

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

from panel_paths import PANELS_ENG
from fal_common import (
    ROOT,
    assert_model_allowed,
    download_file,
    extension_from_url,
    read_fal_key,
    video_url_from_result,
)

SHOT_ID = "S008"
MODEL_STANDARD = "bytedance/seedance-2.0/reference-to-video"
MODEL_FAST = "bytedance/seedance-2.0/fast/reference-to-video"

DEFAULT_IMAGE1 = ROOT / "Tests" / "Final" / "S008_nano-banana-2-edit_20260330T042818Z.png"
DEFAULT_CAMP_REF = ROOT / "Tests" / "Final" / "S002_nano-banana-2-edit_20260326T094158Z.png"
DEFAULT_PANEL_REF = PANELS_ENG / "panel_s008.png"

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

# @Image1 = hero still; optional @Image2 = camp palette or panel layout (see --camp-ref / --panel-ref)
R2V_PROMPT_ONE_REF = (
    "Fantasy anime television production shot, PG adventure, locked-off medium shot, 35mm soft grain, "
    "2.39:1, daytime Northern forest camp, overcast diffused canopy light. "
    "Use @Image1 as the exact composition, character positions, and wardrobe reference; "
    "animate @Image1 with near-static motion only. "
    "Figure on the right seated with open illustrated spellbook: only page edge flutter and hair and coat drift, "
    "no turn to camera, no mouth motion. "
    "Center figure back to camera: slight scarf and purple hair movement in breeze only, does not take the book. "
    "Rear left figure: nearly frozen, tiny shoulder slump only, stays at the edge of frame. "
    "Do not reframe wide, do not mirror left-right order. "
    "Gentle wind in leaves, one continuous beat, no cuts, no on-screen text, no manga texture, no fourth wall."
)

R2V_PROMPT_CAMP_REF = (
    "Fantasy anime television production shot, PG adventure, locked-off medium shot, 35mm soft grain, "
    "2.39:1, daytime Northern forest camp. "
    "Use @Image1 for exact character layout, props, and framing; use @Image2 only for cool forest camp "
    "daylight and color grade, not for character poses. "
    "Animate @Image1 with near-static motion only: page flutter and cloth drift on the seated figure with the book; "
    "center back-to-camera figure scarf and hair drift only; rear-left figure nearly frozen. "
    "No mouth motion, no turn to camera, no interaction beat between figures. "
    "Tripod-locked, no zoom, one continuous beat, no cuts, no text, no manga halftone, no fourth wall."
)

R2V_PROMPT_PANEL_REF = (
    "Fantasy anime television production shot, PG adventure, locked-off medium shot, 35mm soft grain, "
    "2.39:1. Use @Image2 only for left-right blocking and who holds the book; render finished anime like @Image1. "
    "Match @Image1 lighting and paint style. Near-static motion: book pages, hair, scarf, leaves in wind only. "
    "No mouth motion, no cuts, no on-screen text, no manga panel borders or halftone in the output."
)

AUDIO_TAIL = (
    " Ambient forest day: soft wind in trees, distant campfire feel, light cloth rustle; "
    "no speech, no dialogue, no singing, no music score."
)


def build_prompt(*, camp_ref: bool, panel_ref: bool, audio: bool, custom: str | None) -> str:
    if custom:
        text = custom.strip()
    elif panel_ref:
        text = R2V_PROMPT_PANEL_REF
    elif camp_ref:
        text = R2V_PROMPT_CAMP_REF
    else:
        text = R2V_PROMPT_ONE_REF
    if audio and AUDIO_TAIL.strip() not in text:
        text = text + AUDIO_TAIL
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description="S008 → Seedance 2.0 reference-to-video")
    parser.add_argument("--image1", type=Path, default=DEFAULT_IMAGE1, help="Primary ref (@Image1)")
    parser.add_argument(
        "--camp-ref",
        action="store_true",
        help="Add S002 camp Final as @Image2 (palette only)",
    )
    parser.add_argument(
        "--panel-ref",
        action="store_true",
        help="Add panels/eng/panel_s008.png as @Image2 (layout only; higher manga risk)",
    )
    parser.add_argument("--fast", action="store_true", help=f"Use {MODEL_FAST}")
    parser.add_argument("--duration", choices=DURATION_CHOICES, default="5")
    parser.add_argument("--resolution", choices=("480p", "720p", "1080p"), default="720p")
    parser.add_argument(
        "--aspect-ratio",
        dest="aspect_ratio",
        choices=("auto", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16"),
        default="16:9",
    )
    parser.add_argument("--audio", action="store_true", help="generate_audio true (default off)")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--client-timeout", type=float, default=900.0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--prompt", default=None, help="Override motion prompt")
    args = parser.parse_args()

    if args.camp_ref and args.panel_ref:
        print("Use only one of --camp-ref or --panel-ref.", file=sys.stderr)
        return 1

    model_id = MODEL_FAST if args.fast else MODEL_STANDARD
    assert_model_allowed(model_id)

    key = read_fal_key()
    if not key:
        print("Missing FAL_KEY — set in .env at project root.", file=sys.stderr)
        return 1

    image1_path = args.image1.resolve()
    if not image1_path.is_file():
        print(f"image1 not found: {image1_path}", file=sys.stderr)
        return 1

    local_refs: list[Path] = [image1_path]
    if args.camp_ref:
        camp = DEFAULT_CAMP_REF.resolve()
        if not camp.is_file():
            print(f"Camp ref not found: {camp}", file=sys.stderr)
            return 1
        local_refs.append(camp)
    elif args.panel_ref:
        panel = DEFAULT_PANEL_REF.resolve()
        if not panel.is_file():
            print(f"Panel ref not found: {panel}", file=sys.stderr)
            return 1
        local_refs.append(panel)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "outputs" / "fal"
    video_dir = ROOT / "outputs" / "video"
    out_dir.mkdir(parents=True, exist_ok=True)
    video_dir.mkdir(parents=True, exist_ok=True)

    os.environ["FAL_KEY"] = key

    image_urls: list[str] = []
    for i, p in enumerate(local_refs, start=1):
        print(f"Uploading @Image{i}: {p}", flush=True)
        image_urls.append(fal_client.upload_file(str(p)))
    for i, u in enumerate(image_urls, start=1):
        print(f"@Image{i}: {u}", flush=True)

    prompt_text = build_prompt(
        camp_ref=args.camp_ref,
        panel_ref=args.panel_ref,
        audio=bool(args.audio),
        custom=args.prompt,
    )

    arguments: dict = {
        "prompt": prompt_text,
        "image_urls": image_urls,
        "resolution": args.resolution,
        "duration": args.duration,
        "aspect_ratio": args.aspect_ratio,
        "generate_audio": bool(args.audio),
    }
    if args.seed is not None:
        arguments["seed"] = int(args.seed)

    variant = "seedance-2-fast-r2v" if args.fast else "seedance-2-r2v"
    meta_path = out_dir / f"{SHOT_ID}_{variant}_meta_{ts}.json"
    meta_path.write_text(
        json.dumps(
            {
                "shot": SHOT_ID,
                "model_id": model_id,
                "image_refs_local": [str(p) for p in local_refs],
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
