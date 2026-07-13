"""
Generate instrumental BGM via Fal **MiniMax Music 2.6** and optionally trim + mux under a prototype edit.

Default prompt: PrototypeFinal01 analysis in
`outputs/analysis/PrototypeFinal01_music_analysis_log.md`.

Docs: https://fal.ai/models/fal-ai/minimax-music/v2.6
Guideline: docs/prototype-video-music-analysis-guideline.md

Requires: FAL_KEY in project `.env`, package `fal-client`, ffmpeg on PATH for trim/mux.
"""

from __future__ import annotations

import argparse
import json
import os
import re
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
)

MODEL_ID = "fal-ai/minimax-music/v2.6"

PROTOTYPE_FINAL01_PROMPT = (
    "D minor, 76 BPM, fantasy anime underscore instrumental in the style of "
    "melancholic high-fantasy travel drama, soft piano and alto flute lead, "
    "gentle cello and harp, light orchestral strings entering after 45 seconds, "
    "very subtle brushed pulse only when the mood opens toward journey. "
    "Emotional arc for a 66 second film edit: sparse reflective forest camp and "
    "bittersweet memory at the start, quiet and dialogue-friendly, slowly adding "
    "harmonic weight through emotional conversation, then at halfway a gentle "
    "forward walking energy, finally a warm awe-filled swell as characters see a "
    "vast golden valley and distant walled city from a cliff, hopeful but still "
    "bittersweet, no vocals, no choir, no EDM, no trailer brass hits, no heavy "
    "percussion, mixed to sit under environmental foley."
)

DEFAULT_TRIM_DURATION = 65.8


def _extract_prompt_from_log(log_path: Path) -> str | None:
    text = log_path.read_text(encoding="utf-8")
    m = re.search(
        r"## MiniMax prompt \(instrumental\)\s*\n+\s*>\s*(.+?)(?=\n\n|\n\*\*API)",
        text,
        re.DOTALL,
    )
    if not m:
        return None
    return " ".join(m.group(1).split())


def _probe_duration(video: Path) -> float | None:
    ffmpeg = "ffmpeg"
    try:
        r = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(video),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return float(r.stdout.strip())
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
        return None


