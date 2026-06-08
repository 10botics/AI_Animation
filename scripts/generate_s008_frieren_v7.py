"""
S008 Frieren v7 — Qwen from Fal-Demucs isolated 1min dub (voice Frieren1min.mp4).

Source chain:
  voice Frieren1min.mp4 -> isolate_vocals_fal.py -> frieren_1min_vocals.wav
  -> VAD 12s window + Whisper reference_text -> Qwen clone + TTS

Compare:
  v4 outputs/voice/S008/iterations/S008_frieren_qwen_v4_20260602T035231Z.mp4

Usage:
  cd scripts
  python generate_s008_frieren_v7.py
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from fal_common import ROOT, read_fal_key
from dialogue_mux import latest_shot_video, mux_dialogue
from generate_s008_dialogue import FRIEREN_LINE_TEXT
from qwen_tts import DEFAULT_PROMPT, FRIEREN_DIALOGUE_START_SEC, FRIEREN_S008_PROMPT, resolve_character_embedding, synthesize

from voice_paths import VR_EN_FRIEREN, VOICE_REFS_WORK

VOCALS_SRC = VOICE_REFS_WORK / "frieren_1min_vocals.wav"
REF_WAV = VR_EN_FRIEREN / "frieren_1min_qwen_ref.wav"
REF_TXT = VR_EN_FRIEREN / "frieren_1min_qwen_ref.txt"
REF_META = VR_EN_FRIEREN / "frieren_1min_qwen_ref.json"
OUT_DIR = ROOT / "outputs" / "voice" / "S008" / "iterations"


def main() -> int:
    parser = argparse.ArgumentParser(description="S008 Frieren Qwen v7 (1min isolated vocals)")
    parser.add_argument("--skip-ref-prep", action="store_true")
    parser.add_argument("--reclone", action="store_true", default=True)
    parser.add_argument("--no-reclone", action="store_true")
    parser.add_argument("--duck", type=float, default=0.35)
    parser.add_argument("--video", type=Path, default=None)
    args = parser.parse_args()
    reclone = args.reclone and not args.no_reclone

    if not read_fal_key():
        print("Missing FAL_KEY", file=sys.stderr)
        return 1
    os.environ["FAL_KEY"] = read_fal_key() or ""

    if not VOCALS_SRC.is_file():
        print(f"Missing {VOCALS_SRC} — run isolate_vocals_fal.py first", file=sys.stderr)
        return 1

    if not args.skip_ref_prep:
        print("Preparing 12s ref from 1min vocals...", flush=True)
        subprocess.run(
            [
                sys.executable,
                "prepare_frieren_qwen_ref.py",
                "--source",
                str(VOCALS_SRC),
                "--skip-demucs",
                "--skip",
                "0",
                "--target-seconds",
                "12",
                "--out-wav",
                str(REF_WAV),
                "--out-txt",
                str(REF_TXT),
                "--out-meta",
                str(REF_META),
            ],
            check=True,
            cwd=Path(__file__).parent,
        )

    if not REF_WAV.is_file() or not REF_TXT.is_file():
        print(f"Missing ref files under voice_refs/", file=sys.stderr)
        return 1

    ref_text = REF_TXT.read_text(encoding="utf-8-sig").strip()
    ref_seconds = 12.0
    if REF_META.is_file():
        ref_seconds = float(json.loads(REF_META.read_text(encoding="utf-8")).get("duration_sec", 12.0))

    emb_url, emb_meta = resolve_character_embedding(
        "Frieren",
        ref_wav=REF_WAV,
        ref_seconds=ref_seconds,
        ref_skip=0.0,
        force_reclone=reclone,
        reference_text=ref_text,
    )

    video = args.video.resolve() if args.video else latest_shot_video("S008")
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    stem = OUT_DIR / f"s008_frieren_v7_{ts}.mp3"
    audio = synthesize(
        FRIEREN_LINE_TEXT,
        emb_url,
        stem,
        prompt=FRIEREN_S008_PROMPT,
        reference_text=ref_text,
    )
    mux_out = OUT_DIR / f"S008_frieren_qwen_v7_{ts}.mp4"
    mux_dialogue(video, [(audio, FRIEREN_DIALOGUE_START_SEC)], mux_out, args.duck)

    final = ROOT / "outputs" / "video" / "final" / f"{video.stem}_frieren_dialogue_v7_{ts}.mp4"
    import shutil

    shutil.copy2(mux_out, final)

    report = {
        "variant": "v7",
        "source_vocals": str(VOCALS_SRC.relative_to(ROOT)),
        "ref_wav": str(REF_WAV.relative_to(ROOT)),
        "reference_text": ref_text,
        "compare_v4": "outputs/voice/S008/iterations/S008_frieren_qwen_v4_20260602T035231Z.mp4",
        "line": FRIEREN_LINE_TEXT,
        "prompt": FRIEREN_S008_PROMPT,
        "start_sec": FRIEREN_DIALOGUE_START_SEC,
        "qwen_embedding": emb_meta,
        "video_iterations": str(mux_out.relative_to(ROOT)),
        "video_final": str(final.relative_to(ROOT)),
    }
    report_path = OUT_DIR / f"v7_report_{ts}.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"\nv7: {mux_out}", flush=True)
    print(f"Final: {final}", flush=True)
    print(f"Compare v4: outputs/voice/S008/iterations/S008_frieren_qwen_v4_20260602T035231Z.mp4", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
