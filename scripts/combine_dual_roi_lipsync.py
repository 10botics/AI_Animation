"""
Merge two lip-sync passes onto one base frame, then optional dual dialogue mux.

Each pass must be from the same base video (same dimensions). Uses per-speaker face
regions from ROI or mask meta JSON (`lipsync_crop` / `lipsync_full` + `roi_pixels`).

Usage:
  cd scripts
  python combine_dual_roi_lipsync.py `
    --base "..\\outputs\\video\\final\\Voice Added\\S004_kling....mp4" `
    --meta "..\\outputs\\video\\LipsyncTests\\..._frieren_..._roi_....json" `
    --meta "..\\outputs\\video\\LipsyncTests\\..._fern_..._roi_....json" `
    --tag s004_dual_roi_combined
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from dialogue_mux import mux_dialogue, probe_duration
from fal_common import ROOT
from lipsync_meta import write_lipsync_meta


def _load_roi_meta(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    roi = data["roi_pixels"]
    lipsync = data.get("lipsync_crop") or data.get("lipsync_full")
    if not lipsync:
        raise KeyError(f"No lipsync_crop/lipsync_full in {path}")
    return {
        "lipsync_crop": Path(lipsync),
        "x": int(roi["x"]),
        "y": int(roi["y"]),
        "w": int(roi["w"]),
        "h": int(roi["h"]),
        "tag": path.stem,
        "pipeline": data.get("pipeline", "unknown"),
    }


def _overlay_chain(base: Path, layers: list[dict], dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    inputs = ["-i", str(base)]
    for layer in layers:
        inputs.extend(["-i", str(layer["lipsync_crop"])])
    parts: list[str] = []
    prev = "[0:v]"
    for i, layer in enumerate(layers):
        x, y, w, h = layer["x"], layer["y"], layer["w"], layer["h"]
        roi = f"[r{i}]"
        out = f"[v{i}]" if i < len(layers) - 1 else "[vout]"
        parts.append(f"[{i + 1}:v]scale={w}:{h}:flags=lanczos{roi}")
        parts.append(f"{prev}{roi}overlay={x}:{y}:format=auto{out}")
        prev = out
    parts.append("[vout]format=yuv420p[vfinal]")
    filt = ";".join(parts)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            *inputs,
            "-filter_complex",
            filt,
            "-map",
            "[vfinal]",
            "-map",
            "0:a?",
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-preset",
            "medium",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            str(dest),
        ],
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Combine two ROI lip-sync overlays")
    parser.add_argument("--base", type=Path, required=True, help="Silent / Kling I2V base")
    parser.add_argument(
        "--meta",
        type=Path,
        action="append",
        required=True,
        help="ROI meta JSON (repeat per pass; order = overlay stack)",
    )
    parser.add_argument("--out-dir", type=Path, default=ROOT / "outputs" / "video" / "LipsyncTests")
    parser.add_argument("--tag", type=str, default="dual_roi_combined")
    parser.add_argument("--fern-wav", type=Path, default=None)
    parser.add_argument("--frieren-wav", type=Path, default=None)
    parser.add_argument("--fern-start", type=float, default=0.4)
    parser.add_argument("--pause-sec", type=float, default=0.6)
    parser.add_argument("--duck", type=float, default=0.35)
    args = parser.parse_args()

    base = args.base.resolve()
    if not base.is_file():
        print(f"Not found: {base}")
        return 1

    layers = [_load_roi_meta(p.resolve()) for p in args.meta]
    for layer in layers:
        if not layer["lipsync_crop"].is_file():
            print(f"Missing lipsync crop: {layer['lipsync_crop']}")
            return 1

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = args.out_dir.resolve()
    visual = out_dir / f"{base.stem}_{args.tag}_{ts}.mp4"
    print(f"Combining {len(layers)} ROI layers on {base.name}…", flush=True)
    _overlay_chain(base, layers, visual)

    meta = {
        "base": str(base),
        "layers": [
            {**layer, "lipsync_crop": str(layer["lipsync_crop"])} for layer in layers
        ],
        "visual_output": str(visual),
        "ts": ts,
    }

    final = visual
    if args.fern_wav and args.frieren_wav:
        fern = args.fern_wav.resolve()
        frieren = args.frieren_wav.resolve()
        fern_dur = probe_duration(fern)
        frieren_start = args.fern_start + fern_dur + args.pause_sec
        final = out_dir / f"{visual.stem}_dual_mux_{ts}.mp4"
        mux_dialogue(
            visual,
            [(fern, args.fern_start), (frieren, frieren_start)],
            final,
            args.duck,
        )
        meta["mux"] = {
            "fern_wav": str(fern),
            "frieren_wav": str(frieren),
            "fern_start_sec": args.fern_start,
            "frieren_start_sec": round(frieren_start, 3),
            "pause_sec": args.pause_sec,
        }
        meta["final_output"] = str(final)

    meta_path = write_lipsync_meta(final, meta)
    print(f"Saved: {final}", flush=True)
    print(f"Meta: {meta_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
