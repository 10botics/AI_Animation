"""
S002 — **Beatoven** text-to-SFX (`beatoven/sound-effect-generation`).

Same four stems as `generate_s002_sfx.py`, plus **`negative_prompt`** to steer away from voices.

Fal **503 / runner_scheduling_failure** means no serverless runner was allocated (transient). Official
notes: https://docs.fal.ai/documentation/model-apis/request-errors — retry or wait; the queue may retry
automatically. This script retries subscribe with backoff for those error types.

- ffprobe on `outputs/video/final/*s002*` sizes the ambient bed (1–35s).
- Out: `outputs/audio/sfx/S002/beatoven/*.wav` (written **after each** Fal job finishes — not upfront)
- Meta: `outputs/fal/S002_sfx_beatoven_<ts>.json`
- Run log (stdout+stderr): `outputs/fal/S002_beatoven_run_<ts>.log`

Usage:
  cd scripts
  python generate_s002_sfx_beatoven.py
  python generate_s002_sfx_beatoven.py --client-timeout 120
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import IO, TextIO

import fal_client
from fal_client import FalClientHTTPError, FalClientTimeoutError

from fal_common import ROOT, download_file, extension_from_url, read_fal_key

SHOT_ID = "S002"
DEFAULT_VIDEO_DIR = ROOT / "outputs" / "video" / "final"
BEATOVEN_MODEL = "beatoven/sound-effect-generation"

NEGATIVE_GLOBAL = (
    "speech, human voice, whisper, mumbling, dialogue, talking, singing, humming, chanting, lyrics, "
    "crowd chatter, announcer, narration, music melody, full orchestra, drums beat, song"
)


@dataclass(frozen=True)
class BeatovenJob:
    slug: str
    prompt: str
    default_seconds: float
    negative_extra: str = ""

    def negative(self) -> str:
        if not self.negative_extra:
            return NEGATIVE_GLOBAL
        return f"{NEGATIVE_GLOBAL} {self.negative_extra}"


S002_JOBS: tuple[BeatovenJob, ...] = (
    BeatovenJob(
        slug="01_ambient_forest_camp_bed",
        prompt=(
            "Northern temperate forest clearing daytime ambience, open campsite space, soft breeze in trees, "
            "dry leaves and earth, cool air, very sparse distant bird, peaceful rest stop"
        ),
        default_seconds=15.0,
        negative_extra="explosion, traffic, city",
    ),
    BeatovenJob(
        slug="02_campfire_small_crackle",
        prompt=(
            "Small camping fire crackling gently, modest flames, soft wood snaps and ember ticks, intimate outdoor scale, "
            "not a huge bonfire"
        ),
        default_seconds=8.0,
        negative_extra="explosion, bonfire roar",
    ),
    BeatovenJob(
        slug="03_book_pages_soft",
        prompt=(
            "Dry foley only: heavy book pages rustle slowly, crisp paper edge, spine creak, close mic, "
            "unmanned object — paper and binding materials only"
        ),
        default_seconds=5.0,
        negative_extra="breathing, page flip cartoon",
    ),
    BeatovenJob(
        slug="04_gear_fabric_ground",
        prompt=(
            "Subtle camping gear on forest floor: backpack straps, canvas or bedroll, winter coat micro-movement, "
            "seated stillness"
        ),
        default_seconds=5.0,
        negative_extra="footsteps running, zipper loud",
    ),
)


def _unwrap_payload(result: object) -> dict:
    if not isinstance(result, dict):
        return {}
    inner = result.get("data")
    if isinstance(inner, dict):
        return inner
    return result


def _audio_url_beatoven(payload: dict) -> str | None:
    f = payload.get("audio")
    if isinstance(f, dict) and isinstance(f.get("url"), str):
        return f["url"]
    return None


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
    """Align with https://docs.fal.ai/documentation/model-apis/request-errors (transient runner/timeout)."""
    if e.error_type in _TRANSIENT_FAL_ERROR_TYPES:
        return True
    headers = {k.lower(): v for k, v in e.response_headers.items()}
    if headers.get("x-fal-retryable", "").lower() == "true" and e.status_code >= 500:
        return True
    return False


class _TeeTextStream:
    """Mirror writes to the real console stream and a UTF-8 log file."""

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


