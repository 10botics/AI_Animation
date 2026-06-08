"""
S002 — **ThinkSound audio-only** (`fal-ai/thinksound/audio`).

Video → **one** generated audio file (WAV/MP3 per URL), not a dubbed MP4. Same inputs idea as
`fal-ai/thinksound` (video + optional `prompt`); use when you only need the soundtrack.

- In: `outputs/video/final/*s002*.mp4` (uploaded to Fal storage)
- Out: `outputs/audio/sfx/S002/thinksound_audio/S002_thinksound_audio_<ts>.<ext>`
- Meta: `outputs/fal/S002_sfx_thinksound_audio_<ts>.json`
- Run log: `outputs/fal/S002_thinksound_audio_run_<ts>.log`

Usage:
  cd scripts
  python generate_s002_sfx_thinksound_audio.py
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
MODEL_ID = "fal-ai/thinksound/audio"

# Same as `SHOT_THINKSOUND_HINTS["S002"]` in sfx_from_video.py
S002_PROMPT = (
    "Northern forest camp daytime: small campfire crackle at low level, trees and leaves in soft wind, "
    "travelers resting, canvas and fabric micro-rustle, no voices, no animals loud"
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


def _unwrap_payload(result: object) -> dict:
    if not isinstance(result, dict):
        return {}
    inner = result.get("data")
    if isinstance(inner, dict):
        return inner
    return result


def _audio_file_url(payload: dict) -> str | None:
    f = payload.get("audio")
    if isinstance(f, dict) and isinstance(f.get("url"), str):
        return f["url"]
    return None


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


def _subscribe_with_retries(
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
    return res if isinstance(res, dict) else {}


def main() -> int:
    parser = argparse.ArgumentParser(description=f"{SHOT_ID} — ThinkSound audio (video → audio)")
    parser.add_argument("--video-dir", type=Path, default=DEFAULT_VIDEO_DIR)
    parser.add_argument(
        "--prompt",
        default=S002_PROMPT,
        help="Guides generated audio (default S002 camp / forest foley).",
    )
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--num-inference-steps", type=int, default=None)
    parser.add_argument("--cfg-scale", type=float, default=None)
    parser.add_argument(
        "--no-prompt",
        action="store_true",
        help="Omit prompt (API may derive from video).",
    )
    parser.add_argument("--client-timeout", type=float, default=300.0)
    parser.add_argument("--max-retries", type=int, default=10)
    parser.add_argument("--retry-base-sleep", type=float, default=8.0)
    parser.add_argument("--no-run-log", action="store_true")
    args = parser.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    meta_dir = ROOT / "outputs" / "fal"
    meta_dir.mkdir(parents=True, exist_ok=True)
    run_log_path: Path | None = None
    log_fp: IO[str] | None = None
    old_out, old_err = sys.stdout, sys.stderr

    if not args.no_run_log:
        run_log_path = meta_dir / f"{SHOT_ID}_thinksound_audio_run_{ts}.log"
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
        print(f"No *{SHOT_ID}* video under {video_dir}.", file=sys.stderr)
        return 1

    print(f"Reference video: {ref_video}", flush=True)
    out_dir = ROOT / "outputs" / "audio" / "sfx" / SHOT_ID / "thinksound_audio"
    meta_dir = ROOT / "outputs" / "fal"
    out_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)

    if run_log_path is not None:
        print(f"Run log: {run_log_path}", flush=True)
    print(f"Args: model={MODEL_ID} client_timeout={args.client_timeout:g}s", flush=True)

    print("Uploading video …", flush=True)
    video_url = fal_client.upload_file(str(ref_video.resolve()))
    print(f"  video_url: {video_url}", flush=True)

    t_args: dict = {"video_url": video_url}
    if not args.no_prompt and args.prompt.strip():
        t_args["prompt"] = args.prompt.strip()
    if args.seed is not None:
        t_args["seed"] = int(args.seed)
    if args.num_inference_steps is not None:
        t_args["num_inference_steps"] = int(args.num_inference_steps)
    if args.cfg_scale is not None:
        t_args["cfg_scale"] = float(args.cfg_scale)

    meta: dict = {
        "shot": SHOT_ID,
        "model": MODEL_ID,
        "timestamp_utc": ts,
        "run_log": str(run_log_path) if run_log_path else None,
        "reference_video": str(ref_video),
        "arguments": t_args,
    }

    print(f"[ThinkSound/audio] subscribe …", flush=True)
    try:
        raw = _subscribe_with_retries(
            MODEL_ID,
            t_args,
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
    url = _audio_file_url(pay)
    if not url:
        print(f"No audio URL in payload: {raw}", file=sys.stderr)
        return 1

    resolved_prompt = pay.get("prompt")
    if isinstance(resolved_prompt, str):
        print(f"  resolved prompt: {resolved_prompt[:200]}{'…' if len(resolved_prompt) > 200 else ''}", flush=True)
        meta["resolved_prompt"] = resolved_prompt

    ext = extension_from_url(url)
    if ext not in (".wav", ".mp3", ".flac", ".aac", ".m4a"):
        ext = ".wav"
    dest = out_dir / f"{SHOT_ID}_thinksound_audio_{ts}{ext}"
    download_file(url, dest)
    print(f"  saved: {dest}", flush=True)
    meta["output_audio"] = str(dest)
    meta["audio_url"] = url

    meta_path = meta_dir / f"{SHOT_ID}_sfx_thinksound_audio_{ts}.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Meta: {meta_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
