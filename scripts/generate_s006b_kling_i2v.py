"""
S006B — Kling 2.6 Pro **continuation** I2V from the **end frame** of the 10s S006 clip.

**MS** camp hold — Fern **back to camera** at fire, Frieren at tree reading, Stark partial left.
Default: **`Tests/Final/S006B_nano-banana-2-edit_20260330T035743Z.png`**, **`duration` \"5\"**.
**`--anime-limited`** (default), **`--audio`** for native foley.

Requires: `FAL_KEY` in project `.env`, package `fal-client`.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import fal_client

from fal_common import (
    ROOT,
    assert_model_allowed,
    download_file,
    extension_from_url,
    read_fal_key,
    video_url_from_result,
)

SHOT_ID = "S006B"
MODEL_ID = "fal-ai/kling-video/v2.6/pro/image-to-video"

DEFAULT_START = ROOT / "Tests" / "Final" / "S006B_nano-banana-2-edit_20260330T035743Z.png"

NEGATIVE_BASE = (
    "blur, distort, low quality, manga panel, speech bubble, halftone, "
    "extra limbs, morphing face, duplicate Frieren, duplicate Fern, text, watermark, "
    "looking at camera, fourth wall, eye contact with lens, "
    "wide establishing reframe, pulling back, drone zoom out, new camera angle, camera orbit, "
    "Fern turning to face camera, Fern full face reveal, 180 degree turn, "
    "characters on log seats, squirrel, third traveler dominating frame"
)

NEGATIVE_ANIME_EXTRA = (
    "smooth cg camera orbit, mocap glide, hyperreal motion smear, "
    "continuous 3d parallax tour, gimbal float, lip-sync mouth flapping, dialogue animation"
)

MOTION_PROMPT_CINEMATIC = (
    "Fantasy anime, exact same medium-wide camp composition as the reference end frame — "
    "tripod-locked continuation shot, no reframe, no pull-back, no lens change. "
    "Foreground figure with purple hair and blue scarf, back to camera, crouched by campfire: "
    "subtle shoulder and scarf drift only, smallest weight shift on forest floor, hair ribbon tremor; "
    "does not turn around, does not face the lens, stays engaged toward the tree figure. "
    "Figure at large tree with open book: calm flat read, micro page edge flutter, silver pigtails and white coat drift in breeze; "
    "does not stand or walk. Partial red-coated figure at far left edge: nearly frozen, axe on ground unchanged. "
    "Campfire lower left: gentle flame flicker, thin smoke wisps, warm orange pulse on leaves and bark. "
    "Cool misty forest background holds still with soft leaf whisper. One continuous hold beat, no cuts, no manga texture, no on-screen text."
)

MOTION_PROMPT_ANIME_LIMITED = (
    "Fantasy broadcast anime television, cel-shaded, limited-animation timing — preserve exact reference end-frame layout; "
    "locked-off continuation plate, hand-drawn TV anime not 3D, animation on twos, short pose holds, gentle staccato, "
    "not mocap glide or video-game smoothness. "
    "Foreground traveler back to camera by fire: only scarf edge flutter and hair drift, discrete in-between beats, "
    "no turn to viewer, no face reveal, no mouth motion. "
    "Tree-seated reader with book: micro page flutter, coat and pigtail tremor, calm gaze down, no lip-sync, no stand. "
    "Edge warrior partial left: frozen silhouette. "
    "Campfire: simple 2D flame cycle and smoke wisps, warm bounce on nearby surfaces. "
    "Camera almost locked 2D anime plate, hairline environmental tremor at most; no dolly, no zoom, no parallax tour. "
    "Misty forest ambience. One continuous take, no cuts, no halftone, no text."
)

AUDIO_TAIL = (
    " Ambient forest camp night: soft wind in trees, campfire crackle and thin smoke, light cloth rustle; "
    "no speech, no dialogue, no singing, no music score."
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="S006B end-frame → Kling 2.6 Pro 5s continuation (locked camp hold)"
    )
    parser.add_argument("--start-image", type=Path, default=DEFAULT_START, help="End-frame still PNG")
    parser.add_argument(
        "--duration",
        choices=("5", "10"),
        default="5",
        help='Default "5" continuation beat',
    )
    parser.add_argument("--audio", action="store_true", help="generate_audio true (higher cost)")
    parser.add_argument(
        "--anime-limited",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="TV-anime limited-animation prompt (default on)",
    )
    parser.add_argument(
        "--anime-fps",
        type=int,
        default=12,
        metavar="N",
        help="ffmpeg fps post-pass (0=skip). Default 12.",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    start_path = args.start_image.resolve()

    assert_model_allowed(MODEL_ID)

    key = read_fal_key()
    if not key:
        print("Missing FAL_KEY — set in .env at project root.", file=sys.stderr)
        return 1

    if not start_path.is_file():
        print(f"Start image not found: {start_path}", file=sys.stderr)
        return 1

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "outputs" / "fal"
    video_dir = ROOT / "outputs" / "video"
    out_dir.mkdir(parents=True, exist_ok=True)
    video_dir.mkdir(parents=True, exist_ok=True)

    os.environ["FAL_KEY"] = key

    print(f"Uploading start frame: {start_path}", flush=True)
    start_url = fal_client.upload_file(str(start_path))
    print(f"start_image_url: {start_url}", flush=True)

    motion = MOTION_PROMPT_ANIME_LIMITED if args.anime_limited else MOTION_PROMPT_CINEMATIC
    if args.audio and AUDIO_TAIL.strip() not in motion:
        motion = motion + AUDIO_TAIL
    negative = NEGATIVE_BASE + (NEGATIVE_ANIME_EXTRA if args.anime_limited else "")

    arguments = {
        "prompt": motion,
        "start_image_url": start_url,
        "duration": args.duration,
        "generate_audio": args.audio,
        "negative_prompt": negative,
    }

    meta_path = out_dir / f"{SHOT_ID}_kling_i2v_meta_{ts}.json"
    meta_path.write_text(
        json.dumps(
            {
                "shot": SHOT_ID,
                "model_id": MODEL_ID,
                "start_image_local": str(start_path),
                "start_image_url": start_url,
                "arguments": arguments,
                "anime_limited": args.anime_limited,
                "anime_fps_post": args.anime_fps if args.anime_fps > 0 else None,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Meta: {meta_path}", flush=True)

    if args.dry_run:
        print(json.dumps(arguments, indent=2))
        return 0

    print(f"Submitting {MODEL_ID} …", flush=True)
    try:
        result = fal_client.subscribe(
            MODEL_ID,
            arguments=arguments,
            with_logs=True,
        )
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    log_path = out_dir / f"{SHOT_ID}_kling_i2v_{ts}.json"
    log_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(f"Log: {log_path}", flush=True)

    vurl = video_url_from_result(result)
    if not vurl:
        print(
            f"No video URL in response keys: {list(result.keys()) if isinstance(result, dict) else type(result)}",
            file=sys.stderr,
        )
        return 1

    ext = extension_from_url(vurl)
    if ext not in (".mp4", ".webm", ".mov"):
        ext = ".mp4"
    parts = ["anime" if args.anime_limited else "cine"]
    if args.audio:
        parts.append("audio")
    if args.anime_fps > 0:
        parts.append(f"{args.anime_fps}fps")
    tag = "-".join(parts)
    dest = video_dir / f"{SHOT_ID}_kling-v26-pro_i2v_{tag}_{ts}{ext}"
    print(f"Downloading: {vurl}", flush=True)
    download_file(vurl, dest)
    print(f"Saved: {dest}", flush=True)

    if args.anime_fps > 0:
        fps_dest = _downsample_fps(dest, args.anime_fps, ts)
        if fps_dest:
            print(f"Anime fps pass: {fps_dest}", flush=True)

    return 0


def _probe_has_audio(ffmpeg: str, src: Path) -> bool:
    ffprobe = shutil.which("ffprobe") or ffmpeg.replace("ffmpeg", "ffprobe")
    if not Path(ffprobe).exists() and ffprobe == ffmpeg.replace("ffmpeg", "ffprobe"):
        return False
    try:
        r = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-select_streams",
                "a",
                "-show_entries",
                "stream=codec_type",
                "-of",
                "csv=p=0",
                str(src),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return "audio" in (r.stdout or "")
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _downsample_fps(src: Path, fps: int, ts: str) -> Path | None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("ffmpeg not on PATH — skip --anime-fps post-pass.", file=sys.stderr)
        return None
    out = src.with_name(f"{src.stem}_{fps}fps_{ts}{src.suffix}")
    has_audio = _probe_has_audio(ffmpeg, src)
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(src),
        "-vf",
        f"fps={fps}",
        "-c:v",
        "libx264",
        "-crf",
        "18",
        "-preset",
        "medium",
    ]
    if has_audio:
        cmd.extend(["-c:a", "aac", "-b:a", "192k"])
    else:
        cmd.append("-an")
    cmd.append(str(out))
    print(f"ffmpeg downsample to {fps} fps: {' '.join(cmd)}", flush=True)
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"ffmpeg failed: {e.stderr}", file=sys.stderr)
        return None
    return out


if __name__ == "__main__":
    raise SystemExit(main())
