"""
S006 — **present** MS: **Frieren** at tree + **Fern** by **fire** — **camera locked** to `panel_s006.png` (`002.jpg` bottom tier). **Stark** optional at edge only if no reframe.

**Same prompt** for every backend: `S006_EDIT_LEAD_IN` + `S006_PROMPT_FLUX`.

- **Default: Nano Banana 2** `fal-ai/nano-banana-2/edit`.
- **Legacy:** `fal-ai/flux-2-pro/edit` — `--model flux-2-pro-edit`.
- **`--model both`** — one upload, Flux then Nano Banana.

Default ref: **`panels/panel_s006.png`**. Pass `--ref` to override.
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
    S006_PROMPT_FLUX,
    assert_model_allowed,
    download_file,
    extension_from_url,
    image_url_from_result,
    read_fal_key,
)

SHOT_ID = "S006"

DEFAULT_REF = ROOT / "panels" / "panel_s006.png"

FLUX_PRO_EDIT_SLUG = "flux-2-pro-edit"
FLUX_PRO_EDIT_MODEL_ID = "fal-ai/flux-2-pro/edit"
NANO_BANANA_2_EDIT_SLUG = "nano-banana-2-edit"
NANO_BANANA_2_EDIT_MODEL_ID = "fal-ai/nano-banana-2/edit"

S006_EDIT_LEAD_IN = (
    "Using the uploaded **`panel_s006.png`** (Weise **camp** debate), transform it into one finished **fantasy anime television** illustration. "
    "**Camera lock:** **preserve** the panel’s **lens, framing, subject scale, and angle** — **do not mirror** horizontally, **do not** pull back into a **wide establishing** shot, **do not** reframe to match **S002** wide coverage. "
    "The reference **locks** **Frieren** at the **tree** with **book** and **Fern** by the **fire** — **same composition** as the crop. "
    "**Optional:** **Stark** **only** as a **small edge** read if it fits **without** changing camera; **never** prioritize widening over **Frieren**/**Fern** framing. "
    "**Remove** speech balloons, halftone, gutters, and lettering. "
    "Refine into full **cel-shaded anime**, cool Northern daylight with **warm fire accents**. "
)

S006_EDIT_PROMPT = S006_EDIT_LEAD_IN + S006_PROMPT_FLUX


def main() -> int:
    parser = argparse.ArgumentParser(
        description="S006 panel → Flux 2 Pro and/or Nano Banana 2; same prompt string.",
        epilog="Nano Banana: https://fal.ai/models/fal-ai/nano-banana-2/edit/api",
    )
    parser.add_argument(
        "--model",
        dest="model_choice",
        choices=("flux-2-pro-edit", "nano-banana-2-edit", "both"),
        default="nano-banana-2-edit",
        help="Edit backend: Flux, Nano Banana (default), or both in one run",
    )
    parser.add_argument(
        "--ref",
        type=Path,
        default=DEFAULT_REF,
        help=f"Reference image (default: {DEFAULT_REF})",
    )
    parser.add_argument(
        "--image-size",
        dest="image_size",
        choices=("landscape_16_9", "1280x720", "1920x1080"),
        default="landscape_16_9",
        help="Flux only: output 16:9 preset or fixed WxH",
    )
    parser.add_argument(
        "--aspect-ratio",
        dest="aspect_ratio",
        default="16:9",
        help='Nano Banana only (default "16:9").',
    )
    parser.add_argument(
        "--resolution",
        dest="resolution",
        choices=("0.5K", "1K", "2K", "4K"),
        default="1K",
        help="Nano Banana only (default 1K)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional RNG seed for reproducibility",
    )
    args = parser.parse_args()
    ref_path = args.ref.resolve()

    if args.image_size == "1280x720":
        flux_size: dict[str, int] | str = {"width": 1280, "height": 720}
    elif args.image_size == "1920x1080":
        flux_size = {"width": 1920, "height": 1080}
    else:
        flux_size = "landscape_16_9"

    flux_args: dict = {
        "prompt": S006_EDIT_PROMPT,
        "image_size": flux_size,
        "enable_safety_checker": True,
        "output_format": "png",
        "safety_tolerance": "2",
    }
    if args.seed is not None:
        flux_args["seed"] = args.seed

    nano_args: dict = {
        "prompt": S006_EDIT_PROMPT,
        "aspect_ratio": args.aspect_ratio,
        "output_format": "png",
        "safety_tolerance": "4",
        "resolution": args.resolution,
        "limit_generations": True,
    }
    if args.seed is not None:
        nano_args["seed"] = args.seed

    if args.model_choice == "flux-2-pro-edit":
        models: list[tuple[str, str, dict]] = [
            (FLUX_PRO_EDIT_SLUG, FLUX_PRO_EDIT_MODEL_ID, flux_args),
        ]
        meta_extra = {"flux_image_size": flux_size}
    elif args.model_choice == "nano-banana-2-edit":
        models = [(NANO_BANANA_2_EDIT_SLUG, NANO_BANANA_2_EDIT_MODEL_ID, nano_args)]
        meta_extra = {
            "aspect_ratio": args.aspect_ratio,
            "resolution": args.resolution,
        }
    else:
        models = [
            (FLUX_PRO_EDIT_SLUG, FLUX_PRO_EDIT_MODEL_ID, flux_args),
            (NANO_BANANA_2_EDIT_SLUG, NANO_BANANA_2_EDIT_MODEL_ID, nano_args),
        ]
        meta_extra = {
            "flux_image_size": flux_size,
            "nano_aspect_ratio": args.aspect_ratio,
            "nano_resolution": args.resolution,
        }

    for _, mid, _ in models:
        assert_model_allowed(mid)

    key = read_fal_key()
    if not key:
        print("Missing FAL_KEY — set in .env at project root.", file=sys.stderr)
        return 1
    os.environ["FAL_KEY"] = key

    if not ref_path.is_file():
        print(
            f"Reference image not found: {ref_path}\n"
            "Add panels\\panel_s006.png or pass --ref path\\to\\crop.png",
            file=sys.stderr,
        )
        return 1

    print(f"Uploading reference: {ref_path}", flush=True)
    image_url = fal_client.upload_file(str(ref_path))
    print(f"Reference URL: {image_url}", flush=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "outputs" / "fal"
    tests_dir = ROOT / "Tests"
    out_dir.mkdir(parents=True, exist_ok=True)

    meta_path = out_dir / f"{SHOT_ID}_ref_edit_meta_{ts}.json"
    meta_path.write_text(
        json.dumps(
            {
                "model_choice": args.model_choice,
                "reference_local": str(ref_path),
                "reference_upload_url": image_url,
                "seed": args.seed,
                **meta_extra,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"backend: {args.model_choice} {meta_extra}", flush=True)
    print(f"Meta: {meta_path}", flush=True)

    summary: list[dict] = []

    for slug, model_id, base_args in models:
        arguments = dict(base_args)
        arguments["image_urls"] = [image_url]
        print(f"\n--- {slug} ({model_id}) ---", flush=True)
        try:
            result = fal_client.subscribe(
                model_id,
                arguments=arguments,
                with_logs=True,
            )
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            summary.append({"slug": slug, "model_id": model_id, "ok": False, "error": str(e)})
            continue

        log_path = out_dir / f"{SHOT_ID}_{slug}_{ts}.json"
        log_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        print(f"Log: {log_path}", flush=True)

        url = image_url_from_result(result)
        if not url:
            print("No image URL in response", file=sys.stderr)
            summary.append({"slug": slug, "model_id": model_id, "ok": False, "error": "no_url"})
            continue

        ext = extension_from_url(url)
        image_path = tests_dir / f"{SHOT_ID}_{slug}_{ts}{ext}"
        try:
            download_file(url, image_path)
            print(f"Saved: {image_path}", flush=True)
            summary.append(
                {"slug": slug, "model_id": model_id, "ok": True, "url": url, "path": str(image_path)}
            )
        except OSError as e:
            print(f"Download failed: {e}", file=sys.stderr)
            summary.append({"slug": slug, "model_id": model_id, "ok": False, "error": str(e), "url": url})

    summary_path = out_dir / f"{SHOT_ID}_ref_edit_summary_{ts}.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nSummary: {summary_path}", flush=True)
    return 0 if summary and all(s.get("ok") for s in summary) else 1


if __name__ == "__main__":
    raise SystemExit(main())
