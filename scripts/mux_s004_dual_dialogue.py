"""
S004 — mux Fern then Frieren onto Kling I2V (panel order, no lip-sync).

Uses FERN_S004_DIALOGUE_START_SEC + dynamic Frieren start after Fern clip + pause.

Usage:
  cd scripts
  python mux_s004_dual_dialogue.py --video ..\\outputs\\video\\S004_kling....mp4 `
    --fern-wav ..\\outputs\\voice\\final\\S004\\s004_fern_fern_dialogue_v2_ja_....wav `
    --frieren-wav ..\\outputs\\voice\\final\\S004\\s004_frieren_frieren_dialogue_v2_ja_....wav
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from dialogue_mux import mux_dialogue, probe_duration
from fal_common import ROOT
from qwen_tts import (
    FERN_S004_DIALOGUE_START_SEC,
    FERN_S004_PAUSE_BEFORE_FRIEREN_SEC,
    FERN_S004_PHRASES,
    FRIEREN_S004_PHRASES,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="S004 dual-speaker mux (Fern → Frieren)")
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--fern-wav", type=Path, required=True)
    parser.add_argument("--frieren-wav", type=Path, required=True)
    parser.add_argument("--fern-start", type=float, default=FERN_S004_DIALOGUE_START_SEC)
    parser.add_argument("--pause-sec", type=float, default=FERN_S004_PAUSE_BEFORE_FRIEREN_SEC)
    parser.add_argument("--duck", type=float, default=0.35)
    parser.add_argument("--tag", type=str, default="s004_dual_mux")
    args = parser.parse_args()

    video = args.video.resolve()
    fern = args.fern_wav.resolve()
    frieren = args.frieren_wav.resolve()
    for p in (video, fern, frieren):
        if not p.is_file():
            print(f"Not found: {p}")
            return 1

    fern_dur = probe_duration(fern)
    frieren_start = args.fern_start + fern_dur + args.pause_sec
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = video.parent / f"{video.stem}_{args.tag}_{ts}.mp4"

    mux_dialogue(
        video,
        [(fern, args.fern_start), (frieren, frieren_start)],
        out,
        args.duck,
    )

    meta = {
        "video_in": str(video),
        "output": str(out),
        "sequence": [
            {"speaker": "Fern", "text": FERN_S004_PHRASES[0], "start_sec": args.fern_start},
            {
                "speaker": "Frieren",
                "text": FRIEREN_S004_PHRASES[0],
                "start_sec": round(frieren_start, 3),
            },
        ],
        "pause_sec": args.pause_sec,
        "duck": args.duck,
        "ts": ts,
    }
    meta_path = out.with_suffix(".json")
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"Fern @ {args.fern_start:.2f}s", flush=True)
    print(f"Frieren @ {frieren_start:.2f}s", flush=True)
    print(f"Saved: {out}", flush=True)
    print(f"Meta: {meta_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
