"""
S016 — Frieren-only dialogue from forest-meet balloon (`004.jpg` row 2).

Story: panels/jap/panel_s015jap.png (JP balloon) — panel crop id s015; shot list S016.
  Frieren: まさかデンケンだったとはね。 / EN: To think it was Denken.

Default: WAV only under outputs/voice/S016/. Use --mux for Kling overlay.

Usage:
  cd scripts
  python generate_s016_dialogue.py --skip-clone --language Japanese --tag frieren_dialogue_v1_ja
  python generate_s016_dialogue.py --mux --video ..\\outputs\\video\\final\\S016_kling....mp4
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
    FRIEREN_ENG_DUB_REF_SECONDS,
    FRIEREN_ENG_DUB_REF_SKIP,
    FRIEREN_QWEN_REF_WAV,
    FRIEREN_S016_DIALOGUE_START_SEC,
    FRIEREN_S016_LANGUAGE,
    FRIEREN_S016_PHRASES,
    FRIEREN_S016_PHRASES_EN,
    FRIEREN_S016_PROMPT,
    FRIEREN_S016_PROMPT_EN,
    load_reference_text,
    load_registry,
    resolve_character_embedding,
    synthesize_s016_frieren,
)


def _s016_line_and_prompt(language: str) -> tuple[str, str]:
    if language.lower() in ("english", "en"):
        return FRIEREN_S016_PHRASES_EN[0], FRIEREN_S016_PROMPT_EN
    return FRIEREN_S016_PHRASES[0], FRIEREN_S016_PROMPT


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


def main() -> int:
    parser = argparse.ArgumentParser(description="S016 Qwen3 Frieren dialogue (WAV default)")
    parser.add_argument("--mux", action="store_true", help="Mux onto --video (default: WAV only)")
    parser.add_argument("--video", type=Path, default=None)
    parser.add_argument("--skip-clone", action="store_true")
    parser.add_argument("--reclone", action="store_true")
    parser.add_argument("--start-sec", type=float, default=FRIEREN_S016_DIALOGUE_START_SEC)
    parser.add_argument("--duck", type=float, default=0.35)
    parser.add_argument(
        "--language",
        choices=("Japanese", "English"),
        default=FRIEREN_S016_LANGUAGE,
    )
    parser.add_argument("--prompt", type=str, default=None)
    parser.add_argument("--ref-seconds", type=float, default=FRIEREN_ENG_DUB_REF_SECONDS)
    parser.add_argument("--ref-skip", type=float, default=FRIEREN_ENG_DUB_REF_SKIP)
    parser.add_argument("--ref-wav", type=Path, default=None)
    parser.add_argument("--tag", type=str, default=None)
    args = parser.parse_args()

    line_text, default_prompt = _s016_line_and_prompt(args.language)
    prompt = args.prompt or default_prompt

    if not read_fal_key():
        print("Missing FAL_KEY in .env", file=sys.stderr)
        return 1
    os.environ["FAL_KEY"] = read_fal_key() or ""

    ref_path, ref_seconds, ref_skip, reference_text = _resolve_ref(args)

    video: Path | None = None
    if args.mux:
        video = args.video.resolve() if args.video else latest_shot_video("S016")
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
    out_dir = ROOT / "outputs" / "voice" / "S016"
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = args.tag or "frieren_dialogue_ja"
    stem = out_dir / f"s016_frieren_{ts}.mp3"

    wav_path = out_dir / f"s016_frieren_{tag}_{ts}.wav"
    synthesize_s016_frieren(
        emb_url,
        stem,
        wav_path,
        prompt=prompt,
        phrase=line_text,
        language=args.language,
    )
    print(f"TTS Frieren: {stem.name}", flush=True)

    audio_dur = probe_duration(wav_path)
    video_dur = probe_duration(video) if video else None
    if video_dur is not None and audio_dur + args.start_sec > video_dur + 0.05:
        print(
            f"Warning: dialogue ({audio_dur:.1f}s @ {args.start_sec}s) exceeds video ({video_dur:.1f}s) — "
            "output will truncate.",
            file=sys.stderr,
        )

    if not args.mux:
        print(f"WAV: {wav_path}", flush=True)
        final_dir = ROOT / "outputs" / "voice" / "final" / "S016"
        final_dir.mkdir(parents=True, exist_ok=True)
        final_wav = final_dir / wav_path.name
        final_wav.write_bytes(wav_path.read_bytes())
        print(f"Final: {final_wav}", flush=True)

    meta_payload: dict = {
        "engine": "qwen3-tts-1.7b",
        "mode": "frieren_only",
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
        "voice_ref": str(ref_path.relative_to(ROOT)),
        "stem": str(stem),
        "wav_only": not args.mux,
        "panel_story_ref": "panels/jap/panel_s015jap.png",
        "shot_list_id": "S016",
    }
    if not args.mux:
        meta_payload["wav_output"] = str(wav_path)
        meta_payload["wav_final"] = str(ROOT / "outputs" / "voice" / "final" / "S016" / wav_path.name)
    if video_dur is not None:
        meta_payload["video_duration_sec"] = video_dur
        meta_payload["video_in"] = str(video)

    meta = out_dir / f"s016_{tag}_meta_{ts}.json"
    meta.write_text(json.dumps(meta_payload, indent=2), encoding="utf-8")

    if args.mux and video is not None:
        out_video = video.with_name(f"{video.stem}_{tag}_{ts}.mp4")
        mux_dialogue(video, [(stem, args.start_sec)], out_video, args.duck)
        print(f"Saved: {out_video}", flush=True)
    print(f"Meta: {meta}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
