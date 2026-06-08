"""
S012 — Stark reaction stem (Japanese) for wide backs + gilt Weise (B3).

No Stark balloon on panel_s012jap.png — scene stem per docs/stark-qwen-personality-guide.md.
Voice ref: Voice Reference/Japanese/Stark/stark_jp_qwen_ref.wav + stark_jp_qwen_ref.txt

Usage:
  cd scripts
  python generate_s012_stark_dialogue.py --skip-clone --language Japanese --tag stark_dialogue_v2_ja
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from dialogue_mux import latest_shot_video, mux_dialogue, probe_duration
from fal_common import ROOT, read_fal_key
from qwen_tts import (
    STARK_QWEN_REF_WAV,
    STARK_S012_DIALOGUE_START_SEC,
    STARK_S012_LANGUAGE,
    STARK_S012_PAUSE_SEC,
    STARK_S012_PHRASES,
    STARK_S012_PHRASES_EN,
    STARK_S012_PROMPT,
    STARK_S012_PROMPT_EN,
    STARK_S012_PROMPTS,
    load_stark_reference_text,
    load_registry,
    resolve_stark_embedding,
    synthesize,
    synthesize_s012_stark,
)


def _phrases_prompts(language: str) -> tuple[tuple[str, ...], str, tuple[str, ...]]:
    if language.lower() in ("english", "en"):
        return STARK_S012_PHRASES_EN, STARK_S012_PROMPT_EN, STARK_S012_PROMPTS
    return STARK_S012_PHRASES, STARK_S012_PROMPT, STARK_S012_PROMPTS


def _mp3_to_wav(mp3: Path, wav: Path) -> Path:
    wav.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(mp3), "-ac", "1", "-ar", "44100", str(wav)],
        check=True,
        capture_output=True,
    )
    return wav


def main() -> int:
    parser = argparse.ArgumentParser(description="S012 Qwen3 Stark reaction (WAV default)")
    parser.add_argument("--mux", action="store_true")
    parser.add_argument("--video", type=Path, default=None)
    parser.add_argument("--skip-clone", action="store_true")
    parser.add_argument("--reclone", action="store_true")
    parser.add_argument("--start-sec", type=float, default=STARK_S012_DIALOGUE_START_SEC)
    parser.add_argument("--duck", type=float, default=0.35)
    parser.add_argument(
        "--language",
        choices=("Japanese", "English"),
        default=STARK_S012_LANGUAGE,
    )
    parser.add_argument("--prompt", type=str, default=None)
    parser.add_argument("--pause-sec", type=float, default=STARK_S012_PAUSE_SEC)
    parser.add_argument("--single-clip", action="store_true", help="One TTS call (v1-style)")
    parser.add_argument("--tag", type=str, default=None)
    args = parser.parse_args()

    phrases, default_prompt, prompts = _phrases_prompts(args.language)
    if args.prompt is None:
        args.prompt = default_prompt
    line_text = "".join(phrases)

    if not read_fal_key():
        print("Missing FAL_KEY in .env", file=sys.stderr)
        return 1
    os.environ["FAL_KEY"] = read_fal_key() or ""

    video: Path | None = None
    if args.mux:
        video = args.video.resolve() if args.video else latest_shot_video("S012")
        if not video.is_file():
            print(f"Video not found: {video}", file=sys.stderr)
            return 1

    if args.reclone or not args.skip_clone:
        emb_url, emb_meta = resolve_stark_embedding(force_reclone=args.reclone)
        reference_text = load_stark_reference_text()
    else:
        reg = load_registry()
        entry = (reg.get("qwen_speaker_embeddings") or {}).get("Stark")
        if not entry or not entry.get("url"):
            print("No Stark Qwen embedding — run without --skip-clone", file=sys.stderr)
            return 1
        emb_url = str(entry["url"])
        emb_meta = entry
        reference_text = (entry.get("reference_text") or "").strip() or load_stark_reference_text()

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "outputs" / "voice" / "S012"
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = args.tag or "stark_dialogue_ja"
    stem = out_dir / f"s012_stark_{ts}.mp3"

    if args.single_clip:
        audio = synthesize(
            line_text,
            emb_url,
            stem,
            prompt=args.prompt,
            reference_text=None,
            language=args.language,
        )
    else:
        audio = synthesize_s012_stark(
            emb_url,
            stem,
            reference_text=None,
            pause_sec=args.pause_sec,
            prompts=prompts,
            phrases=phrases,
            language=args.language,
        )
    print(f"TTS Stark: {audio.name}", flush=True)

    audio_dur = probe_duration(audio)
    video_dur = probe_duration(video) if video else None
    if video_dur is not None and audio_dur + args.start_sec > video_dur + 0.05:
        print(
            f"Warning: dialogue ({audio_dur:.1f}s @ {args.start_sec}s) exceeds video ({video_dur:.1f}s)",
            file=sys.stderr,
        )

    wav_path = out_dir / f"s012_stark_{tag}_{ts}.wav"
    if not args.mux:
        _mp3_to_wav(audio, wav_path)
        print(f"WAV: {wav_path}", flush=True)

    meta_payload: dict = {
        "engine": "qwen3-tts-1.7b",
        "mode": "stark_reaction",
        "language": args.language,
        "line_text": line_text,
        "phrases": list(phrases),
        "split_phrases": not args.single_clip,
        "pause_sec": args.pause_sec,
        "personality_guide": "docs/stark-qwen-personality-guide.md",
        "start_sec": args.start_sec,
        "audio_duration_sec": audio_dur,
        "qwen_embedding": emb_meta,
        "prompt": args.prompt,
        "reference_text_clone_only": reference_text,
        "voice_ref": str(STARK_QWEN_REF_WAV.relative_to(ROOT)),
        "stem": str(audio),
        "wav_only": not args.mux,
        "panel_story_ref": "panels/jap/panel_s012jap.png",
        "note": "No Stark balloon on panel — scene-authored B3 awe line.",
    }
    if not args.mux:
        meta_payload["wav_output"] = str(wav_path)
    if video_dur is not None:
        meta_payload["video_duration_sec"] = video_dur
        meta_payload["video_in"] = str(video)

    meta = out_dir / f"s012_stark_{tag}_meta_{ts}.json"
    meta.write_text(json.dumps(meta_payload, indent=2), encoding="utf-8")

    if args.mux and video is not None:
        out_video = video.with_name(f"{video.stem}_{tag}_{ts}.mp4")
        mux_dialogue(video, [(audio, args.start_sec)], out_video, args.duck)
        print(f"Saved: {out_video}", flush=True)
    print(f"Meta: {meta}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
