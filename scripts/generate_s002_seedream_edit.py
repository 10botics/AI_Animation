"""
S002 — **ByteDance Seedream 5.0 Lite** image edit (`fal-ai/bytedance/seedream/v5/lite/edit`).

This endpoint is **image → image** (not video). To get an **MP4**, pass **`--chain-kling`**: after the
edited still is saved, this script runs **`generate_s002_kling_i2v.py`** with that PNG as `--start-image`.

- Default ref: `panels/eng/panel_s002.png` (same beat as other S002 edit scripts).
- Prompt: same combined string as **`generate_s002_ref_edit.py`** (lead-in + `S002_PROMPT_FLUX`).
- Outputs: `Tests/S002_seedream-v5-lite-edit_<ts>.png` (+ Fal JSON under `outputs/fal/`).

Usage:
  cd scripts
  python generate_s002_seedream_edit.py
  python generate_s002_seedream_edit.py --chain-kling
  python generate_s002_seedream_edit.py --ref "..\\\\panels\\\\panel_s002.png" --image-size landscape_16_9
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import fal_client

from panel_paths import PANELS_ENG
from fal_common import (
    ROOT,
    S002_PROMPT_FLUX,
    assert_model_allowed,
    download_file,
    extension_from_url,
    image_url_from_result,
    read_fal_key,
)

# Reuse wording from generate_s002_ref_edit.py
S002_EDIT_LEAD_IN = (
    "Using the uploaded reference image as the layout guide, transform it into one finished fantasy anime frame. "
    "The reference wins **composition**: **three people**, **forest clearing**, **central campfire**, same poses, facing, depth layering, and **left-right arrangement** as the upload; **do not mirror** the scene horizontally. "
    "Following text assigns **Fern / Frieren / Stark** wardrobe and storyboard S002 roles while preserving that layout — refine anime color and fabric only; **no fourth traveler**, no biome swap. "
    "Remove ink halftone, panel borders, gutters, **narrative text boxes**, speech balloons, and lettering; only the painted scene remains. "
)

S002_EDIT_PROMPT = S002_EDIT_LEAD_IN + S002_PROMPT_FLUX

SHOT_ID = "S002"
MODEL_ID = "fal-ai/bytedance/seedream/v5/lite/edit"
DEFAULT_REF = PANELS_ENG / "panel_s002.png"

IMAGE_SIZE_CHOICES = (
    "square_hd",
    "square",
    "portrait_4_3",
    "portrait_16_9",
    "landscape_4_3",
    "landscape_16_9",
    "auto_2K",
    "auto_3K",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="S002 panel → Seedream 5 Lite edit; optional Kling I2V chain")
    parser.add_argument("--ref", type=Path, default=DEFAULT_REF, help=f"Primary reference (default: {DEFAULT_REF})")
    parser.add_argument(
        "--extra-ref",
        type=Path,
        nargs="*",
        default=(),
        help="Optional extra local images → additional image_urls (max 10 total on API)",
    )
    parser.add_argument(
        "--image-size",
        choices=IMAGE_SIZE_CHOICES,
        default="landscape_16_9",
        help="Seedream output sizing preset (default landscape_16_9)",
    )
    parser.add_argument("--num-images", type=int, default=1, dest="num_images")
    parser.add_argument("--max-images", type=int, default=1, dest="max_images")
    parser.add_argument(
        "--prompt",
        default=S002_EDIT_PROMPT,
        help="Override edit prompt (default: full S002 anime-edit prompt)",
    )
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument(
        "--disable-safety-checker",
        action="store_true",
        help="Set enable_safety_checker false (default on)",
    )
    parser.add_argument(
        "--client-timeout",
        type=float,
        default=600.0,
        help="fal_client.subscribe client_timeout seconds (default 600)",
    )
    parser.add_argument(
        "--chain-kling",
        action="store_true",
        help="After saving the still, run generate_s002_kling_i2v.py --start-image <that png>",
    )
    parser.add_argument(
        "--kling-duration",
        choices=("5", "10"),
        default="5",
        help='With --chain-kling: Kling duration (default "5")',
    )
    parser.add_argument(
        "--kling-audio",
        action="store_true",
        help="With --chain-kling: pass --audio to Kling (higher cost)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print arguments and exit before Fal")
    args = parser.parse_args()

    assert_model_allowed(MODEL_ID)

    key = read_fal_key()
    if not key:
        print("Missing FAL_KEY — set in .env at project root.", file=sys.stderr)
        return 1

    ref_path = args.ref.resolve()
    if not ref_path.is_file():
        print(f"Reference not found: {ref_path}", file=sys.stderr)
        return 1

    os.environ["FAL_KEY"] = key

    image_urls: list[str] = []
    print(f"Uploading primary ref: {ref_path}", flush=True)
    image_urls.append(fal_client.upload_file(str(ref_path)))
    for p in args.extra_ref:
        pr = p.resolve()
        if not pr.is_file():
            print(f"Skipping missing --extra-ref: {pr}", file=sys.stderr)
            continue
        print(f"Uploading extra ref: {pr}", flush=True)
        image_urls.append(fal_client.upload_file(str(pr)))
    if len(image_urls) > 10:
        print("Note: API uses last 10 image_urls only; truncating.", flush=True)
        image_urls = image_urls[-10:]

    arguments: dict = {
        "prompt": args.prompt.strip(),
        "image_urls": image_urls,
        "image_size": args.image_size,
        "num_images": max(1, args.num_images),
        "max_images": max(1, args.max_images),
        "enable_safety_checker": not args.disable_safety_checker,
    }
    if args.seed is not None:
        arguments["seed"] = int(args.seed)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "outputs" / "fal"
    tests_dir = ROOT / "Tests"
    out_dir.mkdir(parents=True, exist_ok=True)
    tests_dir.mkdir(parents=True, exist_ok=True)

    meta_path = out_dir / f"{SHOT_ID}_seedream_v5_lite_meta_{ts}.json"
    meta_path.write_text(
        json.dumps(
            {
                "shot": SHOT_ID,
                "model_id": MODEL_ID,
                "reference_local": str(ref_path),
                "image_urls": image_urls,
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
            client_timeout=args.client_timeout,
        )
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    log_path = out_dir / f"{SHOT_ID}_seedream_v5_lite_{ts}.json"
    log_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(f"Log: {log_path}", flush=True)

    url = image_url_from_result(result)
    if not url:
        print(f"No image URL in response", file=sys.stderr)
        return 1

    ext = extension_from_url(url)
    image_path = tests_dir / f"{SHOT_ID}_seedream-v5-lite-edit_{ts}{ext}"
    download_file(url, image_path)
    print(f"Saved still: {image_path}", flush=True)

    if not args.chain_kling:
        print(
            "\nSeedream returned a **still image** only. For video, run:\n"
            f'  python generate_s002_kling_i2v.py --start-image "{image_path}"\n'
            "Or re-run this script with --chain-kling",
            flush=True,
        )
        return 0

    kling_script = Path(__file__).resolve().parent / "generate_s002_kling_i2v.py"
    cmd = [
        sys.executable,
        str(kling_script),
        "--start-image",
        str(image_path),
        "--duration",
        args.kling_duration,
    ]
    if args.kling_audio:
        cmd.append("--audio")
    print(f"\nChaining Kling I2V: {' '.join(cmd)}", flush=True)
    try:
        r = subprocess.run(cmd, check=False)
    except OSError as e:
        print(f"Kling subprocess failed: {e}", file=sys.stderr)
        return 1
    return int(r.returncode != 0)


if __name__ == "__main__":
    raise SystemExit(main())
