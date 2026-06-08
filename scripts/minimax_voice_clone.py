"""
MiniMax voice clone on Fal — upload reference audio (or URL), receive custom_voice_id for TTS.

Requires: FAL_KEY in project .env (see fal_common). Reference: ≥10 s, single speaker, clean.
Pricing: see https://fal.ai/models/fal-ai/minimax/voice-clone

Usage:
  cd scripts
  python minimax_voice_clone.py --character Fern --audio "..\\voice_refs\\fern_ref.wav"

Registry: writes voice_registry.local.json at repo root (gitignored) when --character is set.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import fal_client

from fal_common import ROOT, read_fal_key

REGISTRY_PATH = ROOT / "voice_registry.local.json"
VOICE_CLONE_MODEL = "fal-ai/minimax/voice-clone"


def _load_registry() -> dict:
    if not REGISTRY_PATH.is_file():
        return {"minimax_custom_voice_ids": {}}
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if "minimax_custom_voice_ids" not in data:
        data["minimax_custom_voice_ids"] = {}
    return data


def _save_registry(data: dict) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    key = read_fal_key()
    if not key:
        print("Missing FAL_KEY — set it in .env at repo root.", file=sys.stderr)
        return 1

    parser = argparse.ArgumentParser(description="MiniMax voice clone → custom_voice_id")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument(
        "--audio",
        type=Path,
        help="Local WAV/MP3 (≥10s single-voice); uploaded via fal_client.upload_file",
    )
    src.add_argument(
        "--audio-url",
        type=str,
        metavar="URL",
        help="Public HTTPS URL to reference audio",
    )
    parser.add_argument(
        "--character",
        type=str,
        help="Label to store in voice_registry.local.json (e.g. Fern)",
    )
    parser.add_argument(
        "--preview-text",
        type=str,
        default="Hello, this is a preview of your cloned voice! I hope you like it!",
    )
    parser.add_argument(
        "--model",
        choices=("speech-02-hd", "speech-02-turbo", "speech-01-hd", "speech-01-turbo"),
        default="speech-02-hd",
        help="TTS model for preview line",
    )
    parser.add_argument("--noise-reduction", action="store_true")
    parser.add_argument("--volume-normalization", action="store_true")
    parser.add_argument(
        "--no-preview",
        action="store_true",
        help="Clone only: do not send preview text/model (check Fal billing for your account)",
    )
    args = parser.parse_args()

    if args.audio_url:
        audio_url = args.audio_url.strip()
    else:
        p = args.audio.resolve()
        if not p.is_file():
            print(f"Not a file: {p}", file=sys.stderr)
            return 1
        audio_url = fal_client.upload_file(str(p))

    clone_args: dict = {
        "audio_url": audio_url,
        "noise_reduction": args.noise_reduction,
        "need_volume_normalization": args.volume_normalization,
    }
    if not args.no_preview:
        clone_args["text"] = args.preview_text
        clone_args["model"] = args.model

    result = fal_client.subscribe(VOICE_CLONE_MODEL, arguments=clone_args, with_logs=True)

    if not isinstance(result, dict):
        print(result, file=sys.stderr)
        return 1
    voice_id = result.get("custom_voice_id")
    if not voice_id:
        print(f"Unexpected response: {result}", file=sys.stderr)
        return 1
    print(f"custom_voice_id: {voice_id}")
    preview = result.get("audio")
    if isinstance(preview, dict) and preview.get("url"):
        print(f"preview_audio_url: {preview['url']}")

    if args.character:
        reg = _load_registry()
        reg["minimax_custom_voice_ids"][args.character.strip()] = str(voice_id)
        _save_registry(reg)
        print(f"Saved to {REGISTRY_PATH} under [{args.character}]")

    print("\nNext: python minimax_tts.py --character", (args.character or "Name"), '--text "Your line"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
