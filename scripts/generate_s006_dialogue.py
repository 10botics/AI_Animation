"""
S006 — Frieren-only dialogue from panel balloons (`002.jpg` row 3).

Story: panel_s006jap.png (JP) + panel_s006.png (EN layout).
  Fern: あまり乗り気じゃありませんね。 (not muxed)
  Frieren: 大陸魔法協会も通さない… / 正式な依頼って訳でもなさそうだし、断っちゃっていいんじゃない。

Default: WAV only under outputs/voice/S006/. Use --mux for Kling overlay.
Note: default Kling ~5s — full JP two-balloon audio may exceed clip; use --balloon 1 or 10s I2V.

Usage:
  cd scripts
  python generate_s006_dialogue.py --skip-clone --language Japanese --tag frieren_dialogue_v1_ja
  python generate_s006_dialogue.py --mux --video ..\\outputs\\video\\final\\S006_kling....mp4 --balloon 1
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
    FRIEREN_S006_DIALOGUE_START_SEC,
    FRIEREN_S006_LANGUAGE,
    FRIEREN_S006_PAUSE_SEC,
    FRIEREN_S006_PHRASES,
    FRIEREN_S006_PHRASES_EN,
    FRIEREN_S006_PROMPT,
    FRIEREN_S006_PROMPT_EN,
    FRIEREN_S006_PAUSE_SEC_COMPACT,
    FRIEREN_S006_PROMPT_PART1,
    FRIEREN_S006_PROMPT_PART1_COMPACT,
    FRIEREN_S006_PROMPT_PART1_EN,
    FRIEREN_S006_PROMPT_PART2,
    FRIEREN_S006_PROMPT_PART2_COMPACT,
    FRIEREN_S006_PROMPT_PART2_EN,
    load_reference_text,
    load_registry,
    resolve_character_embedding,
    synthesize,
    synthesize_s006_frieren,
)


def _s006_phrases_and_prompts(language: str) -> tuple[tuple[str, ...], str, str, str]:
    if language.lower() in ("english", "en"):
        return (
            FRIEREN_S006_PHRASES_EN,
            FRIEREN_S006_PROMPT_EN,
            FRIEREN_S006_PROMPT_PART1_EN,
            FRIEREN_S006_PROMPT_PART2_EN,
        )
    return (
        FRIEREN_S006_PHRASES,
        FRIEREN_S006_PROMPT,
        FRIEREN_S006_PROMPT_PART1,
        FRIEREN_S006_PROMPT_PART2,
    )


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


def _phrases_for_balloon(phrases: tuple[str, ...], balloon: int | None) -> tuple[str, ...]:
    if balloon == 1:
        return (phrases[0],)
    if balloon == 2:
        return (phrases[1],)
    return phrases


def main() -> int:
    parser = argparse.ArgumentParser(description="S006 Qwen3 Frieren dialogue (WAV default)")
    parser.add_argument(
        "--mux",
        action="store_true",
        help="Mux onto --video (default: WAV only)",
    )
    parser.add_argument("--video", type=Path, default=None)
    parser.add_argument("--skip-clone", action="store_true")
    parser.add_argument("--reclone", action="store_true")
    parser.add_argument("--start-sec", type=float, default=FRIEREN_S006_DIALOGUE_START_SEC)
    parser.add_argument("--duck", type=float, default=0.35)
    parser.add_argument(
        "--language",
        choices=("Japanese", "English"),
        default=FRIEREN_S006_LANGUAGE,
    )
    parser.add_argument("--prompt", type=str, default=None)
    parser.add_argument("--pause-sec", type=float, default=None)
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Shorter pause + brisk prompts (~9s target for 10s Kling)",
    )
    parser.add_argument("--single-clip", action="store_true")
    parser.add_argument(
        "--balloon",
        type=int,
        choices=(1, 2),
        default=None,
        help="Balloon 1 or 2 only (fits ~5s Kling)",
    )
    parser.add_argument("--ref-seconds", type=float, default=FRIEREN_ENG_DUB_REF_SECONDS)
    parser.add_argument("--ref-skip", type=float, default=FRIEREN_ENG_DUB_REF_SKIP)
    parser.add_argument("--ref-wav", type=Path, default=None)
    parser.add_argument("--tag", type=str, default=None)
    args = parser.parse_args()

    phrases_all, default_prompt, prompt_p1, prompt_p2 = _s006_phrases_and_prompts(args.language)
    if args.compact and args.language.lower() not in ("english", "en"):
        prompt_p1 = FRIEREN_S006_PROMPT_PART1_COMPACT
        prompt_p2 = FRIEREN_S006_PROMPT_PART2_COMPACT
    if args.pause_sec is None:
        args.pause_sec = (
            FRIEREN_S006_PAUSE_SEC_COMPACT if args.compact else FRIEREN_S006_PAUSE_SEC
        )
    if args.prompt is None:
        args.prompt = default_prompt
    phrases = _phrases_for_balloon(phrases_all, args.balloon)
    line_text = phrases[0] if len(phrases) == 1 else "".join(phrases)

    if not read_fal_key():
        print("Missing FAL_KEY in .env", file=sys.stderr)
        return 1
    os.environ["FAL_KEY"] = read_fal_key() or ""

    ref_path, ref_seconds, ref_skip, reference_text = _resolve_ref(args)

    video: Path | None = None
    if args.mux:
        video = args.video.resolve() if args.video else latest_shot_video("S006")
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
    out_dir = ROOT / "outputs" / "voice" / "S006"
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = args.tag or (
        "frieren_dialogue_ja" if args.balloon is None else f"frieren_dialogue_b{args.balloon}_ja"
    )
    stem = out_dir / f"s006_frieren_{ts}.mp3"

    if len(phrases) == 1:
        prompt = prompt_p1 if args.balloon == 1 else prompt_p2
        audio = synthesize(
            phrases[0],
            emb_url,
            stem,
            prompt=prompt,
            reference_text=reference_text,
            language=args.language,
        )
    elif args.single_clip:
        audio = synthesize(
            line_text,
            emb_url,
            stem,
            prompt=args.prompt,
            reference_text=reference_text,
            language=args.language,
        )
    else:
        audio = synthesize_s006_frieren(
            emb_url,
            stem,
            reference_text=reference_text,
            pause_sec=args.pause_sec,
            prompt_part1=prompt_p1,
            prompt_part2=prompt_p2,
            phrases=phrases_all,
            language=args.language,
        )
    print(f"TTS Frieren: {audio.name}", flush=True)

    audio_dur = probe_duration(audio)
    video_dur = probe_duration(video) if video else None
    if video_dur is not None and audio_dur + args.start_sec > video_dur + 0.05:
        print(
            f"Warning: dialogue ({audio_dur:.1f}s @ {args.start_sec}s) exceeds video ({video_dur:.1f}s) — "
            "output will truncate. Use --balloon 1, longer I2V, or --video.",
            file=sys.stderr,
        )

    wav_path = out_dir / f"s006_frieren_{tag}_{ts}.wav"
    if not args.mux:
        _mp3_to_wav(audio, wav_path)
        print(f"WAV: {wav_path}", flush=True)
        final_dir = ROOT / "outputs" / "voice" / "final" / "S006"
        final_dir.mkdir(parents=True, exist_ok=True)
        final_wav = final_dir / wav_path.name
        final_wav.write_bytes(wav_path.read_bytes())
        print(f"Final: {final_wav}", flush=True)

    meta_payload: dict = {
        "engine": "qwen3-tts-1.7b",
        "mode": "frieren_only",
        "language": args.language,
        "balloon": args.balloon,
        "line_text": line_text,
        "phrases": list(phrases),
        "split_phrases": not args.single_clip and len(phrases) > 1,
        "compact": args.compact,
        "pause_sec": args.pause_sec,
        "start_sec": args.start_sec,
        "audio_duration_sec": audio_dur,
        "qwen_embedding": emb_meta,
        "prompt": args.prompt,
        "reference_text": reference_text,
        "voice_ref": str(ref_path.relative_to(ROOT)),
        "stem": str(audio),
        "wav_only": not args.mux,
    }
    if wav_path and not args.mux:
        meta_payload["wav_output"] = str(wav_path)
        meta_payload["wav_final"] = str(ROOT / "outputs" / "voice" / "final" / "S006" / wav_path.name)
    if video_dur is not None:
        meta_payload["video_duration_sec"] = video_dur
        meta_payload["video_in"] = str(video)

    meta = out_dir / f"s006_{tag}_meta_{ts}.json"
    meta.write_text(json.dumps(meta_payload, indent=2), encoding="utf-8")

    if args.mux and video is not None:
        out_video = video.with_name(f"{video.stem}_{tag}_{ts}.mp4")
        mux_dialogue(video, [(audio, args.start_sec)], out_video, args.duck)
        print(f"Saved: {out_video}", flush=True)
    print(f"Meta: {meta}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