def _trim_and_fade(src: Path, duration: float, fade_start: float, fade_dur: float) -> Path:
    out = src.with_name(f"{src.stem}_trim{src.suffix}")
    fade_start = max(0.0, fade_start)
    fade_dur = max(0.1, fade_dur)
    af = f"afade=t=out:st={fade_start}:d={fade_dur}"
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-t",
        str(duration),
        "-af",
        af,
        "-c:a",
        "libmp3lame",
        "-q:a",
        "2",
        str(out),
    ]
    print(f"Trim/fade: {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, check=True)
    return out


def _mux_bgm(
    video: Path,
    bgm: Path,
    out: Path,
    bgm_volume: float,
    fade_start: float,
    fade_dur: float,
) -> None:
    dur = _probe_duration(video) or DEFAULT_TRIM_DURATION
    fade_start = min(fade_start, max(0.0, dur - 0.5))
    vol = bgm_volume
    fc = (
        f"[1:a]volume={vol},afade=t=out:st={fade_start}:d={fade_dur}[bgm];"
        f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=0[aout]"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video),
        "-i",
        str(bgm),
        "-filter_complex",
        fc,
        "-map",
        "0:v",
        "-map",
        "[aout]",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        str(out),
    ]
    print(f"Mux: {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="MiniMax Music 2.6 instrumental BGM")
    parser.add_argument(
        "--prompt",
        default=None,
        help="Style prompt (default: PrototypeFinal01 log prompt)",
    )
    parser.add_argument(
        "--from-log",
        type=Path,
        default=ROOT / "outputs" / "analysis" / "PrototypeFinal01_music_analysis_log.md",
        help="Read MiniMax prompt block from analysis log",
    )
    parser.add_argument(
        "--trim-duration",
        type=float,
        default=None,
        help=f"Trim BGM to N seconds (default: ffprobe of --mux-video or {DEFAULT_TRIM_DURATION})",
    )
    parser.add_argument("--fade-start", type=float, default=58.0, help="Fade-out start (seconds)")
    parser.add_argument("--fade-dur", type=float, default=2.0, help="Fade-out duration (seconds)")
    parser.add_argument("--bgm-volume", type=float, default=0.22, help="BGM level in mux mix")
    parser.add_argument(
        "--mux-video",
        type=Path,
        default=None,
        help="Mux trimmed BGM under this video (e.g. PrototypeFinal01.mp4)",
    )
    parser.add_argument(
        "--out-video",
        type=Path,
        default=None,
        help="Mux output path (default: <video_stem>_with_bgm_<ts>.mp4 next to source)",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    assert_model_allowed(MODEL_ID)
    key = read_fal_key()
    if not key:
        print("Missing FAL_KEY — set in .env at project root.", file=sys.stderr)
        return 1

    prompt = args.prompt
    if prompt is None and args.from_log and args.from_log.is_file():
        prompt = _extract_prompt_from_log(args.from_log.resolve())
    if not prompt:
        prompt = PROTOTYPE_FINAL01_PROMPT

    trim_dur = args.trim_duration
    if trim_dur is None and args.mux_video:
        trim_dur = _probe_duration(args.mux_video.resolve())
    if trim_dur is None:
        trim_dur = DEFAULT_TRIM_DURATION

    fade_start = args.fade_start
    if args.mux_video:
        vd = _probe_duration(args.mux_video.resolve())
        if vd:
            fade_start = max(0.0, vd - args.fade_dur)

    arguments = {
        "prompt": prompt,
        "is_instrumental": True,
        "lyrics_optimizer": False,
        "audio_setting": {
            "sample_rate": 44100,
            "bitrate": 256000,
            "format": "mp3",
        },
    }

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_audio_dir = ROOT / "outputs" / "audio" / "bgm"
    meta_dir = ROOT / "outputs" / "fal"
    out_audio_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)

    meta_path = meta_dir / f"bgm_minimax_meta_{ts}.json"
    meta_path.write_text(
        json.dumps(
            {"model_id": MODEL_ID, "trim_duration": trim_dur, "arguments": arguments},
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Meta: {meta_path}", flush=True)

    if args.dry_run:
        print(json.dumps(arguments, indent=2))
        return 0

    os.environ["FAL_KEY"] = key
    print(f"Submitting {MODEL_ID} …", flush=True)
    try:
        result = fal_client.subscribe(MODEL_ID, arguments=arguments, with_logs=True)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    log_path = meta_dir / f"bgm_minimax_{ts}.json"
    log_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(f"Log: {log_path}", flush=True)

    audio = result.get("audio") if isinstance(result, dict) else None
    url = audio.get("url") if isinstance(audio, dict) else None
    if not url:
        print(f"No audio URL in result: {list(result.keys()) if isinstance(result, dict) else result}", file=sys.stderr)
        return 1

    ext = extension_from_url(url)
    if ext not in (".mp3", ".wav", ".flac"):
        ext = ".mp3"
    raw_dest = out_audio_dir / f"PrototypeFinal01_minimax-v26_{ts}{ext}"
    print(f"Downloading: {url}", flush=True)
    download_file(url, raw_dest)
    print(f"Saved raw BGM: {raw_dest}", flush=True)

    trimmed = _trim_and_fade(raw_dest, trim_dur, fade_start, args.fade_dur)
    print(f"Saved trimmed BGM: {trimmed}", flush=True)

    if args.mux_video:
        video = args.mux_video.resolve()
        if not video.is_file():
            print(f"Video not found: {video}", file=sys.stderr)
            return 1
        if args.out_video:
            out_v = args.out_video.resolve()
        else:
            out_v = video.with_name(f"{video.stem}_with_bgm_{ts}.mp4")
        _mux_bgm(video, trimmed, out_v, args.bgm_volume, fade_start, args.fade_dur)
        print(f"Saved muxed video: {out_v}", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
