"""
S076 — hero-party meadow panel → image edit on Fal.

**Same prompt** always: `S076_EDIT_LEAD_IN` + `S076_PROMPT_FLUX`.

- **Default:** `fal-ai/nano-banana-2/edit` — `--model nano-banana-2-edit` (same prompt + `image_urls`).
- **Legacy:** `fal-ai/flux-2-pro/edit`; optional `--with-flex` also runs `flux-2-flex/edit`.

Default reference: `panels/eng/panel_s076.png` (wide flower-field panel). Pass `--ref` for full `Frierien-chapter081/016.jpg` or another crop.

Saves JSON under outputs/fal/ and images under Tests/.
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
    S076_PROMPT_FLUX,
    assert_model_allowed,
    download_file,
    extension_from_url,
    image_url_from_result,
    read_fal_key,
)

SHOT_ID = "S076"

DEFAULT_REF = PANELS_ENG / "panel_s076.png"

# FLUX.2 edit: first sentences should state what the model should do to the uploaded image and what to preserve (BFL image-editing guide).
S076_EDIT_LEAD_IN = (
    "Using the uploaded reference image as the layout guide, transform it into one finished fantasy anime frame. "
    "The reference wins on **composition**: keep the same figure positions, distances, facing, and gestures as the panel — the text prompt only refines material, lighting, and gentle color; "
    "never replace the scene with a new hero pose sheet because of wardrobe words. "
    "Preserve wide scale, forest clearing silhouette, and depth order; do not collapse the cast into a flat front row. "
    "Remove ink halftone, panel borders, gutters, speech balloons, and every bit of lettering so only the painted scene remains. "
)

S076_EDIT_PROMPT = S076_EDIT_LEAD_IN + S076_PROMPT_FLUX

FLUX_PRO_EDIT_SLUG = "flux-2-pro-edit"
FLUX_PRO_EDIT_MODEL_ID = "fal-ai/flux-2-pro/edit"
NANO_BANANA_2_EDIT_SLUG = "nano-banana-2-edit"
NANO_BANANA_2_EDIT_MODEL_ID = "fal-ai/nano-banana-2/edit"

PRO_MODEL: tuple[str, str, dict] = (
    FLUX_PRO_EDIT_SLUG,
    FLUX_PRO_EDIT_MODEL_ID,
    {
        "prompt": S076_EDIT_PROMPT,
        "image_size": {"width": 1280, "height": 720},
        "enable_safety_checker": True,
        "output_format": "png",
        "safety_tolerance": "2",
    },
)

FLEX_MODEL: tuple[str, str, dict] = (
    "flux-2-flex-edit",
    "fal-ai/flux-2-flex/edit",
    {
        "prompt": S076_EDIT_PROMPT,
        "guidance_scale": 3.5,
        "num_inference_steps": 28,
        "image_size": {"width": 1280, "height": 720},
        "enable_safety_checker": True,
        "output_format": "png",
        "safety_tolerance": "2",
    },
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="S076 panel → image edit: Flux 2 Pro (optional Flex) or Nano Banana 2; same S076 prompt.",
        epilog="Nano Banana: https://fal.ai/models/fal-ai/nano-banana-2/edit/api",
    )
    parser.add_argument(
        "--model",
        dest="model_choice",
        choices=("flux-2-pro-edit", "nano-banana-2-edit"),
        default="nano-banana-2-edit",
        help="Edit backend (default: Nano Banana 2; --with-flex ignored for nano-banana)",
    )
    parser.add_argument(
        "--ref",
        type=Path,
        default=DEFAULT_REF,
        help=f"Reference panel image (default: {DEFAULT_REF})",
    )
    parser.add_argument(
        "--with-flex",
        action="store_true",
        help="Also run fal-ai/flux-2-flex/edit (Flux backend only)",
    )
    parser.add_argument(
        "--aspect-ratio",
        dest="aspect_ratio",
        default="16:9",
        help='Nano Banana 2 only (default "16:9").',
    )
    parser.add_argument(
        "--resolution",
        dest="resolution",
        choices=("0.5K", "1K", "2K", "4K"),
        default="1K",
        help="Nano Banana 2 only (default 1K)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional RNG seed (supported by both backends where applicable)",
    )
    args = parser.parse_args()
    ref_path = args.ref.resolve()

    if args.model_choice == "nano-banana-2-edit":
        nano_args: dict = {
            "prompt": S076_EDIT_PROMPT,
            "aspect_ratio": args.aspect_ratio,
            "output_format": "png",
            "safety_tolerance": "4",
            "resolution": args.resolution,
            "limit_generations": True,
        }
        if args.seed is not None:
            nano_args["seed"] = args.seed
        models: list[tuple[str, str, dict]] = [
            (NANO_BANANA_2_EDIT_SLUG, NANO_BANANA_2_EDIT_MODEL_ID, nano_args),
        ]
        if args.with_flex:
            print("Note: --with-flex ignored when using nano-banana-2-edit.", flush=True)
        meta_extra = {"model_choice": "nano-banana-2-edit", "aspect_ratio": args.aspect_ratio, "resolution": args.resolution}
    else:
        pro_entry: tuple[str, str, dict] = (
            PRO_MODEL[0],
            PRO_MODEL[1],
            dict(PRO_MODEL[2]),
        )
        if args.seed is not None:
            pro_entry[2]["seed"] = args.seed
        models = [pro_entry]
        if args.with_flex:
            flex_entry: tuple[str, str, dict] = (
                FLEX_MODEL[0],
                FLEX_MODEL[1],
                dict(FLEX_MODEL[2]),
            )
            if args.seed is not None:
                flex_entry[2]["seed"] = args.seed
            models.append(flex_entry)
        meta_extra = {
            "model_choice": "flux-2-pro-edit",
            "with_flex": bool(args.with_flex),
            "seed": args.seed,
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
            "Add panels\\panel_s076.png or pass --ref path\\to\\crop.png",
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
                "reference_local": str(ref_path),
                "reference_upload_url": image_url,
                **meta_extra,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
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
