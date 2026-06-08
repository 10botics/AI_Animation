"""
Batch S008 Frieren Qwen3 iterations — ref length, prompt, and timing variants.

Usage:
  cd scripts
  python generate_s008_frieren_iterations.py
  python generate_s008_frieren_iterations.py --only v1 v3
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from fal_common import ROOT, read_fal_key
from dialogue_mux import latest_shot_video, mux_dialogue
from generate_s008_dialogue import FRIEREN_LINE_TEXT
from qwen_tts import clone_voice, extract_eng_dub_ref, synthesize

OUT_DIR = ROOT / "outputs" / "voice" / "S008" / "iterations"
from voice_paths import VOICE_REFS_WORK

VOICE_REFS = VOICE_REFS_WORK

VARIANTS = [
    {
        "id": "v1",
        "label": "130s ref, default prompt, 2.0s",
        "ref_seconds": 130.0,
        "ref_skip": 3.0,
        "start_sec": 2.0,
        "prompt": "Calm, understated, slightly interested.",
    },
    {
        "id": "v2",
        "label": "130s ref, dry witty, 2.0s",
        "ref_seconds": 130.0,
        "ref_skip": 3.0,
        "start_sec": 2.0,
        "prompt": "Quiet flat delivery. Female voice. Dry witty tone, soft and low.",
    },
    {
        "id": "v3",
        "label": "130s ref, matter-of-fact amused, 1.95s",
        "ref_seconds": 130.0,
        "ref_skip": 3.0,
        "start_sec": 1.95,
        "prompt": "Soft spoken, matter-of-fact, subtly amused. English anime dub.",
    },
    {
        "id": "v4",
        "label": "130s from start, elf mage, 2.05s (DEFAULT)",
        "ref_seconds": 130.0,
        "ref_skip": 0.0,
        "start_sec": 2.05,
        "prompt": "Calm ancient elf mage. Low energy, interested. English dub actress.",
    },
    {
        "id": "v5",
        "label": "90s ref skip 5, default prompt, 2.0s",
        "ref_seconds": 90.0,
        "ref_skip": 5.0,
        "start_sec": 2.0,
        "prompt": "Calm, understated, slightly interested.",
    },
]


def _ref_path(seconds: float, skip: float) -> Path:
    skip_tag = f"skip{int(skip)}" if skip else "skip0"
    return VOICE_REFS / f"frieren_eng_dub_ref_{int(seconds)}s_{skip_tag}.wav"


def run_variant(variant: dict, video: Path, batch_ts: str, duck: float) -> dict:
    vid = variant["id"]
    ref_path = _ref_path(variant["ref_seconds"], variant["ref_skip"])
    extract_eng_dub_ref(
        ref_path,
        seconds=variant["ref_seconds"],
        skip=variant["ref_skip"],
    )
    print(f"\n--- {vid}: {variant['label']} ---", flush=True)
    print(f"Ref: {ref_path.name}", flush=True)

    emb_url = clone_voice(ref_path)
    stem = OUT_DIR / f"s008_frieren_{vid}_{batch_ts}.mp3"
    audio = synthesize(
        FRIEREN_LINE_TEXT,
        emb_url,
        stem,
        prompt=variant["prompt"],
    )
    mux_out = OUT_DIR / f"S008_frieren_qwen_{vid}_{batch_ts}.mp4"
    mux_dialogue(video, [(audio, variant["start_sec"])], mux_out, duck)

    return {
        "id": vid,
        "label": variant["label"],
        "ref_wav": str(ref_path.relative_to(ROOT)),
        "ref_seconds": variant["ref_seconds"],
        "ref_skip": variant["ref_skip"],
        "start_sec": variant["start_sec"],
        "prompt": variant["prompt"],
        "audio": str(audio.relative_to(ROOT)),
        "video": str(mux_out.relative_to(ROOT)),
        "embedding_url": emb_url,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="S008 Frieren Qwen3 iteration batch")
    parser.add_argument("--only", nargs="+", metavar="ID", help="Subset e.g. v1 v3")
    parser.add_argument("--duck", type=float, default=0.35)
    parser.add_argument("--video", type=Path, default=None)
    args = parser.parse_args()

    if not read_fal_key():
        print("Missing FAL_KEY", file=sys.stderr)
        return 1
    os.environ["FAL_KEY"] = read_fal_key() or ""

    variants = VARIANTS
    if args.only:
        wanted = set(args.only)
        variants = [v for v in VARIANTS if v["id"] in wanted]
        if not variants:
            print(f"No matching variants: {args.only}", file=sys.stderr)
            return 1

    video = args.video.resolve() if args.video else latest_shot_video("S008")
    batch_ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []
    for variant in variants:
        try:
            results.append(run_variant(variant, video, batch_ts, args.duck))
        except Exception as e:
            results.append({"id": variant["id"], "status": "error", "error": str(e)})
            print(f"ERROR {variant['id']}: {e}", file=sys.stderr)

    report = {
        "batch_ts": batch_ts,
        "engine": "qwen3-tts-1.7b",
        "line": FRIEREN_LINE_TEXT,
        "video_in": str(video),
        "variants": results,
    }
    report_path = OUT_DIR / f"iterations_report_{batch_ts}.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nReport: {report_path}", flush=True)
    print("\nOutputs:", flush=True)
    for r in results:
        if r.get("video"):
            print(f"  {r['id']}: {r['video']}", flush=True)
    return 0 if all("video" in r for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
