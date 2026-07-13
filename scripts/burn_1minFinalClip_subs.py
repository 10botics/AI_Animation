"""
Burn subtitles into 1minFinalClip.mp4 (English + HK Traditional Chinese).

Source: 1minFinalClip.mp4 (clean assembly, no subs)
Outputs:
  1minFinalClip_en_subbed.mp4
  1minFinalClip_zh-HK_subbed.mp4

Usage:
  python scripts/burn_1minFinalClip_subs.py
  python scripts/burn_1minFinalClip_subs.py --lang en
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "1minFinalClip.mp4"
SUBS_DIR = ROOT / "subs"

# Shared layout (match EN + zh-HK)
FONT_SIZE = 18
MARGIN_V = 18
OUTLINE = 2
SHADOW = 1

TRACKS = {
    "en": {
        "srt": SUBS_DIR / "1minFinalClip.en.srt",
        "out": ROOT / "1minFinalClip_en_subbed.mp4",
        "force_style": (
            f"FontName=Arial,FontSize={FONT_SIZE},Outline={OUTLINE},"
            f"Shadow={SHADOW},MarginV={MARGIN_V}"
        ),
    },
    "zh-HK": {
        "srt": SUBS_DIR / "1minFinalClip.zh-HK.srt",
        "out": ROOT / "1minFinalClip_zh-HK_subbed.mp4",
        "force_style": (
            f"FontName=Microsoft JhengHei,FontSize={FONT_SIZE},Outline={OUTLINE},"
            f"Shadow={SHADOW},MarginV={MARGIN_V}"
        ),
    },
}


def burn(lang: str) -> None:
    track = TRACKS[lang]
    srt, out = track["srt"], track["out"]
    if not SOURCE.is_file():
        raise FileNotFoundError(f"Missing source video: {SOURCE}")
    if not srt.is_file():
        raise FileNotFoundError(f"Missing subtitle file: {srt}")

    # ffmpeg subtitles filter: paths relative to cwd; escape for Windows filter syntax.
    srt_rel = srt.relative_to(ROOT).as_posix()
    vf = f"subtitles={srt_rel}:force_style='{track['force_style']}'"
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(SOURCE),
        "-vf",
        vf,
        "-c:a",
        "copy",
        str(out),
    ]
    print(f"Burning {lang} -> {out.name}", flush=True)
    subprocess.run(cmd, check=True, cwd=ROOT)


def main() -> None:
    parser = argparse.ArgumentParser(description="Burn 1minFinalClip subtitles.")
    parser.add_argument(
        "--lang",
        choices=("en", "zh-HK", "all"),
        default="all",
        help="Which track to render (default: all)",
    )
    args = parser.parse_args()
    langs = list(TRACKS) if args.lang == "all" else [args.lang]
    for lang in langs:
        burn(lang)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
