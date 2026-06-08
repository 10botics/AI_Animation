"""
S008 — Kling 2.6 Pro **image-to-video** from an approved Stage 4 still.

**MS** B3 daytime camp trio: Fern back to camera; mage right with open grimoire; figure rear left.
Default: **`Tests/Final/S008_nano-banana-2-edit_20260330T042818Z.png`**, **`duration` \"5\"**.
**`--motion`** `natural` | `anime-limited` | `cinematic` — default **`natural`** (S009-style alive timing, seated camp).
**`--audio`** for native foley.

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

SHOT_ID = "S008"
MODEL_ID = "fal-ai/kling-video/v2.6/pro/image-to-video"

DEFAULT_START = ROOT / "Tests" / "Final" / "S008_nano-banana-2-edit_20260330T042818Z.png"

NEGATIVE_BASE = (
    "blur, distort, low quality, manga panel, speech bubble, halftone, "
    "extra limbs, morphing face, duplicate person, wrong left-right order, text, watermark, "
    "looking at camera, fourth wall, wide pull-back, new camera angle, drone, "
    "fourth character, squirrel, traveler holding open grimoire instead of seated mage on right, log seats"
)

NEGATIVE_ANIME_EXTRA = (
    "smooth cg camera orbit, mocap glide, hyperreal motion smear, "
    "continuous 3d parallax tour, gimbal float, lip-sync mouth flapping, dialogue animation"
)

NEGATIVE_NATURAL_EXTRA = (
    "robotic march, lockstep movement, stiff vertical piston bounce, toy-like repetition, "
    "mechanical bobbing, moonwalk, ice skating, parade marching, stiff anime jog cycles, "
    "lip-sync, mouth movement, talking, jaw flap, phoneme shapes, dialogue animation, lip flapping, "
    "eye blink, blinking, eyelid close, hand morphing, distorted fingers, finger crawl, claw hands, "
    "extra fingers, warped grimoire grip"
)

# S009 exp3 alive timing adapted for seated MS camp — natural body, not lockstep or stiff I2V.
MOTION_PROMPT_NATURAL = (
    "Fantasy anime television, bright daytime Northern forest camp — same medium shot as the reference, panel-locked. "
    "Left-to-right: Stark back left seated, Fern center-foreground back or three-quarter to camera, Frieren right with open grimoire on forest floor. "
    "Do not reframe wide, do not mirror. "
    "Living beat — slow, casual, alive like quiet campsite talk: each figure has their own relaxed timing half a beat apart, not lockstep, not robotic. "
    "Natural seated body physics — soft weight shifts on hips and shoulders, visible easy breath, fabric and hair lag and catch up with follow-through. "
    "Frieren: subtle eager read — hands and wrists locked on the open grimoire exactly as the still, stable grip, no finger articulation, no tracing or page-turn hand motion; only whisper of page-edge flutter and pigtails or white coat settling after torso micro-shift; small natural head tilt toward the book only; stays seated, closed mouth. "
    "Fern: organic shoulder roll and soft lean toward Frieren, spine uncurls a fraction then settles; purple hair and blue scarf drag and catch up after the move; does not take the book, closed mouth. "
    "Stark rear left: face frozen to match the reference still — same eyes-open expression, no blink, no eyelid movement, no smile or frown change; body-only slump-breathe in shoulders and torso, one slow strap tug between beats, knee micro-shift on the ground; no step into center, closed mouth. "
    "Environment: dappled canopy light slides on bark and leaves; campfire flame flicker if visible; gentle woodland breeze. "
    "Camera — intimate but grounded: slow documentary handheld breathing micro-float and organic micro-sway on the locked frame, "
    "plus a very gradual intimate push-in inches only — no whip pan, no orbital tour, no wide pull-back; trio stays dominant. "
    "One continuous grimoire-deal beat, no cuts, no manga texture, no on-screen text, no new people."
)

MOTION_PROMPT_CINEMATIC = MOTION_PROMPT_NATURAL

MOTION_PROMPT_ANIME_LIMITED = (
    "Fantasy broadcast anime television, cel-shaded, limited-animation timing — preserve exact reference medium shot and left-right order: "
    "warrior back left, traveler center back to camera, seated mage right with open grimoire. "
    "Motion grammar — hand-drawn TV anime, not 3D: short pose holds, discrete beats, gentle staccato like animation on twos, "
    "not mocap glide. Keep movement small. "
    "Mage right: micro page flutter, coat and pigtails drift in whispers; seated, no lip-sync, no turn to lens. "
    "Center traveler: scarf and hair drift only, does not take the book, no lean into frame. "
    "Rear left warrior: nearly frozen, tiny shoulder slump only. "
    "Environment: leaf shimmer, gentle wind. "
    "Camera almost locked 2D anime plate, hairline tremor at most; no dolly, no parallax tour. "
    "One continuous take, no cuts, no manga halftone, no text, no fourth person."
)

AUDIO_TAIL = (
    " Ambient forest camp day: soft wind in trees, campfire crackle and thin smoke, light cloth and page rustle; "
    "no speech, no dialogue, no vocalizations, no singing, no music score."
)


def main() -> int:
    parser = argparse.ArgumentParser(description="S008 → Kling 2.6 Pro I2V (MS grimoire trio)")
    parser.add_argument("--start-image", type=Path, default=DEFAULT_START, help="Hero still PNG")
    parser.add_argument(
        "--duration",
        choices=("5", "10"),
        default="5",
        help='Default "5" for MS beat ("10" for slower read)',
    )
    parser.add_argument("--audio", action="store_true", help="generate_audio true (higher cost)")
    parser.add_argument(
        "--motion",
        choices=("natural", "anime-limited", "cinematic"),
        default="natural",
        help="natural = S009-style alive timing (seated); anime-limited = on-twos staccato; cinematic = alias of natural",
    )
    parser.add_argument(
        "--anime-limited",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Deprecated: use --motion anime-limited. Overrides --motion when set.",
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

    motion_style = (
        "anime-limited"
        if args.anime_limited is True
        else ("cinematic" if args.anime_limited is False else args.motion)
    )
    if motion_style == "anime-limited":
        motion = MOTION_PROMPT_ANIME_LIMITED
        negative = NEGATIVE_BASE + NEGATIVE_ANIME_EXTRA
    else:
        motion = MOTION_PROMPT_NATURAL
        negative = NEGATIVE_BASE + NEGATIVE_NATURAL_EXTRA
    if args.audio and AUDIO_TAIL.strip() not in motion:
        motion = motion + AUDIO_TAIL

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
                "motion_style": motion_style,
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
    parts = [motion_style]
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
