"""MiniMax TTS helpers for shot dialogue (preset or cloned voice)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import fal_client

from fal_common import ROOT, download_file

MINIMAX_TTS = "fal-ai/minimax-tts/text-to-speech"
REGISTRY_PATH = ROOT / "voice_registry.local.json"

# S005 — ch.81 B2 / `002.jpg` row 3 right / `panels/eng/panel_s005.png`
# Fern reads unofficial letter; Lernen memory telegraph in BG. Formal, measured, quiet weight.
FERN_S005_PHRASES = (
    "Nay, this appears to be a personal request",
    "from First-Class Mage Lernen-sama.",
)
FERN_S005_PAUSE_SEC = 0.45
FERN_S005_DIALOGUE_START_SEC = 1.85
FERN_S005_PRESET_VOICE = "Lovely_Girl"
FERN_S005_EMOTION = "neutral"
FERN_S005_SPEED = 0.95


def _resolve_voice_id(*, character: str | None, voice_id: str | None) -> str:
    if voice_id:
        return voice_id.strip()
    if character and REGISTRY_PATH.is_file():
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        vid = (data.get("minimax_custom_voice_ids") or {}).get(character.strip())
        if vid:
            return str(vid)
    return FERN_S005_PRESET_VOICE


def synthesize_minimax(
    text: str,
    out: Path,
    *,
    voice_id: str | None = None,
    character: str | None = None,
    emotion: str = FERN_S005_EMOTION,
    speed: float = FERN_S005_SPEED,
) -> Path:
    vid = _resolve_voice_id(character=character, voice_id=voice_id)
    vs: dict = {"emotion": emotion, "speed": speed}
    if REGISTRY_PATH.is_file() and character:
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        if (data.get("minimax_custom_voice_ids") or {}).get(character.strip()):
            vs["custom_voice_id"] = vid
        else:
            vs["voice_id"] = vid
    else:
        vs["voice_id"] = vid

    result = fal_client.subscribe(
        MINIMAX_TTS,
        arguments={
            "text": text,
            "voice_setting": vs,
            "language_boost": "English",
        },
        with_logs=True,
    )
    audio = result.get("audio") if isinstance(result, dict) else None
    if not isinstance(audio, dict) or not audio.get("url"):
        print(f"MiniMax TTS failed: {result}", file=sys.stderr)
        raise RuntimeError(f"MiniMax TTS failed: {result}")
    download_file(audio["url"], out)
    return out


def synthesize_fern_s005(
    out: Path,
    *,
    voice_id: str | None = None,
    character: str | None = None,
    pause_sec: float = FERN_S005_PAUSE_SEC,
    emotion: str = FERN_S005_EMOTION,
    speed: float = FERN_S005_SPEED,
) -> Path:
    from qwen_tts import concat_with_pauses

    tmp_dir = out.parent
    stem = out.stem
    parts: list[Path] = []
    for i, text in enumerate(FERN_S005_PHRASES):
        part = tmp_dir / f"{stem}_p{i}.mp3"
        synthesize_minimax(
            text,
            part,
            voice_id=voice_id,
            character=character,
            emotion=emotion,
            speed=speed,
        )
        parts.append(part)
    return concat_with_pauses(parts, pause_sec, out)
