"""
S010 — Golden Weise **ridge overlook** (default ref: `panels/eng/panel_s010.png`).

**Same prompt** always: `S010_EDIT_LEAD_IN` + `S010_PROMPT_FLUX`.

- **`--model nano-banana-2-edit`** (default): `fal-ai/nano-banana-2/edit`.
- **`--model flux-2-pro-edit`**: `fal-ai/flux-2-pro/edit` (legacy); optional **`--with-flex`** adds `flux-2-flex/edit`.
- **`--model both`**: one upload → **Flux Pro** + **Nano Banana** (Flex **not** included; `--with-flex` ignored).

Pass `--ref` to override (e.g. full `003.jpg`). Saves JSON under outputs/fal/ and images under Tests/.
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
    S010_PROMPT_FLUX,
    assert_model_allowed,
    download_file,
    extension_from_url,
    image_url_from_result,
    read_fal_key,
)

SHOT_ID = "S010"

DEFAULT_REF = PANELS_ENG / "panel_s010.png"

FLUX_PRO_EDIT_SLUG = "flux-2-pro-edit"
FLUX_PRO_EDIT_MODEL_ID = "fal-ai/flux-2-pro/edit"
NANO_BANANA_2_EDIT_SLUG = "nano-banana-2-edit"
NANO_BANANA_2_EDIT_MODEL_ID = "fal-ai/nano-banana-2/edit"

# Edit models: composition from image_urls; prompt steers color, anime look, story constraints.
S010_EDIT_LEAD_IN = (
    "Image-guided edit: keep the **same wide ridge layout** and **left-to-right** trio order from **`panel_s010.png`**. "
    "**Orientation locked:** camera **behind** the party — **all three backs to the viewer**, **looking out** at the **distant golden city** — "
    "**do not** swing them to **face the camera** or add a **frontal hero** turnaround. "
    "Redraw as polished fantasy anime TV key art — full color, soft cel shading, no manga screentone or panel frame. "
)

S010_EDIT_PROMPT = S010_EDIT_LEAD_IN + S010_PROMPT_FLUX

FLUX_IMAGE_SIZE = {"width": 1280, "height": 720}

PRO_MODEL: tuple[str, str, dict] = (
    FLUX_PRO_EDIT_SLUG,
    FLUX_PRO_EDIT_MODEL_ID,
    {
        "prompt": S010_EDIT_PROMPT,
        "image_size": FLUX_IMAGE_SIZE,
        "enable_safety_checker": True,
        "output_format": "png",
        "safety_tolerance": "2",
    },
)

FLEX_MODEL: tuple[str, str, dict] = (
    "flux-2-flex-edit",
    "fal-ai/flux-2-flex/edit",
    {
        "prompt": S010_EDIT_PROMPT,
        "guidance_scale": 3.5,
        "num_inference_steps": 28,
        "image_size": FLUX_IMAGE_SIZE,
        "enable_safety_checker": True,
        "output_format": "png",
        "safety_tolerance": "2",
    },
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="S010 panel → Flux Pro (optional Flex) and/or Nano Banana 2; same S010 prompt.",
        epilog="Nano Banana: https://fal.ai/models/fal-ai/nano-banana-2/edit/api",
    )
    parser.add_argument(
        "--model",
        dest="model_choice",
        choices=("flux-2-pro-edit", "nano-banana-2-edit", "both"),
        default="nano-banana-2-edit",
        help="nano-banana-2-edit (default), flux-2-pro-edit, or both (Pro + Nano; no Flex)",
    )
    parser.add_argument(
        "--ref",
        type=Path,
        default=DEFAULT_REF,
        help=f"Reference image (default: {DEFAULT_REF})",
    )
    parser.add_argument(
        "--with-flex",
        action="store_true",
        help="Also run fal-ai/flux-2-flex/edit (when --model is flux-2-pro-edit only)",
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
        help="Optional RNG seed",
    )
    args = parser.parse_args()
    ref_path = args.ref.resolve()

    flux_pro: dict = dict(PRO_MODEL[2])
    if args.seed is not None:
        flux_pro["seed"] = args.seed

    nano_args: dict = {
        "prompt": S010_EDIT_PROMPT,
        "aspect_ratio": args.aspect_ratio,
        "output_format": "png",
        "safety_tolerance": "4",
        "resolution": args.resolution,
        "limit_generations": True,
    }
    if args.seed is not None:
        nano_args["seed"] = args.seed

    models: list[tuple[str, str, dict]]

    if args.model_choice == "both":
        if args.with_flex:
            print("Note: --with-flex ignored when using --model both (use Flux-only mode for Flex).", flush=True)
        models = [
            (FLUX_PRO_EDIT_SLUG, FLUX_PRO_EDIT_MODEL_ID, flux_pro),
            (NANO_BANANA_2_EDIT_SLUG, NANO_BANANA_2_EDIT_MODEL_ID, nano_args),
        ]
        meta_extra = {
            "flux_image_size": FLUX_IMAGE_SIZE,
            "nano_aspect_ratio": args.aspect_ratio,
            "nano_resolution": args.resolution,
        }
    elif args.model_choice == "nano-banana-2-edit":
        if args.with_flex:
            print("Note: --with-flex ignored for nano-banana-2-edit.", flush=True)
        models = [(NANO_BANANA_2_EDIT_SLUG, NANO_BANANA_2_EDIT_MODEL_ID, nano_args)]
        meta_extra = {"aspect_ratio": args.aspect_ratio, "resolution": args.resolution}
    else:
        models = [(FLUX_PRO_EDIT_SLUG, FLUX_PRO_EDIT_MODEL_ID, flux_pro)]
        if args.with_flex:
            flex_d = dict(FLEX_MODEL[2])
            if args.seed is not None:
                flex_d["seed"] = args.seed
            models.append((FLEX_MODEL[0], FLEX_MODEL[1], flex_d))
        meta_extra = {
            "flux_image_size": FLUX_IMAGE_SIZE,
            "with_flex": bool(args.with_flex),
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
            "Add panels\\panel_s010.png or pass --ref path\\to\\panel.png",
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
