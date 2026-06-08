"""
S006A — **insert** MCU: **Fern** by campfire addresses **Frieren** (lip-sync bridge between **S005** letter read and **S006** MS debate).

**No manga panel.** Multi-reference edit:
  image 1 = approved **S006** camp master (layout, tree, fire, lighting)
  image 2 = approved **S005** Fern still (face, hair, wardrobe identity)

**Same prompt** for every backend: `S006A_EDIT_LEAD_IN` + `S006A_PROMPT_FLUX`.

- **Default: Nano Banana 2** `fal-ai/nano-banana-2/edit`.
- **Legacy:** `fal-ai/flux-2-pro/edit` — `--model flux-2-pro-edit`.
- **`--model both`** — one upload pair, Flux then Nano Banana.

Defaults: `--camp-ref` Tests/Final/S006 still, `--fern-ref` Tests/Final/S005 still.
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
    S006A_PROMPT_FLUX,
    assert_model_allowed,
    download_file,
    extension_from_url,
    image_url_from_result,
    read_fal_key,
)

SHOT_ID = "S006A"

DEFAULT_CAMP_REF = (
    ROOT / "Tests" / "Final" / "S006_nano-banana-2-edit_20260330T035743Z.png"
)
DEFAULT_FERN_REF = (
    ROOT / "Tests" / "Final" / "S005_nano-banana-2-edit_20260330T034325Z.png"
)

FLUX_PRO_EDIT_SLUG = "flux-2-pro-edit"
FLUX_PRO_EDIT_MODEL_ID = "fal-ai/flux-2-pro/edit"
NANO_BANANA_2_EDIT_SLUG = "nano-banana-2-edit"
NANO_BANANA_2_EDIT_MODEL_ID = "fal-ai/nano-banana-2/edit"

S006A_EDIT_LEAD_IN = (
    "**Two** uploads in **order**: **image 1** = approved **S006 camp master** — wins **tree**, **campfire**, **forest floor**, **Frieren-at-tree** placement, **Northern daylight**, and **left-right camp geography**; "
    "**image 2** = approved **S005 Fern** still — wins **Fern face**, **purple hair**, **butterfly ornament**, **gray jacket**, **blue braided scarf**, and **close-shot TV-anime finish** only. "
    "**Reframe** to a **medium close-up** on **Fern seated by the campfire** (same fire seat as image 1) — **face and mouth fully visible** for dialogue, **eyes toward Frieren** at the tree; "
    "**Frieren** stays **smaller in soft background left** at the tree — **do not mirror**, **do not** pull back to **S006** full MS width. "
    "**Remove** speech balloons, halftone, gutters, lettering, **Lernen memory portrait**, and **letter** props. "
    "Bridge insert between **S005** and **S006** — Fern speaks to Frieren at camp. "
)

S006A_EDIT_PROMPT = S006A_EDIT_LEAD_IN + S006A_PROMPT_FLUX


def main() -> int:
    parser = argparse.ArgumentParser(
        description="S006A Fern MCU bridge — multi-ref S006 camp + S005 Fern; Nano Banana 2 default.",
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
        "--camp-ref",
        type=Path,
        default=DEFAULT_CAMP_REF,
        help=f"S006 camp master (default: {DEFAULT_CAMP_REF.name})",
    )
    parser.add_argument(
        "--fern-ref",
        type=Path,
        default=DEFAULT_FERN_REF,
        help=f"S005 Fern identity ref (default: {DEFAULT_FERN_REF.name})",
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
        default="2K",
        help="Nano Banana only (default 2K for lip-sync face detail)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional RNG seed for reproducibility",
    )
    args = parser.parse_args()
    camp_path = args.camp_ref.resolve()
    fern_path = args.fern_ref.resolve()

    if args.image_size == "1280x720":
        flux_size: dict[str, int] | str = {"width": 1280, "height": 720}
    elif args.image_size == "1920x1080":
        flux_size = {"width": 1920, "height": 1080}
    else:
        flux_size = "landscape_16_9"

    flux_args: dict = {
        "prompt": S006A_EDIT_PROMPT,
        "image_size": flux_size,
        "enable_safety_checker": True,
        "output_format": "png",
        "safety_tolerance": "2",
    }
    if args.seed is not None:
        flux_args["seed"] = args.seed

    nano_args: dict = {
        "prompt": S006A_EDIT_PROMPT,
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

    for label, path in (("camp-ref", camp_path), ("fern-ref", fern_path)):
        if not path.is_file():
            print(f"{label} not found: {path}", file=sys.stderr)
            return 1

    print(f"Uploading camp master: {camp_path}", flush=True)
    camp_url = fal_client.upload_file(str(camp_path))
    print(f"Camp URL: {camp_url}", flush=True)

    print(f"Uploading Fern identity ref: {fern_path}", flush=True)
    fern_url = fal_client.upload_file(str(fern_path))
    print(f"Fern URL: {fern_url}", flush=True)

    image_urls_list = [camp_url, fern_url]

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "outputs" / "fal"
    tests_dir = ROOT / "Tests"
    out_dir.mkdir(parents=True, exist_ok=True)

    meta_path = out_dir / f"{SHOT_ID}_ref_edit_meta_{ts}.json"
    meta_path.write_text(
        json.dumps(
            {
                "model_choice": args.model_choice,
                "camp_ref_local": str(camp_path),
                "camp_ref_upload_url": camp_url,
                "fern_ref_local": str(fern_path),
                "fern_ref_upload_url": fern_url,
                "image_urls_order": "camp_master_then_fern_identity",
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
        arguments["image_urls"] = image_urls_list
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
