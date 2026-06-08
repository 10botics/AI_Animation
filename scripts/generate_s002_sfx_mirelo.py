"""
S002 — **Mirelo** SFX on your final clip.

Default: **video-to-video** (`mirelo-ai/sfx-v1.5/video-to-video`) — returns **MP4(s)** with a new mixed soundtrack.
Alt: **`--model mirelo-ai/sfx-v1.5/video-to-audio`** — **WAV** samples only under `outputs/audio/...`.

Uses **final S002** + **text_prompt** (camp, wind, small fire, no voices — same spirit as `sfx_from_video` S002).

- In: `outputs/video/final/*s002*.mp4` (uploaded to Fal storage)
- Out (v2v): `outputs/video/sfx/S002_mirelo_v2v_*_<ts>.mp4`
- Out (v2a): `outputs/audio/sfx/S002/mirelo/*.wav`
- Meta: `outputs/fal/S002_sfx_mirelo_v2v_<ts>.json` or `..._v2a_<ts>.json`
- Run log: `outputs/fal/S002_mirelo_run_<ts>.log`

Usage:
  cd scripts
  python generate_s002_sfx_mirelo.py
  python generate_s002_sfx_mirelo.py --model mirelo-ai/sfx-v1.5/video-to-audio
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import IO, TextIO

import fal_client
from fal_client import FalClientHTTPError, FalClientTimeoutError

from fal_common import ROOT, download_file, extension_from_url, read_fal_key

SHOT_ID = "S002"
DEFAULT_VIDEO_DIR = ROOT / "outputs" / "video" / "final"
DEFAULT_MODEL = "mirelo-ai/sfx-v1.5/video-to-video"

# Match SHOT_THINKSOUND_HINTS["S002"] + explicit no-voice guardrails.
S002_MIRELO_PROMPT = (
    "Northern forest camp daytime: small campfire crackle at low level, trees and leaves in soft wind, "
    "travelers resting, canvas and fabric micro-rustle, subtle book-page and gear foley, "
    "no speech, no dialogue, no singing, no crowd, no narration"
)


def find_shot_video(video_dir: Path, shot: str) -> Path | None:
    if not video_dir.is_dir():
        return None
    token = re.escape(shot.lower())
    pat = re.compile(rf"{token}", re.IGNORECASE)
    vids: list[Path] = []
    for p in sorted(video_dir.iterdir()):
        if not p.is_file():
            continue
        if p.suffix.lower() not in (".mp4", ".webm", ".mov", ".mkv", ".m4v"):
            continue
        if pat.search(p.name):
            vids.append(p)
    return vids[0] if vids else None


def probe_duration_seconds(video_path: Path) -> float | None:
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
                str(video_path),
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if r.returncode != 0 or not r.stdout.strip():
            return None
        return float(r.stdout.strip())
    except (FileNotFoundError, ValueError, subprocess.TimeoutExpired):
        return None


def _unwrap_payload(result: object) -> dict:
    if not isinstance(result, dict):
        return {}
    inner = result.get("data")
    if isinstance(inner, dict):
        return inner
    return result


def _mirelo_media_urls(payload: dict, result_key: str) -> list[tuple[str, str]]:
    """Return list of (url, suggested_base_name) from Mirelo `audio` or `video` list output."""
    out: list[tuple[str, str]] = []
    items = payload.get(result_key)
    if not isinstance(items, list):
        return out
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        url = item.get("url")
        if not isinstance(url, str):
            continue
        fn = item.get("file_name")
        base = fn if isinstance(fn, str) else f"sample_{i + 1}"
        out.append((url, Path(base).stem))
    return out


def _mirelo_result_key(model: str) -> str:
    return "video" if "video-to-video" in model else "audio"


_TRANSIENT_FAL_ERROR_TYPES: frozenset[str] = frozenset(
    {
        "runner_scheduling_failure",
        "runner_connection_timeout",
        "runner_disconnected",
        "runner_connection_refused",
        "runner_connection_error",
        "startup_timeout",
    }
)


def _retryable_fal_http(e: FalClientHTTPError) -> bool:
    if e.error_type in _TRANSIENT_FAL_ERROR_TYPES:
        return True
    headers = {k.lower(): v for k, v in e.response_headers.items()}
    if headers.get("x-fal-retryable", "").lower() == "true" and e.status_code >= 500:
        return True
    return False


class _TeeTextStream:
    def __init__(self, primary: TextIO, log_fp: TextIO) -> None:
        self._primary = primary
        self._log = log_fp

    def write(self, s: str) -> int:
        self._primary.write(s)
        self._log.write(s)
        self._log.flush()
        return len(s)

    def flush(self) -> None:
        self._primary.flush()
        self._log.flush()

    def isatty(self) -> bool:
        return self._primary.isatty()


def _subscribe_mirelo(
    model: str,
    arguments: dict,
    *,
    client_timeout: float,
    max_retries: int,
    retry_base_sleep: float,
) -> dict:
    res = None
    for attempt in range(max(1, max_retries)):
        try:
            res = fal_client.subscribe(model, arguments=arguments, with_logs=True, client_timeout=client_timeout)
            break
        except FalClientTimeoutError as e:
            print(
                f"ERROR: Fal client timeout after {client_timeout:g}s. request_id={e.request_id!r}",
                file=sys.stderr,
            )
            raise
        except FalClientHTTPError as e:
            if not _retryable_fal_http(e) or attempt >= max_retries - 1:
                raise
            wait = min(60.0, retry_base_sleep * (2**attempt))
            print(f"  transient Fal error (attempt {attempt + 1}/{max_retries}), sleep {wait:.0f}s …", flush=True)
            time.sleep(wait)
    if res is None:
        raise RuntimeError("subscribe returned no result")
    if not isinstance(res, dict):
        return {}
    return res


def main() -> int:
    parser = argparse.ArgumentParser(description=f"{SHOT_ID} SFX — Mirelo (video-to-video or video-to-audio)")
    parser.add_argument("--video-dir", type=Path, default=DEFAULT_VIDEO_DIR)
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=(
            f"Fal model id (default {DEFAULT_MODEL}). "
            "Alts: mirelo-ai/sfx-v1.5/video-to-audio, mirelo-ai/sfx-v1/video-to-video"
        ),
    )
    parser.add_argument(
        "--text-prompt",
        default=S002_MIRELO_PROMPT,
        help="Guides SFX content; default is S002 camp/forest foley, no voices.",
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=2,
        help="Mirelo num_samples (Fal requires >= 2)",
    )
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--start-offset", type=float, default=0.0)
    parser.add_argument(
        "--client-timeout",
        type=float,
        default=300.0,
        help="Seconds to wait for the Mirelo job (default 300).",
    )
    parser.add_argument("--max-retries", type=int, default=10)
    parser.add_argument("--retry-base-sleep", type=float, default=8.0)
    parser.add_argument("--no-run-log", action="store_true")
    args = parser.parse_args()
    if args.num_samples < 2:
        print("Note: Mirelo API requires num_samples >= 2; using 2.", flush=True)
        args.num_samples = 2

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    meta_dir = ROOT / "outputs" / "fal"
    meta_dir.mkdir(parents=True, exist_ok=True)
    run_log_path: Path | None = None
    log_fp: IO[str] | None = None
    old_out, old_err = sys.stdout, sys.stderr

    if not args.no_run_log:
        run_log_path = meta_dir / f"{SHOT_ID}_mirelo_run_{ts}.log"
        log_fp = run_log_path.open("w", encoding="utf-8")
        sys.stdout = _TeeTextStream(sys.__stdout__, log_fp)
        sys.stderr = _TeeTextStream(sys.__stderr__, log_fp)

    try:
        return _main_run(args, ts, run_log_path)
    finally:
        if log_fp is not None:
            sys.stdout, sys.stderr = old_out, old_err
            log_fp.close()


def _main_run(args: argparse.Namespace, ts: str, run_log_path: Path | None) -> int:
    if not read_fal_key():
        print("Missing FAL_KEY — set it in .env at repo root.", file=sys.stderr)
        return 1

    video_dir = args.video_dir.resolve()
    ref_video = find_shot_video(video_dir, SHOT_ID)
    if not ref_video:
        print(f"No *{SHOT_ID}* video under {video_dir}. Mirelo needs a local final clip.", file=sys.stderr)
        return 1

    vid_dur = probe_duration_seconds(ref_video)
    print(f"Reference video: {ref_video}", flush=True)
    if vid_dur is not None:
        print(f"ffprobe duration: {vid_dur:.2f}s", flush=True)
    else:
        print("ffprobe: could not read duration — using API default duration 10s", flush=True)

    duration = round(vid_dur, 2) if vid_dur is not None else 10.0
    duration = max(1.0, duration)

    result_key = _mirelo_result_key(args.model)
    v2v = result_key == "video"
    meta_suffix = "v2v" if v2v else "v2a"
    if v2v:
        out_dir = ROOT / "outputs" / "video" / "sfx"
    else:
        out_dir = ROOT / "outputs" / "audio" / "sfx" / SHOT_ID / "mirelo"
    meta_dir = ROOT / "outputs" / "fal"
    out_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)

    if run_log_path is not None:
        print(f"Run log: {run_log_path}", flush=True)
    print(
        f"Args: model={args.model} result={result_key} client_timeout={args.client_timeout:g}s "
        f"num_samples={args.num_samples} duration={duration:g} start_offset={args.start_offset:g}",
        flush=True,
    )

    print("Uploading video …", flush=True)
    video_url = fal_client.upload_file(str(ref_video.resolve()))
    print(f"  video_url: {video_url}", flush=True)

    m_args: dict = {
        "video_url": video_url,
        "text_prompt": args.text_prompt.strip(),
        "num_samples": args.num_samples,
        "start_offset": float(args.start_offset),
        "duration": float(duration),
    }
    if args.seed is not None:
        m_args["seed"] = int(args.seed)

    meta: dict = {
        "shot": SHOT_ID,
        "model": args.model,
        "timestamp_utc": ts,
        "run_log": str(run_log_path) if run_log_path else None,
        "reference_video": str(ref_video),
        "video_duration_sec": vid_dur,
        "arguments": m_args,
        "outputs": [],
    }

    print(f"[Mirelo] subscribe ({args.model}) …", flush=True)
    try:
        raw = _subscribe_mirelo(
            args.model,
            m_args,
            client_timeout=args.client_timeout,
            max_retries=args.max_retries,
            retry_base_sleep=args.retry_base_sleep,
        )
    except FalClientTimeoutError:
        return 1
    except FalClientHTTPError as e:
        print(f"ERROR: HTTP {e.status_code} error_type={e.error_type!r} — {e.message}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if isinstance(raw, dict):
        print(f"  fal top-level keys: {sorted(raw.keys())}", flush=True)
    pay = _unwrap_payload(raw)
    pairs = _mirelo_media_urls(pay, result_key)
    if not pairs:
        print(f"No {result_key} URLs in payload: {raw}", file=sys.stderr)
        return 1

    for i, (url, base) in enumerate(pairs):
        ext = extension_from_url(url)
        if v2v:
            if ext not in (".mp4", ".webm", ".mov", ".mkv", ".m4v"):
                ext = ".mp4"
            dest = out_dir / f"{SHOT_ID}_mirelo_v2v_{i + 1:02d}_{ts}{ext}"
        else:
            if ext not in (".wav", ".mp3", ".flac"):
                ext = ".wav"
            dest = out_dir / f"{base}_{i + 1:02d}_{ts}{ext}"
        print(f"  downloading: {result_key} {i + 1}/{len(pairs)} …", flush=True)
        download_file(url, dest)
        print(f"  saved: {dest}", flush=True)
        meta["outputs"].append({"url": url, "local_path": str(dest)})

    meta_path = meta_dir / f"{SHOT_ID}_sfx_mirelo_{meta_suffix}_{ts}.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Meta: {meta_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
