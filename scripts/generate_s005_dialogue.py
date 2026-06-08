"""
S005 — Fern dialogue from panel balloon (`002.jpg` row 3 / `panel_s005.png`).

Story (B2 / stage_02 S005):
  Fern CU reading letter; soft Lernen memory telegraph behind.
  Unofficial First-Class mage request — formal, quiet unease.

Line (English scan):
  Fern: "Nay, this appears to be a personal request from First-Class Mage Lernen-sama."

Voice: **MiniMax TTS** (preset Lovely_Girl or cloned Fern via registry).

Muxes onto latest non-dialogue `S005_kling*.mp4` (~10s CU).

Usage:
  cd scripts
  python generate_s005_dialogue.py
  python generate_s005_dialogue.py --character Fern
  python generate_s005_dialogue.py --start-sec 2.0 --tag fern_dialogue_v2
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dialogue_mux import latest_shot_video, mux_dialogue
from fal_common import ROOT, read_fal_key
from minimax_dialogue import (
    FERN_S005_DIALOGUE_START_SEC,
    FERN_S005_EMOTION,
    FERN_S005_PAUSE_SEC,
    FERN_S005_PHRASES,
    FERN_S005_PRESET_VOICE,
    FERN_S005_SPEED,
    synthesize_fern_s005,
    synthesize_minimax,
)

FERN_LINE_TEXT = " ".join(FERN_S005_PHRASES)


def main() -> int:
    parser = argparse.ArgumentParser(description="S005 MiniMax Fern dialogue + mux")
    parser.add_argument("--video", type=Path, default=None)
    parser.add_argument("--character", type=str, default=None, help="Cloned Fern in voice_registry")
    parser.add_argument("--voice-id", type=str, default=None, help="MiniMax preset or custom_voice_id")
    parser.add_argument("--start-sec", type=float, default=FERN_S005_DIALOGUE_START_SEC)
    parser.add_argument("--duck", type=float, default=0.35)
    parser.add_argument("--pause-sec", type=float, default=FERN_S005_PAUSE_SEC)
    parser.add_argument("--speed", type=float, default=FERN_S005_SPEED)
    parser.add_argument("--emotion", type=str, default=FERN_S005_EMOTION)
    parser.add_argument(
        "--single-clip",
        action="store_true",
        help="One TTS call for full line (no split pause)",
    )
    parser.add_argument("--tag", type=str, default=None)
    args = parser.parse_args()

    if not read_fal_key():
        print("Missing FAL_KEY in .env", file=sys.stderr)
        return 1
    os.environ["FAL_KEY"] = read_fal_key() or ""

    video = args.video.resolve() if args.video else latest_shot_video("S005")
    if not video.is_file():
        print(f"Video not found: {video}", file=sys.stderr)
        return 1

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "outputs" / "voice" / "S005"
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = args.tag or "fern_dialogue"
    stem = out_dir / f"s005_fern_{ts}.mp3"

    if args.single_clip:
        audio = synthesize_minimax(
            FERN_LINE_TEXT,
            stem,
            voice_id=args.voice_id,
            character=args.character,
            emotion=args.emotion,
            speed=args.speed,
        )
    else:
        audio = synthesize_fern_s005(
            stem,
            voice_id=args.voice_id,
            character=args.character,
            pause_sec=args.pause_sec,
            emotion=args.emotion,
            speed=args.speed,
        )
    print(f"TTS Fern: {audio.name}", flush=True)

    meta = out_dir / f"s005_{tag}_meta_{ts}.json"
    meta.write_text(
        json.dumps(
            {
                "video_in": str(video),
                "engine": "minimax-tts",
                "speaker": "Fern",
                "line_text": FERN_LINE_TEXT,
                "phrases": list(FERN_S005_PHRASES),
                "split_phrases": not args.single_clip,
                "pause_sec": args.pause_sec,
                "start_sec": args.start_sec,
                "voice_id": args.voice_id or FERN_S005_PRESET_VOICE,
                "character": args.character,
                "emotion": args.emotion,
                "speed": args.speed,
                "stem": str(audio),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    out_video = video.with_name(f"{video.stem}_{tag}_{ts}.mp4")
    mux_dialogue(video, [(audio, args.start_sec)], out_video, args.duck)
    print(f"Saved: {out_video}", flush=True)
    print(f"Meta: {meta}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
