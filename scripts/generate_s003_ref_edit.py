"""
S003 — **present** Weise **camp**: **Fern** + squirrel-in-satchel (`002.jpg` row 2).

**Variants:** `full` · `fern-only` · **`extend-camp`** (fern-only → S002 camp behind) · **`extend-camp-squirrel`** (extend-camp master → **satchel + squirrel**, **Fern looks at squirrel**).

**Optional `--squirrel-ref path.png`** with **`--variant extend-camp-squirrel`** uploads a **second** image; the model receives **`image_urls` = [camp, squirrel]** and `S003_PROMPT_FLUX_COMPOSITE_SQUIRREL` transfers the **reference squirrel's design** into the camp plate (Nano Banana and Flux both support **multi-reference** edit).

- Default **`--model nano-banana-2-edit`** (Nano Banana 2).
- **Flux 2 Pro** `fal-ai/flux-2-pro/edit` — `landscape_16_9` or `--image-size`.
- **`--model both`** — one upload, Flux then Nano Banana.

Default ref: **`panels/eng/panel_s003.png`** — both variants use this crop for **chirality** (Fern **left-facing**, bag+squirrel **right** in `full`). Nano default output **`--aspect-ratio 16:9`** to match the chapter pipeline; use **`9:16`** only if a run flips or crops badly.

Pass `--ref` to override. Saves JSON under `outputs/fal/` and images under `Tests/`.
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
    S003_PROMPT_FLUX,
    S003_PROMPT_FLUX_COMPOSITE_SQUIRREL,
    S003_PROMPT_FLUX_EXTEND_CAMP,
    S003_PROMPT_FLUX_EXTEND_CAMP_SQUIRREL,
    S003_PROMPT_FLUX_FERN_ONLY,
    assert_model_allowed,
    download_file,
    extension_from_url,
    image_url_from_result,
    read_fal_key,
)

SHOT_ID = "S003"

DEFAULT_REF = PANELS_ENG / "panel_s003.png"
# Default input for extend-camp when user omits --ref (if file exists).
DEFAULT_EXTEND_CAMP_REF = (
    ROOT / "Tests" / "S003_fernonly_nano-banana-2-edit_20260326T142928Z.png"
)
DEFAULT_EXTEND_CAMP_SQUIRREL_REF = (
    ROOT / "Tests" / "S003_extendcamp_nano-banana-2-edit_20260326T143552Z.png"
)

FLUX_PRO_EDIT_SLUG = "flux-2-pro-edit"
FLUX_PRO_EDIT_MODEL_ID = "fal-ai/flux-2-pro/edit"
NANO_BANANA_2_EDIT_SLUG = "nano-banana-2-edit"
NANO_BANANA_2_EDIT_MODEL_ID = "fal-ai/nano-banana-2/edit"

S003_EDIT_LEAD_IN_FULL = (
    "Using the uploaded **`panel_s003.png`** manga crop, transform it into one finished fantasy anime key illustration. "
    "**Chirality is mandatory (copy the ink silhouette, do not flip):** **Fern** is a **left-facing profile** — her **nose and torso aim toward the LEFT edge of the image** (same as the scan); "
    "she **sits directly on the forest floor** with her weight on the ground, **not standing**. "
    "The **open satchel with the squirrel** stays on the **ground in the RIGHT half of frame** — **same** tree and bush order left-to-right as the PNG. "
    "**No horizontal mirror, no swap** of Fern and bag regions, no camera reversal, **no right-facing profile**. "
    "Strip ink **halftone**, panel borders, gutters, **speech balloons**, and lettering. "
    "Do **not** add **Frieren**, **Stark**, or a second human. "
)

S003_EDIT_LEAD_IN_FERN_ONLY = (
    "Using the uploaded **`panel_s003.png`** crop (or a color frame **exported from this exact layout**): **only** traveler **Fern** — **no squirrel**, **no satchel or mail bag**. "
    "**Chirality is mandatory (copy the scan, do not flip):** **Fern** is **LEFT-facing profile** — **face and body toward the LEFT edge of the picture**; she **sits on the ground**, full weight on the forest floor, **not standing**. "
    "Inpaint **only the right side** of the frame into continuous leaf-strewn ground — **same** trees and shrubs **left-to-right** as the PNG, **no horizontal mirror**, **no right-facing profile**. "
    "For manga ink: strip halftone, borders, gutters, balloons, lettering; remove critter and bag, inpaint **continuous forest floor** matching surrounding leaves and earth. "
    "For an existing color render: **preserve** trees, lighting, and pose — **revise the coat sleeves and lap** so **hands are readable**. "
    "**Anatomy:** **both hands and wrists clearly visible**, resting on the lap over the skirt, relaxed natural fingers; **sleeve cuffs must not swallow the hands** — shorten or reshape puff sleeves if needed for a clean TV-anime read. "
)

S003_EDIT_LEAD_IN_EXTEND_CAMP = (
    "Image-guided **extend**: the upload is an approved **S003 fern-only** color frame. "
    "**Lock** foreground **Fern** — same silhouette, colors, pose, and framing; **do not** mirror her, **do not** add a second Fern, **do not** replace her face or outfit. "
    "**Paint** deeper midground and background to match **the same forest camp** as shot **S002** (page `002.jpg` wide beat): "
    "**Frieren** reading by a **large tree**, **Stark** and **small campfire**, **axe** and **packs** in the glade behind her. "
    "Companions stay **smaller in scale** and farther in depth than Fern; coherent Northern travel palette and lighting. "
)

S003_EDIT_LEAD_IN_EXTEND_CAMP_SQUIRREL = (
    "Image-guided **refine** on an approved **S003 extend-camp** frame (wide camp already locked). "
    "**Preserve** **Frieren**, **Stark**, **campfire**, **gear**, trees, and **Fern** body pose **single** composition, **no** duplicate Fern, **no** mirror flip. "
    "**Add** the **tiny grey post-runner squirrel** from the **scene body**: **upright on hind legs** **between Fern and the fire**, **cream-and-tan micro pouch** with **white paper**, **bushy tail**, **Fern's eyes toward** it. "
    "**Match** every **creature and prop** detail in the **concatenated** prompt below. "
)

S003_EDIT_LEAD_IN_COMPOSITE_SQUIRREL = (
    "**Two** uploads in **order**: **image 1** = **camp master** — **layout wins**. **image 2** = **messenger squirrel** ref — **match** its **pack**, **envelope**, **fur**, and **pose** on **image 1's** leaf floor **between Fern and fire**. "
    "**Fern** **looks at** the critter. **Camp**, trees, sky **from image 1**; **image 2** = **courier** **paint** only. "
)


def _edit_prompt(variant: str, *, composite_squirrel: bool) -> str:
    if variant == "fern-only":
        return S003_EDIT_LEAD_IN_FERN_ONLY + S003_PROMPT_FLUX_FERN_ONLY
    if variant == "extend-camp":
        return S003_EDIT_LEAD_IN_EXTEND_CAMP + S003_PROMPT_FLUX_EXTEND_CAMP
    if variant == "extend-camp-squirrel":
        if composite_squirrel:
            return (
                S003_EDIT_LEAD_IN_COMPOSITE_SQUIRREL
                + S003_PROMPT_FLUX_COMPOSITE_SQUIRREL
            )
        return (
            S003_EDIT_LEAD_IN_EXTEND_CAMP_SQUIRREL + S003_PROMPT_FLUX_EXTEND_CAMP_SQUIRREL
        )
    return S003_EDIT_LEAD_IN_FULL + S003_PROMPT_FLUX


def main() -> int:
    parser = argparse.ArgumentParser(
        description="S003 panel → Nano Banana 2 (default) and/or Flux 2 Pro /edit.",
        epilog="Nano Banana: https://fal.ai/models/fal-ai/nano-banana-2/edit/api",
    )
    parser.add_argument(
        "--variant",
        choices=("full", "fern-only", "extend-camp", "extend-camp-squirrel"),
        default="full",
        help="full | fern-only | extend-camp | extend-camp-squirrel (extend-camp PNG → squirrel + gaze)",
    )
    parser.add_argument(
        "--model",
        dest="model_choice",
        choices=("flux-2-pro-edit", "nano-banana-2-edit", "both"),
        default="nano-banana-2-edit",
        help="Edit backend: Nano Banana (default), Flux, or both in one run",
    )
    parser.add_argument(
        "--ref",
        type=Path,
        default=DEFAULT_REF,
        help=f"Reference crop (default: {DEFAULT_REF})",
    )
    parser.add_argument(
        "--squirrel-ref",
        type=Path,
        default=None,
        help="With --variant extend-camp-squirrel: second image (squirrel design ref); enables multi-image edit (camp + squirrel URLs).",
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
        help='Nano Banana only. Default **16:9** for TV-pipeline keys. Use **9:16** if a portrait framing stabilizes chirality.',
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
    squirrel_path: Path | None = (
        args.squirrel_ref.resolve() if args.squirrel_ref is not None else None
    )
    if squirrel_path is not None and args.variant != "extend-camp-squirrel":
        print(
            "--squirrel-ref only applies with --variant extend-camp-squirrel.",
            file=sys.stderr,
        )
        return 1
    composite_squirrel = squirrel_path is not None

    if args.variant == "extend-camp" and ref_path == DEFAULT_REF.resolve():
        if DEFAULT_EXTEND_CAMP_REF.is_file():
            ref_path = DEFAULT_EXTEND_CAMP_REF.resolve()
            print(f"extend-camp: using default fern-only ref {ref_path}", flush=True)
    if (
        args.variant == "extend-camp-squirrel"
        and ref_path == DEFAULT_REF.resolve()
    ):
        if DEFAULT_EXTEND_CAMP_SQUIRREL_REF.is_file():
            ref_path = DEFAULT_EXTEND_CAMP_SQUIRREL_REF.resolve()
            print(
                f"extend-camp-squirrel: using default extend-camp ref {ref_path}",
                flush=True,
            )
    variant_tag = (
        (
            "extendcampsquirrelimg"
            if composite_squirrel
            else "extendcampsquirrel"
        )
        if args.variant == "extend-camp-squirrel"
        else (
            "extendcamp"
            if args.variant == "extend-camp"
            else ("fernonly" if args.variant == "fern-only" else "full")
        )
    )
    edit_prompt = _edit_prompt(args.variant, composite_squirrel=composite_squirrel)

    if args.image_size == "1280x720":
        flux_size: dict[str, int] | str = {"width": 1280, "height": 720}
    elif args.image_size == "1920x1080":
        flux_size = {"width": 1920, "height": 1080}
    else:
        flux_size = "landscape_16_9"

    flux_args: dict = {
        "prompt": edit_prompt,
        "image_size": flux_size,
        "enable_safety_checker": True,
        "output_format": "png",
        "safety_tolerance": "2",
    }
    if args.seed is not None:
        flux_args["seed"] = args.seed

    nano_args: dict = {
        "prompt": edit_prompt,
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
            "Add panels\\panel_s003.png (crop from 002.jpg row 2) or pass --ref path\\to\\crop.png",
            file=sys.stderr,
        )
        return 1

    if composite_squirrel and squirrel_path is not None and not squirrel_path.is_file():
        print(f"--squirrel-ref not found: {squirrel_path}", file=sys.stderr)
        return 1

    print(f"Uploading reference: {ref_path}", flush=True)
    image_url = fal_client.upload_file(str(ref_path))
    print(f"Reference URL: {image_url}", flush=True)

    squirrel_url: str | None = None
    if composite_squirrel and squirrel_path is not None:
        print(f"Uploading squirrel design ref: {squirrel_path}", flush=True)
        squirrel_url = fal_client.upload_file(str(squirrel_path))
        print(f"Squirrel ref URL: {squirrel_url}", flush=True)

    image_urls_list: list[str] = (
        [image_url, squirrel_url] if squirrel_url else [image_url]
    )

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "outputs" / "fal"
    tests_dir = ROOT / "Tests"
    out_dir.mkdir(parents=True, exist_ok=True)

    meta_path = out_dir / f"{SHOT_ID}_ref_edit_meta_{variant_tag}_{ts}.json"
    meta_payload: dict = {
        "variant": args.variant,
        "model_choice": args.model_choice,
        "reference_local": str(ref_path),
        "reference_upload_url": image_url,
        "composite_squirrel": composite_squirrel,
        "seed": args.seed,
        **meta_extra,
    }
    if composite_squirrel and squirrel_path is not None and squirrel_url:
        meta_payload["squirrel_ref_local"] = str(squirrel_path)
        meta_payload["squirrel_ref_upload_url"] = squirrel_url
        meta_payload["image_urls_order"] = "camp_master_then_squirrel_design"
    meta_path.write_text(json.dumps(meta_payload, indent=2), encoding="utf-8")
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

        log_path = out_dir / f"{SHOT_ID}_{variant_tag}_{slug}_{ts}.json"
        log_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        print(f"Log: {log_path}", flush=True)

        url = image_url_from_result(result)
        if not url:
            print("No image URL in response", file=sys.stderr)
            summary.append({"slug": slug, "model_id": model_id, "ok": False, "error": "no_url"})
            continue

        ext = extension_from_url(url)
        image_path = tests_dir / f"{SHOT_ID}_{variant_tag}_{slug}_{ts}{ext}"
        try:
            download_file(url, image_path)
            print(f"Saved: {image_path}", flush=True)
            summary.append(
                {"slug": slug, "model_id": model_id, "ok": True, "url": url, "path": str(image_path)}
            )
        except OSError as e:
            print(f"Download failed: {e}", file=sys.stderr)
            summary.append({"slug": slug, "model_id": model_id, "ok": False, "error": str(e), "url": url})

    summary_path = out_dir / f"{SHOT_ID}_ref_edit_summary_{variant_tag}_{ts}.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nSummary: {summary_path}", flush=True)
    return 0 if summary and all(s.get("ok") for s in summary) else 1


if __name__ == "__main__":
    raise SystemExit(main())
