"""
S012 — Frieren-only dialogue from panel balloons (`003.jpg` bottom tier left).

Story: panel_s012jap.png (JP) — **all balloon tails → Frieren** (center).
  城塞都市ヴァイゼ。 / 噂には聞いていたけど…協会が管理… / 50年前マハト… / 一瞬で黄金に…
  (EN scan often mis-labels the left bubble as Fern.)

Default: WAV only under outputs/voice/S012/. Use --mux for Kling overlay.
Note: default Kling ~5s — full JP may need duration 10 or --single-clip on shorter clip.

Usage:
  cd scripts
  python generate_s012_dialogue.py --skip-clone --language Japanese --tag frieren_dialogue_v1_ja
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
    FRIEREN_ENG_DUB_REF_SECONDS,
    FRIEREN_ENG_DUB_REF_SKIP,
    FRIEREN_QWEN_REF_WAV,
    FRIEREN_S012_DIALOGUE_START_SEC,
    FRIEREN_S012_LANGUAGE,
    FRIEREN_S012_PAUSE_SEC,
    FRIEREN_S012_PHRASES,
    FRIEREN_S012_PHRASES_EN,
    FRIEREN_S012_PROMPT,
    FRIEREN_S012_PROMPT_EN,
    FRIEREN_S012_PROMPTS,
    FRIEREN_S012_PROMPTS_EN,
    load_reference_text,
    load_registry,
    resolve_character_embedding,
    synthesize,
    synthesize_s012_frieren,
)


def _s012_phrases_and_prompts(language: str) -> tuple[tuple[str, ...], str, tuple[str, ...]]:
    if language.lower() in ("english", "en"):
        return FRIEREN_S012_PHRASES_EN, FRIEREN_S012_PROMPT_EN, FRIEREN_S012_PROMPTS_EN
    return FRIEREN_S012_PHRASES, FRIEREN_S012_PROMPT, FRIEREN_S012_PROMPTS


def _resolve_ref(args: argparse.Namespace) -> tuple[Path, float, float, str | None]:
    ref_path = args.ref_wav.resolve() if args.ref_wav else FRIEREN_QWEN_REF_WAV
    ref_seconds = args.ref_seconds
    ref_skip = args.ref_skip
    if args.ref_wav is None and ref_path == FRIEREN_QWEN_REF_WAV:
        try:
            from qwen_tts import _ref_duration

            ref_seconds = _ref_duration(FRIEREN_QWEN_REF_WAV)
            ref_skip = 0.0
        except Exception:
            ref_seconds = 12.0
            ref_skip = 0.0
    elif args.ref_wav is None and args.ref_seconds != FRIEREN_ENG_DUB_REF_SECONDS:
        ref_path = ROOT / "voice_refs" / f"frieren_eng_dub_ref_{int(args.ref_seconds)}s.wav"

    reference_text: str | None = None
    ref_txt = ref_path.with_suffix(".txt")
    if ref_path == FRIEREN_QWEN_REF_WAV:
        reference_text = load_reference_text()
    elif ref_txt.is_file():
        reference_text = ref_txt.read_text(encoding="utf-8-sig").strip()
    return ref_path, ref_seconds, ref_skip, reference_text


def _mp3_to_wav(mp3: Path, wav: Path) -> Path:
    wav.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(mp3), "-ac", "1", "-ar", "44100", str(wav)],
        check=True,
        capture_output=True,
    )
    return wav


def main() -> int:
    parser = argparse.ArgumentParser(description="S012 Qwen3 Frieren dialogue (WAV default)")
    parser.add_argument("--mux", action="store_true")
    parser.add_argument("--video", type=Path, default=None)
    parser.add_argument("--skip-clone", action="store_true")
    parser.add_argument("--reclone", action="store_true")
    parser.add_argument("--start-sec", type=float, default=FRIEREN_S012_DIALOGUE_START_SEC)
    parser.add_argument("--duck", type=float, default=0.35)
    parser.add_argument(
        "--language",
        choices=("Japanese", "English"),
        default=FRIEREN_S012_LANGUAGE,
    )
    parser.add_argument("--prompt", type=str, default=None)
    parser.add_argument("--pause-sec", type=float, default=FRIEREN_S012_PAUSE_SEC)
    parser.add_argument("--single-clip", action="store_true")
    parser.add_argument("--ref-seconds", type=float, default=FRIEREN_ENG_DUB_REF_SECONDS)
    parser.add_argument("--ref-skip", type=float, default=FRIEREN_ENG_DUB_REF_SKIP)
    parser.add_argument("--ref-wav", type=Path, default=None)
    parser.add_argument("--tag", type=str, default=None)
    args = parser.parse_args()

    phrases, default_prompt, prompts = _s012_phrases_and_prompts(args.language)
    if args.prompt is None:
        args.prompt = default_prompt
    line_text = "".join(phrases)

    if not read_fal_key():
        print("Missing FAL_KEY in .env", file=sys.stderr)
        return 1
    os.environ["FAL_KEY"] = read_fal_key() or ""

    ref_path, ref_seconds, ref_skip, reference_text = _resolve_ref(args)

    video: Path | None = None
    if args.mux:
        video = args.video.resolve() if args.video else latest_shot_video("S012")
        if not video.is_file():
            print(f"Video not found: {video}", file=sys.stderr)
            return 1

    if args.reclone or not args.skip_clone:
        emb_url, emb_meta = resolve_character_embedding(
            "Frieren",
            ref_wav=ref_path,
            ref_seconds=ref_seconds,
            ref_skip=ref_skip,
            force_reclone=args.reclone,
            reference_text=reference_text,
        )
    else:
        reg = load_registry()
        entry = (reg.get("qwen_speaker_embeddings") or {}).get("Frieren")
        if not entry or not entry.get("url"):
            print("No Frieren Qwen embedding — run without --skip-clone", file=sys.stderr)
            return 1
        emb_url = str(entry["url"])
        emb_meta = entry
        reference_text = (entry.get("reference_text") or reference_text or "").strip() or None

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "outputs" / "voice" / "S012"
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = args.tag or "frieren_dialogue_ja"
    stem = out_dir / f"s012_frieren_{ts}.mp3"

    if args.single_clip:
        audio = synthesize(
            line_text,
            emb_url,
            stem,
            prompt=args.prompt,
            reference_text=reference_text,
            language=args.language,
        )
    else:
        audio = synthesize_s012_frieren(
            emb_url,
            stem,
            reference_text=reference_text,
            pause_sec=args.pause_sec,
            prompts=prompts,
            phrases=phrases,
            language=args.language,
        )
    print(f"TTS Frieren: {audio.name}", flush=True)

    audio_dur = probe_duration(audio)
    video_dur = probe_duration(video) if video else None
    if video_dur is not None and audio_dur + args.start_sec > video_dur + 0.05:
        print(
            f"Warning: dialogue ({audio_dur:.1f}s @ {args.start_sec}s) exceeds video ({video_dur:.1f}s) — "
            "use --duration 10 I2V or --single-clip on a shorter base.",
            file=sys.stderr,
        )

    wav_path = out_dir / f"s012_frieren_{tag}_{ts}.wav"
    if not args.mux:
        _mp3_to_wav(audio, wav_path)
        print(f"WAV: {wav_path}", flush=True)

    meta_payload: dict = {
        "engine": "qwen3-tts-1.7b",
        "mode": "frieren_only",
        "language": args.language,
        "line_text": line_text,
        "phrases": list(phrases),
        "split_phrases": not args.single_clip,
        "pause_sec": args.pause_sec,
        "start_sec": args.start_sec,
        "audio_duration_sec": audio_dur,
        "qwen_embedding": emb_meta,
        "prompt": args.prompt,
        "reference_text": reference_text,
        "voice_ref": str(ref_path.relative_to(ROOT)),
        "stem": str(audio),
        "wav_only": not args.mux,
        "panel_story_ref": "panels/jap/panel_s012jap.png",
    }
    if not args.mux:
        meta_payload["wav_output"] = str(wav_path)
    if video_dur is not None:
        meta_payload["video_duration_sec"] = video_dur
        meta_payload["video_in"] = str(video)

    meta = out_dir / f"s012_{tag}_meta_{ts}.json"
    meta.write_text(json.dumps(meta_payload, indent=2), encoding="utf-8")

    if args.mux and video is not None:
        out_video = video.with_name(f"{video.stem}_{tag}_{ts}.mp4")
        mux_dialogue(video, [(audio, args.start_sec)], out_video, args.duck)
        print(f"Saved: {out_video}", flush=True)
    print(f"Meta: {meta}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
