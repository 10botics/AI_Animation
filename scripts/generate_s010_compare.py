"""
Run S010 (golden ridge) on Flux only — Flash vs Flex — for style comparison.
(SoteDiffusion is project-blacklisted; see fal_common.BLACKLISTED_FAL_MODEL_IDS.)

Saves JSON logs under outputs/fal/ and images under Tests/.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

import fal_client

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

MODELS: list[tuple[str, str, dict]] = [
    (
        "flux-2-flash",
        "fal-ai/flux-2/flash",
        {
            "prompt": S010_PROMPT_FLUX,
            "guidance_scale": 2.5,
            "image_size": {"width": 1280, "height": 720},
            "num_images": 1,
            "enable_safety_checker": True,
            "output_format": "png",
        },
    ),
    (
        "flux-2-flex",
        "fal-ai/flux-2-flex",
        {
            "prompt": S010_PROMPT_FLUX,
            "guidance_scale": 3.5,
            "num_inference_steps": 28,
            "image_size": {"width": 1280, "height": 720},
            "enable_safety_checker": True,
            "output_format": "png",
            "safety_tolerance": "2",
        },
    ),
]


def main() -> int:
    for _, mid, _ in MODELS:
        assert_model_allowed(mid)

    key = read_fal_key()
    if not key:
        print("Missing FAL_KEY — set in .env at project root.", file=sys.stderr)
        return 1
    os.environ["FAL_KEY"] = key

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "outputs" / "fal"
    tests_dir = ROOT / "Tests"
    out_dir.mkdir(parents=True, exist_ok=True)

    summary: list[dict] = []

    for slug, model_id, arguments in MODELS:
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
            print(f"URL: {url}", flush=True)
            print(f"Saved: {image_path}", flush=True)
            summary.append(
                {"slug": slug, "model_id": model_id, "ok": True, "url": url, "path": str(image_path)}
            )
        except OSError as e:
            print(f"Download failed: {e}", file=sys.stderr)
            summary.append({"slug": slug, "model_id": model_id, "ok": False, "error": str(e), "url": url})

    summary_path = out_dir / f"{SHOT_ID}_compare_summary_{ts}.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nSummary: {summary_path}", flush=True)
    return 0 if summary and all(s.get("ok") for s in summary) else 1


if __name__ == "__main__":
    raise SystemExit(main())
