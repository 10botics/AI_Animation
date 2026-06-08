"""
Prepare Fern JP Qwen3 reference from `video source/fernsource.mp4`.

Outputs (production):
  Voice Reference/Japanese/Fern/fern_jp_qwen_ref.wav
  Voice Reference/Japanese/Fern/fern_jp_qwen_ref.txt
  Voice Reference/Japanese/Fern/fern_jp_qwen_ref.json

Usage:
  cd scripts
  python isolate_vocals_fal.py "..\\video source\\fernsource.mp4" --out "..\\voice_refs\\fern_jp_vocals.wav"
  python prepare_fern_qwen_ref.py
  python prepare_fern_qwen_ref.py --skip-demucs --source "..\\voice_refs\\fern_jp_vocals.wav"
"""

from __future__ import annotations

import subprocess
import sys

from fal_common import ROOT
from voice_paths import VR_JP_FERN

OUT_WAV = VR_JP_FERN / "fern_jp_qwen_ref.wav"
OUT_TXT = VR_JP_FERN / "fern_jp_qwen_ref.txt"
OUT_META = VR_JP_FERN / "fern_jp_qwen_ref.json"
DEFAULT_SOURCE = ROOT / "video source" / "fernsource.mp4"
VOCALS_FALLBACK = ROOT / "voice_refs" / "fern_jp_vocals.wav"


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Fern JP Qwen ref (VAD + transcript)")
    parser.add_argument("--source", type=str, default=None)
    parser.add_argument("--skip-demucs", action="store_true")
    parser.add_argument(
        "--skip",
        type=float,
        default=20.0,
        help="Start scan in source (seconds); 20 avoids opening gasp on fernsource",
    )
    args, rest = parser.parse_known_args()

    src = args.source
    if src is None:
        src = str(VOCALS_FALLBACK if VOCALS_FALLBACK.is_file() else DEFAULT_SOURCE)
    skip_demucs = args.skip_demucs or VOCALS_FALLBACK.is_file()

    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "prepare_frieren_qwen_ref.py"),
        "--source",
        src,
        "--whisper-language",
        "ja",
        "--out-wav",
        str(OUT_WAV),
        "--out-txt",
        str(OUT_TXT),
        "--out-meta",
        str(OUT_META),
    ]
    if skip_demucs:
        cmd.append("--skip-demucs")
    if "--skip" not in rest:
        cmd.extend(["--skip", str(args.skip)])
    cmd.extend(rest)
    print("Running:", " ".join(cmd), flush=True)
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
