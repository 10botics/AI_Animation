"""
S008 — dialogue test from panel balloons (003.jpg grimoire bribe).

Story (B3 / stage_02 S008): panel_s008jap.png (JP) + panel_s008.png (EN layout).
  Fern: 報酬の魔導書も一緒に送られてきていますけれども… / EN: grimoire reward …though…
  Frieren: よし。やるか。 (default TTS) · EN: --language English
  Stark: えぇ… / EN: "Eh?"

Voice ref: fireren Japan.mp4 → Voice Reference/Japanese/Frieren/frieren_jp_qwen_ref.wav

Frieren voice: **Qwen3 TTS** (clone + TTS, default language Japanese).
Fern/Stark (--all-speakers): MiniMax preset voices.

Default: **WAV only** under `outputs/voice/S008/` (no video mux). Use `--mux` to burn onto Kling.

Usage:
  cd scripts
  python generate_s008_dialogue.py --skip-clone
  python generate_s008_dialogue.py --mux --video ..\outputs\video\final\S008_kling....mp4
  python generate_s008_dialogue.py --prompt "Quiet flat delivery. Dry witty tone."
  python generate_s008_dialogue.py --all-speakers
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import fal_client

from dialogue_mux import latest_shot_video, mux_dialogue
from fal_common import ROOT, download_file, read_fal_key
from qwen_tts import (
    FRIEREN_S008_LANGUAGE,
    FRIEREN_S008_PAUSE_SEC,
    FRIEREN_S008_PHRASES,
    FRIEREN_S008_PHRASES_EN,
    FRIEREN_S008_PROMPT,
    FRIEREN_S008_PROMPT_EN,
    FRIEREN_S008_PROMPT_PART1,
    FRIEREN_S008_PROMPT_PART1_EN,
    FRIEREN_S008_PROMPT_PART2,
    FRIEREN_S008_PROMPT_PART2_EN,
    FRIEREN_DIALOGUE_START_SEC,
    FRIEREN_ENG_DUB_REF_SECONDS,
    FRIEREN_ENG_DUB_REF_SKIP,
    FRIEREN_ENG_DUB_REF_WAV,
    FRIEREN_QWEN_REF_WAV,
    load_reference_text,
    load_registry,
    resolve_character_embedding,
    synthesize,
    synthesize_s008_frieren,
)

MINIMAX_TTS = "fal-ai/minimax-tts/text-to-speech"
REGISTRY_PATH = ROOT / "voice_registry.local.json"
VOICE_REF_ENG_DUB = FRIEREN_QWEN_REF_WAV
ENG_DUB_REF_SECONDS = FRIEREN_ENG_DUB_REF_SECONDS
ENG_DUB_REF_SKIP = FRIEREN_ENG_DUB_REF_SKIP
def _s008_phrases_and_prompts(language: str) -> tuple[tuple[str, ...], str, str, str]:
    if language.lower() in ("english", "en"):
        return (
            FRIEREN_S008_PHRASES_EN,
            FRIEREN_S008_PROMPT_EN,
            FRIEREN_S008_PROMPT_PART1_EN,
            FRIEREN_S008_PROMPT_PART2_EN,
        )
    return (
        FRIEREN_S008_PHRASES,
        FRIEREN_S008_PROMPT,
        FRIEREN_S008_PROMPT_PART1,
        FRIEREN_S008_PROMPT_PART2,
    )

S008_ALL_LINES = [
    {
        "speaker": "Fern",
        "text": "A grimoire reward was included with the request, though...",
        "voice_id": "Lovely_Girl",
        "emotion": "neutral",
        "speed": 1.0,
        "start_sec": 0.0,
    },
    {
        "speaker": "Frieren",
        "text": "".join(FRIEREN_S008_PHRASES),
        "custom": True,
        "start_sec": 1.55,
    },
    {
        "speaker": "Stark",
        "text": "Eh?",
        "voice_id": "Casual_Guy",
        "emotion": "neutral",
        "speed": 1.0,
        "start_sec": 3.35,
    },
]


def _ensure_frieren_embedding(
    force: bool,
    ref_seconds: float,
    ref_skip: float,
    ref_path: Path,
    reference_text: str | None,
) -> tuple[str, dict]:
    return resolve_character_embedding(
        "Frieren",
        ref_wav=ref_path,
        ref_seconds=ref_seconds,
        ref_skip=ref_skip,
        force_reclone=force,
        reference_text=reference_text,
    )


def _mp3_to_wav(mp3: Path, wav: Path) -> Path:
    wav.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(mp3), "-ac", "1", "-ar", "44100", str(wav)],
        check=True,
        capture_output=True,
    )
    return wav


def _tts_minimax_line(line: dict, out: Path) -> None:
    vs: dict = {"emotion": line["emotion"], "speed": line["speed"], "voice_id": line["voice_id"]}
    result = fal_client.subscribe(
        MINIMAX_TTS,
        arguments={
            "text": line["text"],
            "voice_setting": vs,
            "language_boost": "English",
        },
        with_logs=True,
    )
    audio = result.get("audio") if isinstance(result, dict) else None
    if not isinstance(audio, dict) or not audio.get("url"):
        print(f"TTS failed for {line['speaker']}: {result}", file=sys.stderr)
        sys.exit(1)
    download_file(audio["url"], out)
    print(f"TTS {line['speaker']}: {out.name}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="S008 Qwen3 Frieren dialogue (WAV default)")
    parser.add_argument(
        "--mux",
        action="store_true",
        help="Mux dialogue onto --video (default: WAV only, no MP4)",
    )
    parser.add_argument("--video", type=Path, default=None, help="Required with --mux")
    parser.add_argument("--skip-clone", action="store_true")
    parser.add_argument("--reclone", action="store_true", help="Fresh Qwen embedding from eng dub ref")
    parser.add_argument("--all-speakers", action="store_true")
    parser.add_argument("--start-sec", type=float, default=None)
    parser.add_argument("--duck", type=float, default=0.35)
    parser.add_argument(
        "--language",
        choices=("Japanese", "English"),
        default=FRIEREN_S008_LANGUAGE,
        help="TTS language (default Japanese for S008 manga line)",
    )
    parser.add_argument("--prompt", type=str, default=None, help="Qwen delivery hint (single-clip; default from --language)")
    parser.add_argument(
        "--pause-sec",
        type=float,
        default=FRIEREN_S008_PAUSE_SEC,
        help="Silence between S008 phrases (split TTS; default from qwen_tts)",
    )
    parser.add_argument(
        "--single-clip",
        action="store_true",
        help="One TTS call for full line (old behavior; shorter inter-phrase pause)",
    )
    parser.add_argument("--ref-seconds", type=float, default=ENG_DUB_REF_SECONDS)
    parser.add_argument("--ref-skip", type=float, default=ENG_DUB_REF_SKIP)
    parser.add_argument(
        "--ref-wav",
        type=Path,
        default=None,
        help="Override ref path (default: voice_refs/frieren_eng_dub_ref_<N>s.wav)",
    )
    parser.add_argument("--tag", type=str, default=None, help="Suffix on output filename")
    args = parser.parse_args()
    phrases, default_prompt, prompt_p1, prompt_p2 = _s008_phrases_and_prompts(args.language)
    frieren_line_text = "".join(phrases)
    if args.prompt is None:
        args.prompt = default_prompt

    if not read_fal_key():
        print("Missing FAL_KEY in .env", file=sys.stderr)
        return 1
    os.environ["FAL_KEY"] = read_fal_key() or ""

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
    elif args.ref_wav is None and args.ref_seconds != ENG_DUB_REF_SECONDS:
        ref_path = ROOT / "voice_refs" / f"frieren_eng_dub_ref_{int(args.ref_seconds)}s.wav"

    reference_text: str | None = None
    ref_txt = ref_path.with_suffix(".txt")
    if ref_path == FRIEREN_QWEN_REF_WAV:
        reference_text = load_reference_text()
    elif ref_txt.is_file():
        reference_text = ref_txt.read_text(encoding="utf-8-sig").strip()

    video: Path | None = None
    if args.mux:
        video = args.video.resolve() if args.video else latest_shot_video("S008")
        if not video.is_file():
            print(f"Video not found: {video}", file=sys.stderr)
            return 1

    if args.reclone or not args.skip_clone:
        emb_url, emb_meta = _ensure_frieren_embedding(
            force=args.reclone,
            ref_seconds=ref_seconds,
            ref_skip=ref_skip,
            ref_path=ref_path,
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
    out_dir = ROOT / "outputs" / "voice" / "S008"
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.all_speakers:
        lines = S008_ALL_LINES
        tag = args.tag or "dialogue"
    else:
        frieren = {
            "speaker": "Frieren",
            "text": frieren_line_text,
            "custom": True,
            "start_sec": FRIEREN_DIALOGUE_START_SEC,
        }
        if args.start_sec is not None:
            frieren["start_sec"] = args.start_sec
        lines = [frieren]
        tag = args.tag or "frieren_dialogue"

    stems: list[tuple[Path, float]] = []
    for line in lines:
        stem = out_dir / f"s008_{line['speaker'].lower()}_{ts}.mp3"
        if line.get("custom"):
            if args.single_clip:
                audio = synthesize(
                    line["text"],
                    emb_url,
                    stem,
                    prompt=args.prompt,
                    reference_text=reference_text,
                    language=args.language,
                )
            else:
                audio = synthesize_s008_frieren(
                    emb_url,
                    stem,
                    reference_text=reference_text,
                    pause_sec=args.pause_sec,
                    prompt_part1=prompt_p1,
                    prompt_part2=prompt_p2,
                    phrases=phrases,
                    language=args.language,
                )
            print(f"TTS {line['speaker']}: {audio.name}", flush=True)
        else:
            _tts_minimax_line(line, stem)
        stems.append((stem, line["start_sec"]))

    wav_outputs: list[Path] = []
    if not args.mux:
        for i, (stem_path, _) in enumerate(stems):
            speaker = lines[i]["speaker"].lower()
            wav_path = out_dir / f"s008_{speaker}_{tag}_{ts}.wav"
            if stem_path.suffix.lower() == ".mp3":
                _mp3_to_wav(stem_path, wav_path)
            else:
                wav_path.write_bytes(stem_path.read_bytes())
            wav_outputs.append(wav_path)
            print(f"WAV: {wav_path}", flush=True)

    meta = out_dir / f"s008_{tag}_meta_{ts}.json"
    meta_payload: dict = {
                "engine": "qwen3-tts-1.7b",
                "mode": "all_speakers" if args.all_speakers else "frieren_only",
                "lines": lines,
                "qwen_embedding": emb_meta,
                "prompt": args.prompt,
                "pause_sec": args.pause_sec,
                "split_phrases": not args.single_clip,
                "language": args.language,
                "phrases": list(phrases),
                "reference_text": reference_text,
                "voice_ref": str(ref_path.relative_to(ROOT)),
                "ref_seconds": ref_seconds,
                "ref_skip": ref_skip,
                "line_text": frieren_line_text,
                "stems": [str(p) for p, _ in stems],
                "wav_only": not args.mux,
            }
    if wav_outputs:
        meta_payload["wav_outputs"] = [str(p) for p in wav_outputs]
    if video is not None:
        meta_payload["video_in"] = str(video)
    meta.write_text(json.dumps(meta_payload, indent=2), encoding="utf-8")

    if args.mux and video is not None:
        out_video = video.with_name(f"{video.stem}_{tag}_{ts}.mp4")
        mux_dialogue(video, stems, out_video, args.duck)
        print(f"Saved: {out_video}", flush=True)
    print(f"Meta: {meta}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
