"""
S003 — **Fern + squirrel messenger** MCU SFX via **CassetteAI only**.

Scene: stage_02 S003 + fal_common S003_PROMPT_FLUX — forest floor, tan leather satchel, small squirrel-like creature, winter clothing, beat before a letter.

- Video: `outputs/video/final/*s003*` (case-insensitive); ffprobe sizes ambient bed.
- Output: `outputs/audio/sfx/S003/cassetteai/`
- Meta: `outputs/fal/S003_sfx_cassette_<ts>.json`

Usage:
  cd scripts
  python generate_s003_sfx.py
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import fal_client

from fal_common import ROOT, download_file, extension_from_url, read_fal_key

SHOT_ID = "S003"
DEFAULT_VIDEO_DIR = ROOT / "outputs" / "video" / "final"
CASSETTE_MODEL = "cassetteai/sound-effects-generator"


@dataclass(frozen=True)
class CassetteJob:
    slug: str
    prompt: str
    default_seconds: int


S003_JOBS: tuple[CassetteJob, ...] = (
    CassetteJob(
        slug="01_ambient_forest_floor_mcu",
        prompt=(
            "Cool Northern forest floor ambience, daytime, dry leaves and sparse grass, soft distant trees, "
            "intimate outdoor close perspective, calm and still, gentle air, no voices, no music"
        ),
        default_seconds=15,
    ),
    CassetteJob(
        slug="02_small_rodent_in_bag",
        prompt=(
            "Very soft foley: small squirrel-sized forest animal inside an open leather satchel on the ground, "
            "subtle fur rustle, tiny delicate paw adjustment on fabric, no loud squeals, no cartoon chatter, "
            "no human speech, natural and quiet"
        ),
        default_seconds=6,
    ),
    CassetteJob(
        slug="03_leather_satchel_creak",
        prompt=(
            "Tan leather travel bag on forest soil, soft creak of straps and flap, canvas or mail-sack undertone, "
            "gentle handling weight, no voices, no music"
        ),
        default_seconds=6,
    ),
    CassetteJob(
        slug="04_winter_coat_scarf_seated",
        prompt=(
            "Winter jacket and thick woven scarf micro-rustle, person seated on leaf-strewn ground, idle posture, "
            "no footsteps, no voice, intimate foley"
        ),
        default_seconds=5,
    ),
    CassetteJob(
        slug="05_mail_paper_soft",
        prompt=(
            "Soft paper or letter inside a mail bag shifting slightly, delicate crisp rustle only, very subtle, no tearing. "
            "Pure object foley — no human voice, whisper, reading, or vocal reaction; no music"
        ),
        default_seconds=4,
    ),
)


def _unwrap_payload(result: object) -> dict:
    if not isinstance(result, dict):
        return {}
    inner = result.get("data")
    if isinstance(inner, dict):
        return inner
    return result


def _audio_url_from_cassette(payload: dict) -> str | None:
    f = payload.get("audio_file")
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
    if not read_fal_key():
        print("Missing FAL_KEY — set it in .env at repo root.", file=sys.stderr)
        return 1

    parser = argparse.ArgumentParser(description=f"{SHOT_ID} SFX — CassetteAI only")
    parser.add_argument("--video-dir", type=Path, default=DEFAULT_VIDEO_DIR)
    parser.add_argument("--ambient-cap", type=int, default=30, help="Cassette max duration (API 1–30)")
    args = parser.parse_args()

    video_dir = args.video_dir.resolve()
    ref_video = find_shot_video(video_dir, SHOT_ID)
    vid_dur = probe_duration_seconds(ref_video) if ref_video else None

    if ref_video:
        print(f"Reference video: {ref_video}", flush=True)
        if vid_dur is not None:
            print(f"ffprobe duration: {vid_dur:.2f}s", flush=True)
    else:
        print(f"No *{SHOT_ID}* video under {video_dir} — ambient uses default seconds.", flush=True)

    if vid_dur is not None:
        ambient_len = max(1, min(int(round(vid_dur)), args.ambient_cap))
    else:
        ambient_len = S003_JOBS[0].default_seconds

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "outputs" / "audio" / "sfx" / SHOT_ID / "cassetteai"
    meta_dir = ROOT / "outputs" / "fal"
    out_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)

    meta: dict = {
        "shot": SHOT_ID,
        "model": CASSETTE_MODEL,
        "timestamp_utc": ts,
        "reference_video": str(ref_video) if ref_video else None,
        "video_duration_sec": vid_dur,
        "generations": [],
    }

    for job in S003_JOBS:
        is_bed = job.slug.startswith("01_")
        dur = ambient_len if is_bed else max(1, min(job.default_seconds, 30))
        print(f"[CassetteAI] {job.slug} ({dur}s) ...", flush=True)
        try:
            res = fal_client.subscribe(
                CASSETTE_MODEL,
                arguments={"prompt": job.prompt, "duration": dur},
                with_logs=True,
            )
        except Exception as e:
            print(f"ERROR {job.slug}: {e}", file=sys.stderr)
            return 1
        pay = _unwrap_payload(res)
        url = _audio_url_from_cassette(pay)
        if not url:
            print(f"No audio_file URL: {res}", file=sys.stderr)
            return 1
        ext = extension_from_url(url)
        if ext not in (".wav", ".mp3", ".flac"):
            ext = ".wav"
        dest = out_dir / f"{job.slug}_{ts}{ext}"
        download_file(url, dest)
        print(f"  saved: {dest}", flush=True)
        meta["generations"].append(
            {"slug": job.slug, "duration": dur, "prompt": job.prompt, "local_path": str(dest)}
        )

    meta_path = meta_dir / f"{SHOT_ID}_sfx_cassette_{ts}.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Meta: {meta_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
