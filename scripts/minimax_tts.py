"""
MiniMax Speech-02 HD TTS with a cloned voice (custom_voice_id from minimax_voice_clone.py).

Requires: FAL_KEY in project .env. Use --voice-id or --character (voice_registry.local.json).

Default output language hint: English. For Cantonese later, pass e.g.
  --language-boost "Chinese,Yue"
(Fal enum label; confirm in playground if an update renames it.)

Usage:
  cd scripts
  python minimax_tts.py --character Fern --text "Line here" --out "..\\outputs\\voice\\fern_line01.mp3"
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import fal_client

from fal_common import ROOT, download_file, read_fal_key

REGISTRY_PATH = ROOT / "voice_registry.local.json"
TTS_MODEL = "fal-ai/minimax-tts/text-to-speech"


def _resolve_voice_id(character: str | None, voice_id: str | None) -> str:
    if voice_id:
        return voice_id.strip()
    if not character:
        print("Pass --voice-id or --character.", file=sys.stderr)
        sys.exit(1)
    if not REGISTRY_PATH.is_file():
        print(f"Missing {REGISTRY_PATH} — run minimax_voice_clone.py --character first.", file=sys.stderr)
        sys.exit(1)
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    ids = data.get("minimax_custom_voice_ids") or {}
    vid = ids.get(character.strip())
    if not vid:
        print(f"No custom_voice_id for [{character}] in registry.", file=sys.stderr)
        sys.exit(1)
    return str(vid)


def main() -> int:
    if not read_fal_key():
        print("Missing FAL_KEY — set it in .env at repo root.", file=sys.stderr)
        return 1

    parser = argparse.ArgumentParser(description="MiniMax TTS with cloned voice")
    idg = parser.add_mutually_exclusive_group(required=True)
    idg.add_argument("--voice-id", type=str, help="custom_voice_id from voice clone")
    idg.add_argument("--character", type=str, help="Key from voice_registry.local.json")
    parser.add_argument("--text", type=str, help="Up to ~5000 chars")
    parser.add_argument(
        "--text-file",
        type=Path,
        help="UTF-8 file (use instead of --text)",
    )
    parser.add_argument(
        "--language-boost",
        default="English",
        help=(
            'Fal MiniMax language_boost enum value. Default: English. '
            'Cantonese: often "Chinese,Yue" (see fal-ai/minimax-tts/text-to-speech API). '
            'Other examples: Japanese, auto.'
        ),
    )
    parser.add_argument(
        "--emotion",
        choices=("happy", "sad", "angry", "fearful", "disgusted", "surprised", "neutral"),
        default="neutral",
    )
    parser.add_argument("--speed", type=float, default=1.0, help="0.5–2.0")
    parser.add_argument(
        "--english-normalization",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Improve English number/date reading (Fal voice_setting; on by default for convenience)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Output path (.mp3). Default: outputs/voice/<timestamp>_<character or id>.mp3",
    )
    args = parser.parse_args()

    if args.text_file:
        text = args.text_file.read_text(encoding="utf-8-sig").strip()
    elif args.text:
        text = args.text.strip()
    else:
        print("Provide --text or --text-file.", file=sys.stderr)
        return 1
    if len(text) > 5000:
        print(f"Text is {len(text)} chars; split into chunks ≤5000.", file=sys.stderr)
        return 1

    vid = _resolve_voice_id(args.character, args.voice_id)

    if args.out:
        out_path = args.out.resolve()
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        label = (args.character or "voice").replace(" ", "_")
        out_path = ROOT / "outputs" / "voice" / f"{label}_{ts}.mp3"

    voice_setting: dict = {
        "custom_voice_id": vid,
        "emotion": args.emotion,
        "speed": args.speed,
    }
    boost = str(args.language_boost).strip()
    if boost.casefold() == "english" and args.english_normalization:
        voice_setting["english_normalization"] = True

    result = fal_client.subscribe(
        TTS_MODEL,
        arguments={
            "text": text,
            "voice_setting": voice_setting,
            "language_boost": args.language_boost,
        },
        with_logs=True,
    )

    if not isinstance(result, dict):
        print(result, file=sys.stderr)
        return 1
    audio = result.get("audio")
    if not isinstance(audio, dict) or not audio.get("url"):
        print(f"Unexpected response: {result}", file=sys.stderr)
        return 1
    url = audio["url"]
    download_file(url, out_path)
    print(f"Wrote {out_path}")
    if "duration_ms" in result:
        print(f"duration_ms: {result['duration_ms']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
