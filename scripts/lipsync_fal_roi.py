"""
ROI lip-sync: crop face region → Fal lipsync → overlay back on full frame.

PixVerse lipsync has no face picker; cropping steers the model toward one speaker.

Usage:
  cd scripts
  python lipsync_fal_roi.py --video ..\\outputs\\video\\final\\S005_....mp4 `
    --audio ..\\outputs\\voice\\final\\S005\\s005_fern_....wav `
    --start-sec 1.85 --tag fern_dialogue_v2_ja_roi --shot S005
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import fal_client

from dialogue_mux import probe_duration
from fal_common import ROOT, assert_model_allowed, download_file, read_fal_key
from lipsync_fal import (
    DEFAULT_LIPSYNC_MODEL,
    MODELS,
    _build_api_args,
    _ensure_video_specs,
    _pad_audio_for_video,
    _video_url_from_lipsync_result,
)
from lipsync_meta import write_lipsync_meta

# S005 CU: Fern foreground (profile / letter read); Lernen memory BG left — crop right-center.
SHOT_ROI_REL: dict[str, tuple[float, float, float, float]] = {
    "S005": (0.38, 0.10, 0.58, 0.82),
    # S004 Frieren foreground profile (left)
    "S004": (0.02, 0.12, 0.52, 0.78),
    # S004 Fern deeper background, envelope / upper body
    "S004_FERN": (0.40, 0.18, 0.42, 0.58),
    "S008": (0.55, 0.08, 0.42, 0.75),
}


def _probe_size(video: Path) -> tuple[int, int]:
    r = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "csv=p=0",
            str(video),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    w, h = r.stdout.strip().split(",")
    return int(w), int(h)


def _rel_to_pixels(
    rel: tuple[float, float, float, float],
    width: int,
    height: int,
) -> tuple[int, int, int, int]:
    x_r, y_r, w_r, h_r = rel
    cw = max(64, int(w_r * width))
    ch = max(64, int(h_r * height))
    x = max(0, min(int(x_r * width), width - cw))
    y = max(0, min(int(y_r * height), height - ch))
    return x, y, cw, ch


def _crop_video(src: Path, dest: Path, x: int, y: int, cw: int, ch: int) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-vf",
            f"crop={cw}:{ch}:{x}:{y}",
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-preset",
            "fast",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(dest),
        ],
        check=True,
        capture_output=True,
    )
    return dest


def _overlay_roi(
    full: Path,
    lipsync_roi: Path,
    dest: Path,
    *,
    x: int,
    y: int,
    cw: int,
    ch: int,
) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    filt = (
        f"[1:v]scale={cw}:{ch}:flags=lanczos[roi];"
        f"[0:v][roi]overlay={x}:{y}:format=auto,format=yuv420p[v]"
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(full),
            "-i",
            str(lipsync_roi),
            "-filter_complex",
            filt,
            "-map",
            "[v]",
            "-map",
            "1:a?",
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
        capture_output=True,
    )
    return dest


def _run_lipsync_crop(
    model_key: str,
    crop_video: Path,
    padded_audio: Path,
    *,
    sync_mode: str,
) -> Path:
    model_id = MODELS[model_key]
    assert_model_allowed(model_id)
    work = crop_video.parent / f"{crop_video.stem}_upload.mp4"
    _ensure_video_specs(crop_video, work)
    print(f"Uploading ROI video ({crop_video.name})…", flush=True)
    video_url = fal_client.upload_file(str(work))
    audio_url = fal_client.upload_file(str(padded_audio))
    print(f"Submitting {model_id} …", flush=True)
    result = fal_client.subscribe(
        model_id,
        arguments=_build_api_args(
            model_key, video_url=video_url, audio_url=audio_url, sync_mode=sync_mode
        ),
        with_logs=True,
    )
    if not isinstance(result, dict):
        raise RuntimeError(f"Lipsync failed: {result}")
    out = crop_video.parent / f"{crop_video.stem}_{model_key}_raw.mp4"
    download_file(_video_url_from_lipsync_result(result), out)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="ROI crop → Fal lipsync → overlay")
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--start-sec", type=float, required=True)
    parser.add_argument("--tag", type=str, default="lipsync_roi")
    parser.add_argument("--shot", type=str, default=None, help="Use SHOT_ROI_REL preset (e.g. S005)")
    parser.add_argument(
        "--crop-rel",
        type=str,
        default=None,
        help="x,y,w,h fractions 0–1 (overrides --shot)",
    )
    parser.add_argument("--model", choices=tuple(MODELS.keys()), default=DEFAULT_LIPSYNC_MODEL)
    parser.add_argument("--sync-mode", default="cut_off")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "outputs" / "video" / "LipsyncTests",
    )
    parser.add_argument(
        "--keep-work",
        action="store_true",
        help="Save crop + raw lipsync under outputs/voice/roi_work/",
    )
    args = parser.parse_args()

    if not read_fal_key():
        print("Missing FAL_KEY in .env", file=sys.stderr)
        return 1
    os.environ["FAL_KEY"] = read_fal_key() or ""

    video_in = args.video.resolve()
    dialogue = args.audio.resolve()
    if not video_in.is_file() or not dialogue.is_file():
        print("Video or audio not found", file=sys.stderr)
        return 1

    if args.crop_rel:
        parts = [float(p.strip()) for p in args.crop_rel.split(",")]
        if len(parts) != 4:
            print("--crop-rel needs x,y,w,h", file=sys.stderr)
            return 1
        rel = tuple(parts)  # type: ignore
    elif args.shot:
        key = args.shot.upper()
        if key not in SHOT_ROI_REL:
            print(f"Unknown shot {key}; known: {list(SHOT_ROI_REL)}", file=sys.stderr)
            return 1
        rel = SHOT_ROI_REL[key]
    else:
        print("Pass --shot S005 or --crop-rel x,y,w,h", file=sys.stderr)
        return 1

    vw, vh = _probe_size(video_in)
    x, y, cw, ch = _rel_to_pixels(rel, vw, vh)
    video_dur = probe_duration(video_in)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = args.out_dir.resolve()

    work_root = ROOT / "outputs" / "voice" / "roi_work" / (args.shot or "custom").upper()
    if args.keep_work:
        work_root.mkdir(parents=True, exist_ok=True)
        work_dir = work_root / ts
        work_dir.mkdir(parents=True, exist_ok=True)
    else:
        work_dir = Path(tempfile.mkdtemp(prefix="lipsync_roi_"))

    try:
        crop_path = work_dir / f"{video_in.stem}_crop.mp4"
        print(f"ROI crop {cw}x{ch} at ({x},{y}) from {vw}x{vh}", flush=True)
        _crop_video(video_in, crop_path, x, y, cw, ch)

        padded = work_dir / "audio_padded.mp3"
        _pad_audio_for_video(dialogue, video_dur, args.start_sec, padded)

        print(f"\n=== ROI {args.model} ===", flush=True)
        lipsync_raw = _run_lipsync_crop(
            args.model,
            crop_path,
            padded,
            sync_mode=args.sync_mode,
        )

        stem = video_in.stem
        final = out_dir / f"{stem}_{args.tag}_{args.model}_roi_{ts}.mp4"
        print(f"Overlay ROI on full frame…", flush=True)
        _overlay_roi(video_in, lipsync_raw, final, x=x, y=y, cw=cw, ch=ch)

        meta_path = write_lipsync_meta(
            final,
            {
                "pipeline": "crop_lipsync_overlay",
                "model": MODELS[args.model],
                "video_in": str(video_in),
                "audio_in": str(dialogue),
                "start_sec": args.start_sec,
                "roi_pixels": {"x": x, "y": y, "w": cw, "h": ch},
                "roi_rel": rel,
                "full_size": {"w": vw, "h": vh},
                "crop_video": str(crop_path),
                "lipsync_crop": str(lipsync_raw),
                "output": str(final),
            },
        )
        print(f"Saved: {final}", flush=True)
        print(f"Meta: {meta_path}", flush=True)
    finally:
        if not args.keep_work and work_dir.exists():
            for f in work_dir.iterdir():
                try:
                    f.unlink()
                except OSError:
                    pass
            try:
                work_dir.rmdir()
            except OSError:
                pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
