"""
Stage 4 smoke / S010: Golden Weise ridge — fal-ai/flux-2/flash (text-to-image).
Loads FAL_KEY from project-root .env (never print the key).
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

from fal_common import (
    ROOT,
    S010_PROMPT_FLUX,
    assert_model_allowed,
    download_file,
    extension_from_url,
    image_url_from_result,
    read_fal_key,
)

import fal_client

MODEL_ID = "fal-ai/flux-2/flash"
SHOT_ID = "S010"


def main() -> int:
    assert_model_allowed(MODEL_ID)

    key = read_fal_key()
    if not key:
        print(
            "Missing or empty FAL_KEY. In project root .env use exactly:\n"
            "  FAL_KEY=your_key_here\n"
            "(no spaces around =; one line; no quotes unless needed).",
            file=sys.stderr,
        )
        return 1
    os.environ["FAL_KEY"] = key

    out_dir = ROOT / "outputs" / "fal"
    tests_dir = ROOT / "Tests"
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = out_dir / f"{SHOT_ID}_{ts}.json"

    arguments = {
        "prompt": S010_PROMPT_FLUX,
        "guidance_scale": 2.5,
        "image_size": {"width": 1280, "height": 720},
        "num_images": 1,
        "enable_safety_checker": True,
        "output_format": "png",
    }

    print(f"Submitting {MODEL_ID} for {SHOT_ID}...", flush=True)
    result = fal_client.subscribe(
        MODEL_ID,
        arguments=arguments,
        with_logs=True,
    )

    log_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(f"Raw response saved: {log_path}", flush=True)

    url = image_url_from_result(result)
    if not url:
        print("Unexpected response shape; see JSON log.", file=sys.stderr)
        return 2

    print(f"Image URL: {url}", flush=True)
    ext = extension_from_url(url)
    image_path = tests_dir / f"{SHOT_ID}_{ts}{ext}"
    try:
        download_file(url, image_path)
        print(f"Saved image: {image_path}", flush=True)
    except OSError as e:
        print(f"Download failed: {e}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
