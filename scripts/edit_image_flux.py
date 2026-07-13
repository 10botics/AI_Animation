"""
**Legacy:** Flux 2 Pro Edit (and optional Flex). Project stills default to **Nano Banana 2** via `generate_*_ref_edit.py --model nano-banana-2-edit`.

Post-process any image with Flux 2 Pro Edit by default; pass --with-flex to also run Flex.

Uploads your file, applies your natural-language edit prompt, downloads results to Tests/
and writes JSON logs under outputs/fal/.

Example (PowerShell):
  python scripts/edit_image_flux.py -i Tests/S010_flux-2-pro-edit_20260325_103440.png `
    -p "Increase golden reflections on the city; keep three figures and composition unchanged."
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import fal_client

from fal_common import (
    ROOT,
    assert_model_allowed,
    download_file,
    extension_from_url,
    image_url_from_result,
    read_fal_key,
)


def _safe_label(text: str) -> str:
    s = re.sub(r"[^\w\-.]+", "_", text.strip(), flags=re.UNICODE).strip("_")
    return (s[:48] or "edit").lower()


def build_models(
    prompt: str,
    width: int,
    height: int,
) -> list[tuple[str, str, dict]]:
    return [
        (
            "flux-2-pro-edit",
            "fal-ai/flux-2-pro/edit",
            {
                "prompt": prompt,
                "image_size": {"width": width, "height": height},
                "enable_safety_checker": True,
                "output_format": "png",
                "safety_tolerance": "2",
            },
        ),
        (
            "flux-2-flex-edit",
            "fal-ai/flux-2-flex/edit",
            {
                "prompt": prompt,
                "guidance_scale": 3.5,
                "num_inference_steps": 28,
                "image_size": {"width": width, "height": height},
                "enable_safety_checker": True,
                "output_format": "png",
                "safety_tolerance": "2",
            },
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Edit an image with Flux 2 Pro (default; --with-flex adds Flex)"
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        required=True,
        help="Local image to edit (PNG/JPEG/WebP)",
    )
    parser.add_argument(
        "-p",
        "--prompt",
        required=True,
        help="What to change or add; be specific about what must stay the same",
    )
    parser.add_argument(
        "--label",
        type=str,
        default="",
        help="Output file prefix (default: stem of --input)",
    )
    parser.add_argument("--width", type=int, default=1280, help="Output width (default 1280)")
    parser.add_argument("--height", type=int, default=720, help="Output height (default 720)")
    parser.add_argument(
        "--with-flex",
        action="store_true",
        help="Also run fal-ai/flux-2-flex/edit after Pro",
    )
    parser.add_argument(
        "--flex-only",
        action="store_true",
        help="Only run fal-ai/flux-2-flex/edit",
    )
    args = parser.parse_args()

    if args.with_flex and args.flex_only:
        print("Use only one of --with-flex and --flex-only.", file=sys.stderr)
        return 1

    inp = args.input.resolve()
    label = _safe_label(args.label) if args.label else _safe_label(inp.stem)

    full = build_models(args.prompt, args.width, args.height)
    if args.flex_only:
        models = [m for m in full if m[0] == "flux-2-flex-edit"]
    elif args.with_flex:
        models = full
    else:
        models = [m for m in full if m[0] == "flux-2-pro-edit"]

    for _, mid, _ in models:
        assert_model_allowed(mid)

    key = read_fal_key()
    if not key:
        print("Missing FAL_KEY — set in .env at project root.", file=sys.stderr)
        return 1
    os.environ["FAL_KEY"] = key

    if not inp.is_file():
        print(f"Input not found: {inp}", file=sys.stderr)
        return 1

    print(f"Uploading: {inp}", flush=True)
    image_url = fal_client.upload_file(str(inp))
    print(f"URL: {image_url}", flush=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = ROOT / "outputs" / "fal"
    tests_dir = ROOT / "Tests"
    out_dir.mkdir(parents=True, exist_ok=True)

    meta_path = out_dir / f"{label}_image_edit_meta_{ts}.json"
    meta_path.write_text(
        json.dumps(
            {
                "input_local": str(inp),
                "upload_url": image_url,
                "prompt": args.prompt,
                "image_size": {"width": args.width, "height": args.height},
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
        print(f"\n--- {slug} ---", flush=True)
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

        log_path = out_dir / f"{label}_{slug}_{ts}.json"
        log_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        print(f"Log: {log_path}", flush=True)

        url = image_url_from_result(result)
        if not url:
            print("No image URL in response", file=sys.stderr)
            summary.append({"slug": slug, "model_id": model_id, "ok": False, "error": "no_url"})
            continue

        ext = extension_from_url(url)
        out_img = tests_dir / f"{label}_{slug}_{ts}{ext}"
        try:
            download_file(url, out_img)
            print(f"Saved: {out_img}", flush=True)
            summary.append({"slug": slug, "model_id": model_id, "ok": True, "url": url, "path": str(out_img)})
        except OSError as e:
            print(f"Download failed: {e}", file=sys.stderr)
            summary.append({"slug": slug, "model_id": model_id, "ok": False, "error": str(e), "url": url})

    summary_path = out_dir / f"{label}_image_edit_summary_{ts}.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nSummary: {summary_path}", flush=True)
    return 0 if summary and all(s.get("ok") for s in summary) else 1


if __name__ == "__main__":
    raise SystemExit(main())
