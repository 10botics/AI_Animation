"""
S008 Frieren v6 — curated 12s ref + reference_text + Demucs (Tier 1 Qwen improvements).

Compare against v4:
  outputs/voice/S008/iterations/S008_frieren_qwen_v4_20260602T035231Z.mp4

Usage:
  cd scripts
  python prepare_frieren_qwen_ref.py
  python generate_s008_frieren_v6.py
  python generate_s008_frieren_v6.py --skip-ref-prep --reclone
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
from qwen_tts import (
    DEFAULT_PROMPT,
    FRIEREN_DIALOGUE_START_SEC,
    FRIEREN_QWEN_REF_TXT,
    FRIEREN_QWEN_REF_WAV,
    load_reference_text,
    resolve_character_embedding,
    synthesize,
)

OUT_DIR = ROOT / "outputs" / "voice" / "S008" / "iterations"


def main() -> int:
    parser = argparse.ArgumentParser(description="S008 Frieren Qwen v6 (ICL-style Fal)")
    parser.add_argument("--skip-ref-prep", action="store_true")
    parser.add_argument("--reclone", action="store_true")
    parser.add_argument("--duck", type=float, default=0.35)
    parser.add_argument("--video", type=Path, default=None)
    args = parser.parse_args()

    if not read_fal_key():
        print("Missing FAL_KEY", file=sys.stderr)
        return 1
    os.environ["FAL_KEY"] = read_fal_key() or ""

    if not args.skip_ref_prep:
        print("Preparing curated ref...", flush=True)
        subprocess.run([sys.executable, "prepare_frieren_qwen_ref.py"], check=True, cwd=Path(__file__).parent)

    if not FRIEREN_QWEN_REF_WAV.is_file():
        print(f"Missing ref wav: {FRIEREN_QWEN_REF_WAV}", file=sys.stderr)
        return 1

    ref_text = load_reference_text()
    meta_path = ROOT / "voice_refs" / "frieren_qwen_ref_15s.json"
    ref_seconds = 12.0
    ref_skip = 0.0
    if meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        ref_seconds = float(meta.get("duration_sec", ref_seconds))

    emb_url, emb_meta = resolve_character_embedding(
        "Frieren",
        ref_wav=FRIEREN_QWEN_REF_WAV,
        ref_seconds=ref_seconds,
        ref_skip=ref_skip,
        force_reclone=args.reclone,
        reference_text=ref_text,
    )

    video = args.video.resolve() if args.video else latest_shot_video("S008")
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    stem = OUT_DIR / f"s008_frieren_v6_{ts}.mp3"
    audio = synthesize(
        FRIEREN_LINE_TEXT,
        emb_url,
        stem,
        prompt=DEFAULT_PROMPT,
        reference_text=ref_text,
    )
    mux_out = OUT_DIR / f"S008_frieren_qwen_v6_{ts}.mp4"
    mux_dialogue(video, [(audio, FRIEREN_DIALOGUE_START_SEC)], mux_out, args.duck)

    final = ROOT / "outputs" / "video" / "final" / f"{video.stem}_frieren_dialogue_v6_{ts}.mp4"
    import shutil

    shutil.copy2(mux_out, final)

    report = {
        "variant": "v6",
        "improvements": ["curated_10-15s_ref", "reference_text", "demucs_vocals", "fal_whisper_transcript"],
        "compare_v4": "outputs/voice/S008/iterations/S008_frieren_qwen_v4_20260602T035231Z.mp4",
        "line": FRIEREN_LINE_TEXT,
        "prompt": DEFAULT_PROMPT,
        "start_sec": FRIEREN_DIALOGUE_START_SEC,
        "ref_wav": str(FRIEREN_QWEN_REF_WAV.relative_to(ROOT)),
        "reference_text": ref_text,
        "qwen_embedding": emb_meta,
        "audio": str(audio.relative_to(ROOT)),
        "video_iterations": str(mux_out.relative_to(ROOT)),
        "video_final": str(final.relative_to(ROOT)),
    }
    report_path = OUT_DIR / f"v6_report_{ts}.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"\n v6: {mux_out}", flush=True)
    print(f"Final: {final}", flush=True)
    print(f"Report: {report_path}", flush=True)
    print(f"\nCompare with v4: outputs/voice/S008/iterations/S008_frieren_qwen_v4_20260602T035231Z.mp4", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
