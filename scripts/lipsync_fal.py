"""
Fal lip-sync: drive mouth motion from dialogue audio on an I2V clip.

**Production default:** pixverse — fal-ai/pixverse/lipsync (see docs/pixverse-lipsync-log.md).

Inputs:
  - **video:** silent base I2V (no muxed dialogue track)
  - **audio:** clean Qwen stem, padded to match --start-sec
  - **out-dir:** outputs/video/LipsyncTests (default)

Other models (A/B fallback only):
  musetalk, sync-pro, sync-v3, sync, kling, latentsync, heygen-precision, heygen-speed

Usage:
  cd scripts
  python lipsync_fal.py --video ... --audio ... --start-sec 2.05 --tag frieren_dialogue_v14_ja
  python lipsync_fal.py --model musetalk --video ... --audio ...   # fallback
  python lipsync_fal.py --all-models --video ... --audio ...       # pixverse + musetalk + sync-pro
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
from lipsync_meta import write_lipsync_meta

MODELS = {
    "musetalk": "fal-ai/musetalk",
    "latentsync": "fal-ai/latentsync",
    "sync-pro": "fal-ai/sync-lipsync/v2/pro",
    "sync-v3": "fal-ai/sync-lipsync/v3",
    "sync": "fal-ai/sync-lipsync",
    "kling": "fal-ai/kling-video/lipsync/audio-to-video",
    "pixverse": "fal-ai/pixverse/lipsync",
    "heygen-precision": "fal-ai/heygen/v3/lipsync/precision",
    "heygen-speed": "fal-ai/heygen/v3/lipsync/speed",
}

# Production default; --all-models runs this tuple for A/B.
RECOMMENDED_FOR_ANIME = ("pixverse", "musetalk", "sync-pro")
DEFAULT_LIPSYNC_MODEL = "pixverse"


def _pad_audio_for_video(
    dialogue: Path,
    video_dur: float,
    start_sec: float,
    out: Path,
) -> Path:
    """Prepend silence so dialogue aligns with mux timing (lipsync APIs start at t=0)."""
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"anullsrc=r=44100:cl=mono,atrim=duration={start_sec:.3f}",
            "-i",
            str(dialogue),
            "-filter_complex",
            f"[0:a][1:a]concat=n=2:v=0:a=1,apad=whole_dur={video_dur:.3f}[out]",
            "-map",
            "[out]",
            "-c:a",
            "libmp3lame",
            "-q:a",
            "2",
            str(out),
        ],
        check=True,
        capture_output=True,
    )
    return out


def _ensure_video_specs(src: Path, dest: Path) -> Path:
    """Kling lipsync: 720–1920px width; scale down if needed."""
    r = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width",
            "-of",
            "csv=p=0",
            str(src),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    w = int(r.stdout.strip())
    if w <= 1920:
        if src.resolve() != dest.resolve():
            dest.write_bytes(src.read_bytes())
        return dest
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-vf",
            "scale=1920:-2",
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-preset",
            "fast",
            "-c:a",
            "copy",
            str(dest),
        ],
        check=True,
        capture_output=True,
    )
    return dest


def _extract_audio_from_video(video: Path, out: Path) -> Path:
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "44100", str(out)],
        check=True,
        capture_output=True,
    )
    return out


def _build_api_args(
    model_key: str,
    *,
    video_url: str,
    audio_url: str,
    sync_mode: str,
) -> dict:
    if model_key == "musetalk":
        return {"source_video_url": video_url, "audio_url": audio_url}
    args: dict = {"video_url": video_url, "audio_url": audio_url}
    if model_key.startswith("heygen"):
        args["enable_dynamic_duration"] = True
    if model_key == "pixverse":
        return {"video_url": video_url, "audio_url": audio_url}
    if model_key.startswith("sync"):
        args["sync_mode"] = sync_mode
    if model_key == "sync":
        args["model"] = "lipsync-1.9.0-beta"
    return args


def _run_one(
    model_key: str,
    *,
    work_video: Path,
    padded_audio: Path,
    video_in: Path,
    dialogue: Path,
    start_sec: float,
    video_dur: float,
    sync_mode: str,
    tag: str,
    out_dir: Path,
) -> Path:
    model_id = MODELS[model_key]
    assert_model_allowed(model_id)
    print(f"\n=== {model_key} ({model_id}) ===", flush=True)
    video_url = fal_client.upload_file(str(work_video))
    audio_url = fal_client.upload_file(str(padded_audio))
    api_args = _build_api_args(
        model_key, video_url=video_url, audio_url=audio_url, sync_mode=sync_mode
    )
    result = fal_client.subscribe(model_id, arguments=api_args, with_logs=True)
    if not isinstance(result, dict):
        raise RuntimeError(f"Lipsync failed: {result}")
    out_url = _video_url_from_lipsync_result(result)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stem = video_in.stem
    out_mp4 = out_dir / f"{stem}_{tag}_{model_key}_{ts}.mp4"
    download_file(out_url, out_mp4)
    meta_path = write_lipsync_meta(
        out_mp4,
        {
            "model": model_id,
            "model_key": model_key,
            "video_in": str(video_in),
            "audio_in": str(dialogue),
            "start_sec": start_sec,
            "video_duration_sec": video_dur,
            "output": str(out_mp4),
        },
    )
    print(f"Saved: {out_mp4}", flush=True)
    print(f"Meta: {meta_path}", flush=True)
    return out_mp4


def _video_url_from_lipsync_result(result: dict) -> str:
    video = result.get("video")
    if isinstance(video, dict) and video.get("url"):
        return str(video["url"])
    data = result.get("data")
    if isinstance(data, dict):
        video = data.get("video")
        if isinstance(video, dict) and video.get("url"):
            return str(video["url"])
    raise RuntimeError(f"No video URL in lipsync result: {result}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fal lip-sync on dialogue clip")
    parser.add_argument("--video", type=Path, help="Base visual MP4 (prefer silent I2V)")
    parser.add_argument("--audio", type=Path, help="Dialogue-only audio (mp3/wav)")
    parser.add_argument(
        "--dialogue-video",
        type=Path,
        help="Muxed dialogue MP4 — uses its audio track if --audio omitted",
    )
    parser.add_argument(
        "--start-sec",
        type=float,
        default=2.05,
        help="Dialogue start offset in base video (pad silence before speech)",
    )
    parser.add_argument(
        "--model",
        choices=tuple(MODELS.keys()),
        default=DEFAULT_LIPSYNC_MODEL,
        help=f"Lipsync backend (default: {DEFAULT_LIPSYNC_MODEL}; A/B: {', '.join(RECOMMENDED_FOR_ANIME)})",
    )
    parser.add_argument(
        "--all-models",
        action="store_true",
        help=f"Run A/B batch: {', '.join(RECOMMENDED_FOR_ANIME)}",
    )
    parser.add_argument(
        "--sync-mode",
        default="cut_off",
        choices=("cut_off", "loop", "bounce", "silence", "remap"),
        help="Sync.so models only",
    )
    parser.add_argument("--tag", type=str, default="lipsync")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "outputs" / "video" / "LipsyncTests",
        help="Output folder for lip-sync renders (default: outputs/video/LipsyncTests)",
    )
    args = parser.parse_args()

    if not read_fal_key():
        print("Missing FAL_KEY in .env", file=sys.stderr)
        return 1
    os.environ["FAL_KEY"] = read_fal_key() or ""

    if not args.video and not args.dialogue_video:
        print("Pass --video (silent base) or --dialogue-video", file=sys.stderr)
        return 1

    video_in = args.video.resolve() if args.video else args.dialogue_video.resolve()
    if not video_in.is_file():
        print(f"Video not found: {video_in}", file=sys.stderr)
        return 1

    video_dur = probe_duration(video_in)
    models_to_run = list(RECOMMENDED_FOR_ANIME) if args.all_models else [args.model]

    with tempfile.TemporaryDirectory(prefix="lipsync_") as tmp:
        tmp_path = Path(tmp)
        work_video = tmp_path / "video_in.mp4"
        _ensure_video_specs(video_in, work_video)

        if args.audio:
            dialogue = args.audio.resolve()
        elif args.dialogue_video:
            dialogue = tmp_path / "extracted.mp3"
            _extract_audio_from_video(args.dialogue_video.resolve(), dialogue)
        else:
            print("Pass --audio or --dialogue-video", file=sys.stderr)
            return 1

        if not dialogue.is_file():
            print(f"Audio not found: {dialogue}", file=sys.stderr)
            return 1

        padded = tmp_path / "audio_padded.mp3"
        _pad_audio_for_video(dialogue, video_dur, args.start_sec, padded)

        out_dir = args.out_dir.resolve()
        errors: list[str] = []
        for model_key in models_to_run:
            try:
                _run_one(
                    model_key,
                    work_video=work_video,
                    padded_audio=padded,
                    video_in=video_in,
                    dialogue=dialogue,
                    start_sec=args.start_sec,
                    video_dur=video_dur,
                    sync_mode=args.sync_mode,
                    tag=args.tag,
                    out_dir=out_dir,
                )
            except Exception as e:
                errors.append(f"{model_key}: {e}")
                print(f"FAILED {model_key}: {e}", file=sys.stderr)

        if errors and len(errors) == len(models_to_run):
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