def main() -> int:
    parser = argparse.ArgumentParser(description=f"{SHOT_ID} SFX — Beatoven")
    parser.add_argument("--video-dir", type=Path, default=DEFAULT_VIDEO_DIR)
    parser.add_argument("--ambient-cap", type=float, default=35.0, help="Beatoven max duration (API 1–35)")
    parser.add_argument("--creativity", type=float, default=12.0, help="1–20; lower = stick closer to prompt")
    parser.add_argument("--refinement", type=int, default=40)
    parser.add_argument(
        "--client-timeout",
        type=float,
        default=120.0,
        help="Seconds to wait per stem (fal_client; default 120). Increase if queue+generation often exceeds 2 min.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=10,
        help="Subscribe attempts per stem for transient Fal errors (e.g. 503 runner_scheduling_failure).",
    )
    parser.add_argument(
        "--retry-base-sleep",
        type=float,
        default=8.0,
        help="Base seconds before first retry; exponential backoff, capped at 60s.",
    )
    parser.add_argument(
        "--no-run-log",
        action="store_true",
        help="Do not write outputs/fal/S002_beatoven_run_<ts>.log",
    )
    args = parser.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    meta_dir = ROOT / "outputs" / "fal"
    meta_dir.mkdir(parents=True, exist_ok=True)
    run_log_path: Path | None = None
    log_fp: IO[str] | None = None
    old_out, old_err = sys.stdout, sys.stderr

    if not args.no_run_log:
        run_log_path = meta_dir / f"{SHOT_ID}_beatoven_run_{ts}.log"
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
    vid_dur = probe_duration_seconds(ref_video) if ref_video else None

    if ref_video:
        print(f"Reference video: {ref_video}", flush=True)
        if vid_dur is not None:
            print(f"ffprobe duration: {vid_dur:.2f}s", flush=True)
    else:
        print(f"No *{SHOT_ID}* video under {video_dir} — ambient uses default.", flush=True)

    if vid_dur is not None:
        ambient_len = max(1.0, min(round(vid_dur, 2), args.ambient_cap))
    else:
        ambient_len = S002_JOBS[0].default_seconds

    out_dir = ROOT / "outputs" / "audio" / "sfx" / SHOT_ID / "beatoven"
    meta_dir = ROOT / "outputs" / "fal"
    out_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)

    if run_log_path is not None:
        print(f"Run log: {run_log_path}", flush=True)
    print(
        f"Args: client_timeout={args.client_timeout:g}s max_retries={args.max_retries} "
        f"retry_base_sleep={args.retry_base_sleep:g}s refinement={args.refinement} creativity={args.creativity:g}",
        flush=True,
    )

    meta: dict = {
        "shot": SHOT_ID,
        "model": BEATOVEN_MODEL,
        "timestamp_utc": ts,
        "run_log": str(run_log_path) if run_log_path else None,
        "reference_video": str(ref_video) if ref_video else None,
        "video_duration_sec": vid_dur,
        "generations": [],
    }

    for job in S002_JOBS:
        is_bed = job.slug.startswith("01_")
        dur = float(ambient_len if is_bed else min(job.default_seconds, 35.0))
        dur = max(1.0, min(dur, 35.0))
        neg = job.negative()
        b_args = {
            "prompt": job.prompt,
            "negative_prompt": neg,
            "duration": dur,
            "refinement": args.refinement,
            "creativity": max(1.0, min(args.creativity, 20.0)),
        }
        print(
            f"[Beatoven] {job.slug} ({dur}s) ... (timeout {args.client_timeout:g}s)",
            flush=True,
        )
        res = None
        for attempt in range(max(1, args.max_retries)):
            try:
                res = fal_client.subscribe(
                    BEATOVEN_MODEL,
                    arguments=b_args,
                    with_logs=True,
                    client_timeout=args.client_timeout,
                )
                break
            except FalClientTimeoutError as e:
                rid = e.request_id
                print(
                    f"ERROR {job.slug}: Fal client timeout after {args.client_timeout:g}s. "
                    f"request_id={rid!r} — check queue/billing at fal.ai; raise --client-timeout if generation is slow.",
                    file=sys.stderr,
                )
                return 1
            except FalClientHTTPError as e:
                if not _retryable_fal_http(e) or attempt >= args.max_retries - 1:
                    print(
                        f"ERROR {job.slug}: HTTP {e.status_code} "
                        f"error_type={e.error_type!r} — {e.message}",
                        file=sys.stderr,
                    )
                    return 1
                wait = min(60.0, args.retry_base_sleep * (2**attempt))
                print(
                    f"  transient Fal error (attempt {attempt + 1}/{args.max_retries}), "
                    f"sleep {wait:.0f}s …",
                    flush=True,
                )
                time.sleep(wait)
            except Exception as e:
                print(f"ERROR {job.slug}: {e}", file=sys.stderr)
                return 1
        if res is None:
            return 1
        pay = _unwrap_payload(res)
        if isinstance(res, dict):
            print(f"  fal response keys: {sorted(res.keys())}", flush=True)
        url = _audio_url_beatoven(pay)
        if not url:
            print(f"No audio URL: {res}", file=sys.stderr)
            return 1
        ext = extension_from_url(url)
        if ext not in (".wav", ".mp3", ".flac"):
            ext = ".wav"
        dest = out_dir / f"{job.slug}_{ts}{ext}"
        download_file(url, dest)
        print(f"  saved: {dest}", flush=True)
        meta["generations"].append(
            {
                "slug": job.slug,
                "duration": dur,
                "prompt": job.prompt,
                "negative_prompt": neg,
                "local_path": str(dest),
            }
        )

    meta_path = meta_dir / f"{SHOT_ID}_sfx_beatoven_{ts}.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Meta: {meta_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
