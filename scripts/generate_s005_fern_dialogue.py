"""
S005 — Fern dialogue from panel_s005jap.png (JP balloons).

  いえ、
  一級魔法使いレルネン様からの
  個人的な依頼のようです。

Default: WAV under outputs/voice/S005/ + copy to outputs/voice/final/S005/.

Usage:
  cd scripts
  python generate_s005_fern_dialogue.py --skip-clone --tag fern_dialogue_v1_ja
  python generate_s005_fern_dialogue.py --mux --video ..\\outputs\\video\\final\\S005_kling....mp4
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
    FERN_QWEN_REF_WAV,
    FERN_S005_DIALOGUE_START_SEC,
    FERN_S005_LANGUAGE,
    FERN_S005_PAUSE_SEC,
    FERN_S005_PHRASES,
    FERN_S005_PHRASES_EN,
    FERN_S005_PROMPTS,
    FERN_S005_PROMPTS_EN,
    load_fern_reference_text,
    load_registry,
    resolve_fern_embedding,
    synthesize_s005_fern,
)


def _phrases_prompts(language: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if language.lower() in ("english", "en"):
        return FERN_S005_PHRASES_EN, FERN_S005_PROMPTS_EN
    return FERN_S005_PHRASES, FERN_S005_PROMPTS


def main() -> int:
    parser = argparse.ArgumentParser(description="S005 Qwen3 Fern dialogue (WAV default)")
    parser.add_argument("--mux", action="store_true")
    parser.add_argument("--video", type=Path, default=None)
    parser.add_argument("--skip-clone", action="store_true")
    parser.add_argument("--reclone", action="store_true")
    parser.add_argument("--start-sec", type=float, default=FERN_S005_DIALOGUE_START_SEC)
    parser.add_argument("--pause-sec", type=float, default=FERN_S005_PAUSE_SEC)
    parser.add_argument(
        "--language",
        choices=("Japanese", "English"),
        default=FERN_S005_LANGUAGE,
    )
    parser.add_argument("--tag", type=str, default=None)
    args = parser.parse_args()

    phrases, prompts = _phrases_prompts(args.language)
    line_text = "".join(phrases) if args.language == "Japanese" else " ".join(phrases)

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
        video = args.video.resolve() if args.video else latest_shot_video("S005")
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
    out_dir = ROOT / "outputs" / "voice" / "S005"
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = args.tag or "fern_dialogue_ja"
    stem = out_dir / f"s005_fern_{ts}.mp3"
    wav_path = out_dir / f"s005_fern_{tag}_{ts}.wav"

    synthesize_s005_fern(
        emb_url,
        stem,
        wav_path,
        phrases=phrases,
        prompts=prompts,
        pause_sec=args.pause_sec,
        language=args.language,
    )
    print(f"TTS Fern S005: {stem.name}", flush=True)

    audio_dur = probe_duration(wav_path)
    video_dur = probe_duration(video) if video else None

    if not args.mux:
        print(f"WAV: {wav_path}", flush=True)
        final_dir = ROOT / "outputs" / "voice" / "final" / "S005"
        final_dir.mkdir(parents=True, exist_ok=True)
        final_wav = final_dir / wav_path.name
        final_wav.write_bytes(wav_path.read_bytes())
        print(f"Final: {final_wav}", flush=True)

    meta_payload: dict = {
        "engine": "qwen3-tts-1.7b",
        "mode": "fern_s005_split",
        "language": args.language,
        "line_text": line_text,
        "phrases": list(phrases),
        "pause_sec": args.pause_sec,
        "start_sec": args.start_sec,
        "audio_duration_sec": audio_dur,
        "qwen_embedding": emb_meta,
        "reference_text_clone_only": reference_text,
        "reference_text_on_tts": False,
        "wav_export": "export_dialogue_wav (24kHz mono PCM)",
        "voice_ref": str(FERN_QWEN_REF_WAV.relative_to(ROOT)),
        "panel_story_ref": "panels/jap/panel_s005jap.png",
        "personality_guide": "docs/fern-qwen-personality-guide.md",
    }
    if not args.mux:
        meta_payload["wav_output"] = str(wav_path)
        meta_payload["wav_final"] = str(ROOT / "outputs" / "voice" / "final" / "S005" / wav_path.name)
    if video_dur is not None:
        meta_payload["video_duration_sec"] = video_dur
        meta_payload["video_in"] = str(video)

    meta = out_dir / f"s005_{tag}_meta_{ts}.json"
    meta.write_text(json.dumps(meta_payload, indent=2), encoding="utf-8")
    print(f"Meta: {meta}", flush=True)

    if args.mux and video is not None:
        out_video = video.with_name(f"{video.stem}_{tag}_{ts}.mp4")
        mux_dialogue(video, [(stem, args.start_sec)], out_video, 0.35)
        print(f"Saved: {out_video}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
