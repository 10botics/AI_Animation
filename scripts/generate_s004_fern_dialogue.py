"""
S004 — Fern dialogue from panel_s004jap.png (JP balloon).

  Fern: フリーレン様。
  Frieren: また大陸魔法協会からの依頼？ (see generate_s004_dialogue.py)

Default: WAV under outputs/voice/S004/ + copy to outputs/voice/final/S004/.

Usage:
  cd scripts
  python prepare_fern_qwen_ref.py
  python generate_s004_fern_dialogue.py --reclone --tag fern_dialogue_v1_ja
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dialogue_mux import latest_shot_video, mux_dialogue, probe_duration
from fal_common import ROOT, read_fal_key
from qwen_tts import (
    FERN_S004_DIALOGUE_START_SEC,
    FERN_S004_LANGUAGE,
    FERN_S004_PHRASES,
    FERN_S004_PHRASES_EN,
    FERN_S004_PROMPT,
    FERN_S004_PROMPT_EN,
    FERN_QWEN_REF_TXT,
    FERN_QWEN_REF_WAV,
    load_fern_reference_text,
    load_registry,
    resolve_fern_embedding,
    synthesize_s004_fern,
)


def _line_and_prompt(language: str) -> tuple[str, str]:
    if language.lower() in ("english", "en"):
        return FERN_S004_PHRASES_EN[0], FERN_S004_PROMPT_EN
    return FERN_S004_PHRASES[0], FERN_S004_PROMPT


def main() -> int:
    parser = argparse.ArgumentParser(description="S004 Qwen3 Fern dialogue (WAV default)")
    parser.add_argument("--mux", action="store_true")
    parser.add_argument("--video", type=Path, default=None)
    parser.add_argument("--skip-clone", action="store_true")
    parser.add_argument("--reclone", action="store_true")
    parser.add_argument("--start-sec", type=float, default=FERN_S004_DIALOGUE_START_SEC)
    parser.add_argument("--duck", type=float, default=0.35)
    parser.add_argument(
        "--language",
        choices=("Japanese", "English"),
        default=FERN_S004_LANGUAGE,
    )
    parser.add_argument("--prompt", type=str, default=None)
    parser.add_argument("--tag", type=str, default=None)
    args = parser.parse_args()

    line_text, default_prompt = _line_and_prompt(args.language)
    prompt = args.prompt or default_prompt

    if not read_fal_key():
        print("Missing FAL_KEY in .env", file=sys.stderr)
        return 1
    os.environ["FAL_KEY"] = read_fal_key() or ""

    if not FERN_QWEN_REF_WAV.is_file():
        print(
            f"Missing Fern ref: {FERN_QWEN_REF_WAV}\nRun: python prepare_fern_qwen_ref.py",
            file=sys.stderr,
        )
        return 1

    video: Path | None = None
    if args.mux:
        video = args.video.resolve() if args.video else latest_shot_video("S004")
        if not video.is_file():
            print(f"Video not found: {video}", file=sys.stderr)
            return 1

    if args.reclone or not args.skip_clone:
        emb_url, emb_meta = resolve_fern_embedding(force_reclone=args.reclone)
        reference_text = load_fern_reference_text()
    else:
        reg = load_registry()
        entry = (reg.get("qwen_speaker_embeddings") or {}).get("Fern")
        if not entry or not entry.get("url"):
            print("No Fern Qwen embedding — run without --skip-clone", file=sys.stderr)
            return 1
        emb_url = str(entry["url"])
        emb_meta = entry
        reference_text = (entry.get("reference_text") or "").strip() or None

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "outputs" / "voice" / "S004"
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = args.tag or "fern_dialogue_ja"
    stem = out_dir / f"s004_fern_{ts}.mp3"
    wav_path = out_dir / f"s004_fern_{tag}_{ts}.wav"

    synthesize_s004_fern(
        emb_url,
        stem,
        wav_path,
        prompt=prompt,
        phrase=line_text,
        language=args.language,
    )
    print(f"TTS Fern: {stem.name}", flush=True)

    audio_dur = probe_duration(wav_path)
    video_dur = probe_duration(video) if video else None

    if not args.mux:
        print(f"WAV: {wav_path}", flush=True)
        final_dir = ROOT / "outputs" / "voice" / "final" / "S004"
        final_dir.mkdir(parents=True, exist_ok=True)
        final_wav = final_dir / wav_path.name
        final_wav.write_bytes(wav_path.read_bytes())
        print(f"Final: {final_wav}", flush=True)

    meta_payload: dict = {
        "engine": "qwen3-tts-1.7b",
        "mode": "fern_only",
        "language": args.language,
        "line_text": line_text,
        "phrases": [line_text],
        "start_sec": args.start_sec,
        "audio_duration_sec": audio_dur,
        "qwen_embedding": emb_meta,
        "prompt": prompt,
        "reference_text_clone_only": reference_text,
        "reference_text_on_tts": False,
        "wav_export": "export_dialogue_wav (24kHz mono PCM)",
        "voice_ref": str(FERN_QWEN_REF_WAV.relative_to(ROOT)),
        "voice_ref_txt": str(FERN_QWEN_REF_TXT.relative_to(ROOT)),
        "stem": str(stem),
        "wav_only": not args.mux,
        "panel_story_ref": "panels/jap/panel_s004jap.png",
        "personality_guide": "docs/fern-qwen-personality-guide.md",
    }
    if not args.mux:
        meta_payload["wav_output"] = str(wav_path)
        meta_payload["wav_final"] = str(ROOT / "outputs" / "voice" / "final" / "S004" / wav_path.name)
    if video_dur is not None:
        meta_payload["video_duration_sec"] = video_dur
        meta_payload["video_in"] = str(video)

    meta = out_dir / f"s004_{tag}_meta_{ts}.json"
    meta.write_text(json.dumps(meta_payload, indent=2), encoding="utf-8")
    print(f"Meta: {meta}", flush=True)

    if args.mux and video is not None:
        out_video = video.with_name(f"{video.stem}_{tag}_{ts}.mp4")
        mux_dialogue(video, [(stem, args.start_sec)], out_video, args.duck)
        print(f"Saved: {out_video}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
