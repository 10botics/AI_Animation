"""
HeyGen lip-sync via Fal.ai (same FAL_KEY as other scripts).

Delegates to lipsync_fal.py — no separate HeyGen API key.

S008 defaults:
  python heygen_lipsync.py
  python heygen_lipsync.py --mode speed --tag lipsync_v11_draft

Fal models:
  fal-ai/heygen/v3/lipsync/precision
  fal-ai/heygen/v3/lipsync/speed
"""

from __future__ import annotations

import sys

from lipsync_fal import ROOT, main as lipsync_main

# HeyGen on Fal errors on fully silent video ("No speech detected"). Use muxed dialogue clip.
S008_BASE_VIDEO = (
    ROOT
    / "outputs"
    / "video"
    / "final"
    / "S008_kling-v26-pro_i2v_natural-audio_20260527_092816_frieren_dialogue_v11_20260602_103647.mp4"
)
S008_DIALOGUE_AUDIO = ROOT / "outputs" / "voice" / "S008" / "s008_frieren_20260602_103112.mp3"
S008_DIALOGUE_START_SEC = 2.05


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="HeyGen lip-sync via Fal (FAL_KEY)")
    parser.add_argument("--mode", choices=("precision", "speed"), default="precision")
    parser.add_argument(
        "--video",
        type=str,
        default=str(S008_BASE_VIDEO),
        help="Source MP4 (muxed dialogue OK; silent Kling alone fails HeyGen)",
    )
    parser.add_argument("--audio", type=str, default=str(S008_DIALOGUE_AUDIO))
    parser.add_argument("--start-sec", type=float, default=S008_DIALOGUE_START_SEC)
    parser.add_argument("--tag", type=str, default="heygen")
    parser.add_argument("--out-dir", type=str, default=str(ROOT / "outputs" / "video" / "final"))
    args, _ = parser.parse_known_args()

    model_key = f"heygen-{args.mode}"
    sys.argv = [
        "lipsync_fal.py",
        "--model",
        model_key,
        "--video",
        args.video,
        "--audio",
        args.audio,
        "--start-sec",
        str(args.start_sec),
        "--tag",
        args.tag,
        "--out-dir",
        args.out_dir,
    ]
    return lipsync_main()


if __name__ == "__main__":
    raise SystemExit(main())
