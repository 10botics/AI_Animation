"""
Black-box mask on non-speaking face(s) → full-frame PixVerse → combine via
combine_dual_roi_lipsync.py (paste each speaker's face region from the full pass).

Easier than crop-ROI: tune one rectangle per face to hide, run lipsync on full frame.

Usage (S004 dual):
  cd scripts
  python lipsync_fal_mask.py --shot S004 --speaker fern --video ..\\outputs\\video\\S004_kling....mp4 `
    --audio ..\\outputs\\voice\\final\\S004\\s004_fern_....wav --start-sec 1.0 --tag fern_v2_mask
  python lipsync_fal_mask.py --shot S004 --speaker frieren --video ... --audio ... --start-sec 3.1 --tag frieren_v2_mask
  python combine_dual_roi_lipsync.py --base ... --meta ...fern....json --meta ...frieren....json ...
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
from lipsync_fal_roi import SHOT_ROI_REL, _probe_size, _rel_to_pixels
from lipsync_meta import write_lipsync_meta

# Per shot: face region to paste on combine (speaker being synced).
SHOT_SPEAKER_OVERLAY: dict[str, dict[str, str]] = {
    "S004": {"fern": "S004_FERN", "frieren": "S004"},
}

# Per shot: which ROI(s) to black out when syncing the named speaker.
SHOT_MASK_WHEN_SPEAKER: dict[str, dict[str, tuple[str, ...]]] = {
    "S004": {
        "fern": ("S004",),
        "frieren": ("S004_FERN",),
    },
}


def _apply_black_masks(
    src: Path,
    dest: Path,
    boxes: list[tuple[int, int, int, int]],
) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not boxes:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(src), "-c:v", "libx264", "-crf", "18", "-preset", "fast", "-an", str(dest)],
            check=True,
            capture_output=True,
        )
        return dest
    draws = [
        f"drawbox=x={x}:y={y}:w={w}:h={h}:color=black@1:t=fill"
        for x, y, w, h in boxes
    ]
    vf = f"{','.join(draws)},format=yuv420p"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-vf",
            vf,
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-preset",
            "fast",
            "-an",
            str(dest),
        ],
        check=True,
        capture_output=True,
    )
    return dest


def _run_lipsync_full(
    model_key: str,
    video: Path,
    padded_audio: Path,
    *,
    sync_mode: str,
) -> Path:
    model_id = MODELS[model_key]
    assert_model_allowed(model_id)
    work = video.parent / f"{video.stem}_upload.mp4"
    _ensure_video_specs(video, work)
    print(f"Uploading masked video ({video.name})…", flush=True)
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
    out = video.parent / f"{video.stem}_{model_key}_raw.mp4"
    download_file(_video_url_from_lipsync_result(result), out)
    return out


def _resolve_speaker_masks(shot: str, speaker: str) -> tuple[str, tuple[str, ...]]:
    key = shot.upper()
    sp = speaker.lower()
    if key not in SHOT_MASK_WHEN_SPEAKER:
        raise KeyError(f"No mask map for shot {key}")
    if sp not in SHOT_MASK_WHEN_SPEAKER[key]:
        raise KeyError(f"Unknown speaker {sp} for {key}; use: {list(SHOT_MASK_WHEN_SPEAKER[key])}")
    overlay_key = SHOT_SPEAKER_OVERLAY.get(key, {}).get(sp, key)
    return overlay_key, SHOT_MASK_WHEN_SPEAKER[key][sp]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Black-mask other face(s) → full-frame Fal lipsync (PixVerse default)"
    )
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--start-sec", type=float, required=True)
    parser.add_argument("--tag", type=str, default="lipsync_mask")
    parser.add_argument("--shot", type=str, required=True, help="e.g. S004")
    parser.add_argument(
        "--speaker",
        type=str,
        required=True,
        help="Speaker being synced (fern | frieren) — other face(s) get black box",
    )
    parser.add_argument(
        "--mask-rel",
        type=str,
        action="append",
        default=None,
        help="Extra mask x,y,w,h fractions (repeatable); overrides shot map if set",
    )
    parser.add_argument("--overlay-shot", type=str, default=None, help="ROI to paste on combine (default: speaker face)")
    parser.add_argument("--model", choices=tuple(MODELS.keys()), default=DEFAULT_LIPSYNC_MODEL)
    parser.add_argument("--sync-mode", default="cut_off")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "outputs" / "video" / "LipsyncTests")
    parser.add_argument("--keep-work", action="store_true")
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

    shot = args.shot.upper()
    vw, vh = _probe_size(video_in)
    video_dur = probe_duration(video_in)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    try:
        overlay_key, mask_keys = _resolve_speaker_masks(shot, args.speaker)
    except KeyError as e:
        print(e, file=sys.stderr)
        return 1

    if args.overlay_shot:
        overlay_key = args.overlay_shot.upper()
    if overlay_key not in SHOT_ROI_REL:
        print(f"Unknown overlay shot {overlay_key}", file=sys.stderr)
        return 1

    mask_boxes: list[tuple[int, int, int, int]] = []
    if args.mask_rel:
        for spec in args.mask_rel:
            parts = [float(p.strip()) for p in spec.split(",")]
            if len(parts) != 4:
                print("--mask-rel needs x,y,w,h", file=sys.stderr)
                return 1
            mask_boxes.append(_rel_to_pixels(tuple(parts), vw, vh))  # type: ignore
    else:
        for mk in mask_keys:
            if mk not in SHOT_ROI_REL:
                print(f"Unknown mask region {mk}", file=sys.stderr)
                return 1
            mask_boxes.append(_rel_to_pixels(SHOT_ROI_REL[mk], vw, vh))

    overlay_rel = SHOT_ROI_REL[overlay_key]
    ox, oy, ow, oh = _rel_to_pixels(overlay_rel, vw, vh)

    work_root = ROOT / "outputs" / "voice" / "mask_work" / shot
    if args.keep_work:
        work_root.mkdir(parents=True, exist_ok=True)
        work_dir = work_root / f"{args.speaker}_{ts}"
        work_dir.mkdir(parents=True, exist_ok=True)
    else:
        work_dir = Path(tempfile.mkdtemp(prefix="lipsync_mask_"))

    try:
        masked_path = work_dir / f"{video_in.stem}_masked.mp4"
        print(f"Black mask {len(mask_boxes)} box(es) on {video_in.name}", flush=True)
        for i, b in enumerate(mask_boxes):
            print(f"  mask[{i}] {b[2]}x{b[3]} at ({b[0]},{b[1]})", flush=True)
        _apply_black_masks(video_in, masked_path, mask_boxes)

        padded = work_dir / "audio_padded.mp3"
        _pad_audio_for_video(dialogue, video_dur, args.start_sec, padded)

        print(f"\n=== mask {args.model} ({args.speaker}) ===", flush=True)
        lipsync_raw = _run_lipsync_full(
            args.model,
            masked_path,
            padded,
            sync_mode=args.sync_mode,
        )

        out_dir = args.out_dir.resolve()
        stem = video_in.stem
        final = out_dir / f"{stem}_{args.tag}_{args.model}_mask_{ts}.mp4"
        # Full-frame result for QC; combine step uses lipsync_raw + overlay ROI.
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(lipsync_raw), "-c", "copy", str(final)],
            check=True,
            capture_output=True,
        )

        meta_path = write_lipsync_meta(
            final,
            {
                "pipeline": "mask_lipsync",
                "model": MODELS[args.model],
                "video_in": str(video_in),
                "audio_in": str(dialogue),
                "start_sec": args.start_sec,
                "speaker": args.speaker,
                "shot": shot,
                "mask_boxes": [
                    {"x": b[0], "y": b[1], "w": b[2], "h": b[3]} for b in mask_boxes
                ],
                "masked_video": str(masked_path),
                "lipsync_full": str(lipsync_raw),
                "lipsync_crop": str(lipsync_raw),
                "roi_pixels": {"x": ox, "y": oy, "w": ow, "h": oh},
                "roi_rel": overlay_rel,
                "output": str(final),
            },
        )
        print(f"Saved: {final}", flush=True)
        print(f"Meta: {meta_path}", flush=True)
        print("Combine: combine_dual_roi_lipsync.py --base <same video> --meta <this json> ...", flush=True)
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
