"""
S004 — combine Fern + Frieren JP stems in panel read order for lip-sync / mux.

Order (panel_s004jap.png):
  1. Fern  フリーレン様。  @ FERN_S004_DIALOGUE_START_SEC
  2. pause FERN_S004_PAUSE_BEFORE_FRIEREN_SEC
  3. Frieren  また大陸魔法協会からの依頼？  (dynamic start after Fern ends)

Usage:
  cd scripts
  python build_s004_combined_dialogue.py `
    --fern-wav "..\outputs\voice\final\S004\s004_fern_fern_dialogue_v2_ja_20260604T072740Z.wav" `
    --frieren-wav "..\outputs\voice\final\S004\s004_frieren_frieren_dialogue_v1_ja_20260603T070054Z.wav"
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from dialogue_mux import mix_dialogue_stems, probe_duration
from fal_common import ROOT
from qwen_tts import (
    FERN_S004_DIALOGUE_START_SEC,
    FERN_S004_PAUSE_BEFORE_FRIEREN_SEC,
    FRIEREN_S004_PHRASES,
    FERN_S004_PHRASES,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="S004 Fern→Frieren timeline WAV")
    parser.add_argument("--fern-wav", type=Path, required=True)
    parser.add_argument("--frieren-wav", type=Path, required=True)
    parser.add_argument("--fern-start", type=float, default=FERN_S004_DIALOGUE_START_SEC)
    parser.add_argument("--pause-sec", type=float, default=FERN_S004_PAUSE_BEFORE_FRIEREN_SEC)
    parser.add_argument("--video", type=Path, default=None, help="Optional: pad timeline to video length")
    parser.add_argument("--tag", type=str, default="s004_fern_frieren_ja")
    args = parser.parse_args()

    fern = args.fern_wav.resolve()
    frieren = args.frieren_wav.resolve()
    if not fern.is_file():
        print(f"Not found: {fern}")
        return 1
    if not frieren.is_file():
        print(f"Not found: {frieren}")
        return 1

    fern_dur = probe_duration(fern)
    frieren_start = args.fern_start + fern_dur + args.pause_sec
    frieren_dur = probe_duration(frieren)
    total = frieren_start + frieren_dur + 0.3
    if args.video:
        v = args.video.resolve()
        if v.is_file():
            total = max(total, probe_duration(v))

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "outputs" / "voice" / "S004"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_wav = out_dir / f"s004_combined_{args.tag}_{ts}.wav"
    final_dir = ROOT / "outputs" / "voice" / "final" / "S004"
    final_dir.mkdir(parents=True, exist_ok=True)

    mix_dialogue_stems(
        [(fern, args.fern_start), (frieren, frieren_start)],
        out_wav,
        total_dur=total,
    )
    final_wav = final_dir / out_wav.name
    final_wav.write_bytes(out_wav.read_bytes())

    meta = {
        "sequence": [
            {"speaker": "Fern", "text": FERN_S004_PHRASES[0], "start_sec": args.fern_start, "duration_sec": fern_dur},
            {
                "speaker": "Frieren",
                "text": FRIEREN_S004_PHRASES[0],
                "start_sec": round(frieren_start, 3),
                "duration_sec": frieren_dur,
            },
        ],
        "pause_between_sec": args.pause_sec,
        "panel_ref": "panels/jap/panel_s004jap.png",
        "combined_wav": str(out_wav.relative_to(ROOT)),
        "combined_final": str(final_wav.relative_to(ROOT)),
        "lipsync_start_sec": 0.0,
        "ts": ts,
    }
    meta_path = out_dir / f"s004_combined_{args.tag}_meta_{ts}.json"
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    print(f"Fern @ {args.fern_start:.2f}s ({fern_dur:.2f}s)", flush=True)
    print(f"Pause {args.pause_sec:.2f}s", flush=True)
    print(f"Frieren @ {frieren_start:.2f}s ({frieren_dur:.2f}s)", flush=True)
    print(f"Combined: {final_wav}", flush=True)
    print(f"Meta: {meta_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
