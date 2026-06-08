"""
S011–S012 — CassetteAI SFX only (no voice / music cues in prompts). Scene refs: stage_02 S011–S012.

- Video: `outputs/video/final/*S011*` / `*S012*`
- Out: `outputs/audio/sfx/S011|cassetteai/`, `S012/...`
- Meta: `outputs/fal/S011_S012_sfx_cassette_<ts>.json`

Usage:
  cd scripts
  python generate_s011_s012_sfx_cassette.py
  python generate_s011_s012_sfx_cassette.py --only S012
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

DEFAULT_VIDEO_DIR = ROOT / "outputs" / "video" / "final"
CASSETTE_MODEL = "cassetteai/sound-effects-generator"

NO_VOCAL = (
    "Sound effects only — absolutely no human voice, whisper, speech, gasp, inhale, dialogue, humming, singing, "
    "or music."
)


def _nv(s: str) -> str:
    return f"{s.strip()} {NO_VOCAL}"


@dataclass(frozen=True)
class CassetteJob:
    slug: str
    prompt: str
    default_seconds: int


SHOT_JOBS: dict[str, tuple[CassetteJob, ...]] = {
    "S011": (
        CassetteJob(
            slug="01_ambient_gold_vista_mcu",
            prompt=_nv(
                "Open-air gold landscape panorama air, high vantage brightness, soft wind at ear height, vast valley "
                "acoustics, crisp daylight — no crowd, no celebration"
            ),
            default_seconds=15,
        ),
        CassetteJob(
            slug="02_distant_metallic_shimmer_air",
            prompt=_nv(
                "Abstract distant gilt terrain and citadel air vibration — soft metallic sparkle hiss, not bells, "
                "not marching — environmental only"
            ),
            default_seconds=8,
        ),
        CassetteJob(
            slug="03_winter_coat_leather_strap",
            prompt=_nv(
                "Heavy red winter coat and cross-body leather strap micro-stress as figure stands still facing vista, "
                "fabric and harness foley only"
            ),
            default_seconds=6,
        ),
        CassetteJob(
            slug="04_axe_sheathed_subtle",
            prompt=_nv(
                "Very faint wooden haft and metal axe head micro-clink from still body — single traveler gear, "
                "no weapon swing"
            ),
            default_seconds=4,
        ),
    ),
    "S012": (
        CassetteJob(
            slug="01_ambient_ridge_wide_three_backs",
            prompt=_nv(
                "Epic ridge overlook wide shot wind, grass and small plants rustle, huge open sky and distant golden "
                "forest-city air, calm awe without crowd noise"
            ),
            default_seconds=15,
        ),
        CassetteJob(
            slug="02_gilt_forest_and_city_hum",
            prompt=_nv(
                "Layered distant golden citadel and gilt treeline ambience — soft airy shimmer, no bells, no voices, "
                "fantasy vast scale"
            ),
            default_seconds=10,
        ),
        CassetteJob(
            slug="03_three_travelers_cloth_breeze",
            prompt=_nv(
                "Light breeze across three standing winter coats and long purple hair strand beside two shorter "
                "silhouettes — backs to camera, fabric edge motion only"
            ),
            default_seconds=8,
        ),
        CassetteJob(
            slug="04_ground_peak_gravel_grass",
            prompt=_nv(
                "Feet-ready ridge soil: sparse grass and fine grit, wind riffling surface particles, no foot stomps"
            ),
            default_seconds=5,
        ),
    ),
}

SHOT_ORDER: tuple[str, ...] = ("S011", "S012")


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
    token = re.escape(shot.casefold())
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

    parser = argparse.ArgumentParser(description="S011–S012 CassetteAI SFX (no voice)")
    parser.add_argument("--video-dir", type=Path, default=DEFAULT_VIDEO_DIR)
    parser.add_argument("--ambient-cap", type=int, default=30)
    parser.add_argument("--only", dest="only_shot", metavar="S011", help="Single shot e.g. S012")
    args = parser.parse_args()

    video_dir = args.video_dir.resolve()
    if args.only_shot:
        s = args.only_shot.strip().upper()
        if s not in SHOT_JOBS:
            print(f"Unknown shot {s!r}. Use: {list(SHOT_JOBS)}", file=sys.stderr)
            return 1
        run_shots: tuple[str, ...] = (s,)
    else:
        run_shots = SHOT_ORDER

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    meta_dir = ROOT / "outputs" / "fal"
    meta_dir.mkdir(parents=True, exist_ok=True)
    all_meta: dict = {"model": CASSETTE_MODEL, "timestamp_utc": ts, "shots": []}

    for shot in run_shots:
        jobs = SHOT_JOBS[shot]
        ref = find_shot_video(video_dir, shot)
        vid_dur = probe_duration_seconds(ref) if ref else None
        if ref:
            print(f"{shot} reference: {ref}", flush=True)
            if vid_dur is not None:
                print(f"  ffprobe: {vid_dur:.2f}s", flush=True)
        else:
            print(f"{shot}: no video match in {video_dir}", flush=True)

        if vid_dur is not None:
            ambient_len = max(1, min(int(round(vid_dur)), args.ambient_cap))
        else:
            ambient_len = jobs[0].default_seconds

        out_dir = ROOT / "outputs" / "audio" / "sfx" / shot / "cassetteai"
        out_dir.mkdir(parents=True, exist_ok=True)
        shot_generations: list[dict] = []

        for job in jobs:
            is_bed = job.slug.startswith("01_")
            dur = ambient_len if is_bed else max(1, min(job.default_seconds, 30))
            print(f"[CassetteAI] {shot} {job.slug} ({dur}s) ...", flush=True)
            try:
                res = fal_client.subscribe(
                    CASSETTE_MODEL,
                    arguments={"prompt": job.prompt, "duration": dur},
                    with_logs=True,
                )
            except Exception as e:
                print(f"ERROR {shot} {job.slug}: {e}", file=sys.stderr)
                return 1
            pay = _unwrap_payload(res)
            url = _audio_url_from_cassette(pay)
            if not url:
                print(f"No audio_file URL {shot} {job.slug}: {res}", file=sys.stderr)
                return 1
            ext = extension_from_url(url)
            if ext not in (".wav", ".mp3", ".flac"):
                ext = ".wav"
            dest = out_dir / f"{job.slug}_{ts}{ext}"
            download_file(url, dest)
            print(f"  saved: {dest}", flush=True)
            shot_generations.append(
                {
                    "slug": job.slug,
                    "duration": dur,
                    "prompt": job.prompt,
                    "local_path": str(dest),
                }
            )

        all_meta["shots"].append(
            {
                "shot": shot,
                "reference_video": str(ref) if ref else None,
                "video_duration_sec": vid_dur,
                "ambient_seconds": ambient_len,
                "generations": shot_generations,
            }
        )

    label = args.only_shot.strip().upper() if args.only_shot else "S011_S012"
    meta_path = meta_dir / f"{label}_sfx_cassette_{ts}.json"
    meta_path.write_text(json.dumps(all_meta, indent=2), encoding="utf-8")
    print(f"Meta: {meta_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
