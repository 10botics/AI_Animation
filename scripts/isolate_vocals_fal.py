"""
Isolate vocals from video/audio using Fal Demucs (removes BGM, keeps dialogue).

Local Demucs save fails on this Windows env (torchcodec); Fal hosted Demucs works.

Usage:
  cd scripts
  python isolate_vocals_fal.py "..\\voice Frieren1min.mp4"
  python isolate_vocals_fal.py "..\\voice Frieren1min.mp4" --out "..\\voice_refs\\frieren_1min_vocals.wav"
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

from fal_common import ROOT, download_file, read_fal_key

DEMUCS_MODEL = "fal-ai/demucs"


def _extract_wav(src: Path, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "44100",
            str(dest),
        ],
        check=True,
        capture_output=True,
    )
    return dest


def isolate_vocals(
    input_path: Path,
    out_wav: Path,
    *,
    model: str = "htdemucs",
    also_other: bool = False,
) -> dict:
    work = ROOT / "outputs" / "voice" / "isolation"
    work.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    raw = work / f"{input_path.stem}_{ts}_full.wav"
    _extract_wav(input_path, raw)

    url = fal_client.upload_file(str(raw))
    print(f"Uploaded: {url}", flush=True)
    stems = ["vocals"]
    if also_other:
        stems.extend(["other"])

    result = fal_client.subscribe(
        DEMUCS_MODEL,
        arguments={
            "audio_url": url,
            "model": model,
            "stems": stems,
            "output_format": "wav",
        },
        with_logs=True,
    )
    if not isinstance(result, dict):
        raise RuntimeError(f"Demucs failed: {result}")

    vocals = result.get("vocals")
    if not isinstance(vocals, dict) or not vocals.get("url"):
        raise RuntimeError(f"No vocals stem in result: {result}")

    out_wav.parent.mkdir(parents=True, exist_ok=True)
    download_file(vocals["url"], out_wav)
    print(f"Vocals: {out_wav}", flush=True)

    meta = {
        "input": str(input_path.relative_to(ROOT)) if input_path.is_relative_to(ROOT) else str(input_path),
        "out_wav": str(out_wav.relative_to(ROOT)) if out_wav.is_relative_to(ROOT) else str(out_wav),
        "demucs_model": model,
        "fal_result_keys": list(result.keys()),
        "ts": ts,
    }
    meta_path = out_wav.with_suffix(".json")
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return meta


def main() -> int:
    if not read_fal_key():
        print("Missing FAL_KEY in .env", file=sys.stderr)
        return 1
    os.environ["FAL_KEY"] = read_fal_key() or ""

    parser = argparse.ArgumentParser(description="Vocal isolation via Fal Demucs")
    parser.add_argument("input", type=Path, help="Video or audio file")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "voice_refs" / "frieren_1min_vocals.wav",
    )
    parser.add_argument(
        "--model",
        default="htdemucs",
        choices=("htdemucs", "htdemucs_6s", "htdemucs_ft"),
        help="htdemucs = vocals-focused; htdemucs_6s = more stems",
    )
    args = parser.parse_args()

    src = args.input.resolve()
    if not src.is_file():
        print(f"Not found: {src}", file=sys.stderr)
        return 1

    out = args.out.resolve()
    isolate_vocals(src, out, model=args.model)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
