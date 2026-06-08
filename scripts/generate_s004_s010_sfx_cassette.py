"""
S004–S010 — **CassetteAI SFX only** (no TTS, no Kling audio). Prompts are written for **foley / ambience only**
and explicitly forbid vocals — models can still drift; re-run singles if needed.

- Resolves `outputs/video/final/*s00N*` per shot for ffprobe → first `01_*` bed length.
- Writes `outputs/audio/sfx/S00N/cassetteai/`
- Meta: `outputs/fal/S004_S010_sfx_cassette_<ts>.json`

Usage:
  cd scripts
  python generate_s004_s010_sfx_cassette.py
  python generate_s004_s010_sfx_cassette.py --only S009
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
    "Sound effects only — absolutely no human voice, whisper, speech, dialogue, humming, singing, chanting, "
    "or music."
)


def _nv(s: str) -> str:
    return f"{s.strip()} {NO_VOCAL}"


@dataclass(frozen=True)
class CassetteJob:
    slug: str
    prompt: str
    default_seconds: int


# First job per shot must be slug starting with 01_ (ambient bed: duration from video when available).
SHOT_JOBS: dict[str, tuple[CassetteJob, ...]] = {
    "S004": (
        CassetteJob(
            slug="01_ambient_northern_forest_ms",
            prompt=_nv(
                "Cool Northern forest clearing daytime air, leaf litter, soft trees, intimate medium-shot depth, "
                "calm outdoor campsite continuation"
            ),
            default_seconds=15,
        ),
        CassetteJob(
            slug="02_grimoire_pages_dry",
            prompt=_nv(
                "Dry foley only: thick bound spellbook pages rustle, paper edge, slow turn, object-only — "
                "no reader, no breathing, no mouth noise"
            ),
            default_seconds=5,
        ),
        CassetteJob(
            slug="03_envelope_paper_soft",
            prompt=_nv(
                "Soft sealed paper envelope in hands, light crinkle and stiffness, delicate mail handling"
            ),
            default_seconds=4,
        ),
        CassetteJob(
            slug="04_winter_fabric_seated",
            prompt=_nv(
                "Micro-rustle of heavy winter coat and scarf, seated figures on forest floor, no footsteps, no movement bursts"
            ),
            default_seconds=5,
        ),
    ),
    "S005": (
        CassetteJob(
            slug="01_ambient_forest_cu_intimate",
            prompt=_nv(
                "Close quiet Northern forest air, shallow depth, leaf floor, still tension, soft daylight filter"
            ),
            default_seconds=15,
        ),
        CassetteJob(
            slug="02_paper_letter_handling",
            prompt=_nv(
                "Folded letter or paper in hands, soft crisp rustle, careful handling — paper only, no reading aloud"
            ),
            default_seconds=5,
        ),
        CassetteJob(
            slug="03_air_stillness_detail",
            prompt=_nv(
                "Very faint outdoor room tone, microscopic leaf tick on forest floor — environment texture only, no breath"
            ),
            default_seconds=4,
        ),
    ),
    "S006": (
        CassetteJob(
            slug="01_ambient_camp_daytime_ms",
            prompt=_nv(
                "Weise forest camp medium shot air, daytime, trees and clearing, faint leaf clutter, same region as earlier camp"
            ),
            default_seconds=15,
        ),
        CassetteJob(
            slug="02_distant_small_fire_crackle",
            prompt=_nv(
                "Very distant small campfire crackle and low wood tick — far field, not close-mic blaze"
            ),
            default_seconds=6,
        ),
        CassetteJob(
            slug="03_book_or_pages_subtle",
            prompt=_nv(
                "Barely audible paper or book shift at tree seat — dry short foley, no vocalization"
            ),
            default_seconds=4,
        ),
        CassetteJob(
            slug="04_fabric_seated_shift",
            prompt=_nv(
                "Winter travel clothing micro-rustle from seated argument posture, forest floor"
            ),
            default_seconds=5,
        ),
    ),
    "S007": (
        CassetteJob(
            slug="01_ambient_camp_daytime_layered",
            prompt=_nv(
                "Forest camp daytime ambience for layered composite shot — open clearing air, soft canopy, quiet tension"
            ),
            default_seconds=15,
        ),
        CassetteJob(
            slug="02_grimoire_boards_shift",
            prompt=_nv(
                "Heavy spellbook boards and pages tiny movement, leather weight, object foley close"
            ),
            default_seconds=5,
        ),
        CassetteJob(
            slug="03_winter_layers_fabric",
            prompt=_nv(
                "Coat and scarf subtle rustle, two seated figures, minimal gesture foley"
            ),
            default_seconds=5,
        ),
    ),
    "S008": (
        CassetteJob(
            slug="01_ambient_camp_clearing_day",
            prompt=_nv(
                "Bright daytime forest camp clearing, sun-fleck air, open space medium shot, energic but still natural"
            ),
            default_seconds=15,
        ),
        CassetteJob(
            slug="02_spellbook_pages_dry",
            prompt=_nv(
                "Open grimoire pages dry rustle, thick paper, slow foley, no implied speaker"
            ),
            default_seconds=5,
        ),
        CassetteJob(
            slug="03_winter_gear_fabric",
            prompt=_nv(
                "Back-turned figure coat and scarf plus distant seated rustle, small camp sounds"
            ),
            default_seconds=5,
        ),
    ),
    "S009": (
        CassetteJob(
            slug="01_ambient_forest_path_day",
            prompt=_nv(
                "Wide forest hiking path daytime, sun through canopy, dappled trail air, open walking corridor"
            ),
            default_seconds=15,
        ),
        CassetteJob(
            slug="02_footsteps_dirt_leaves_soft",
            prompt=_nv(
                "Soft dirt and dry leaves under several walkers, slow casual pace, leather boot scuffs, "
                "no crowd, no shouting — foot and ground foley only"
            ),
            default_seconds=8,
        ),
        CassetteJob(
            slug="03_travel_case_leather",
            prompt=_nv(
                "Large rectangular travel case leather creak and strap stress, walking sway foley"
            ),
            default_seconds=6,
        ),
        CassetteJob(
            slug="04_cloth_rustle_walk",
            prompt=_nv(
                "Winter coats and woven scarf motion from walking, fabric swish low level"
            ),
            default_seconds=6,
        ),
    ),
    "S010": (
        CassetteJob(
            slug="01_ambient_ridge_wind_wide",
            prompt=_nv(
                "High grass ridge overlook, gentle panoramic wind, airy vast valley space, soft tree line hiss, "
                "epic but peaceful"
            ),
            default_seconds=15,
        ),
        CassetteJob(
            slug="02_gold_valley_air_shimmer",
            prompt=_nv(
                "Distant golden citadel ambience — abstract soft metallic air shimmer, heat-haze tickle, no bells, no crowds"
            ),
            default_seconds=8,
        ),
        CassetteJob(
            slug="03_fabric_hair_soft_breeze",
            prompt=_nv(
                "Very light breeze on coats and long hair of standing figures seen from behind, cloth edge flutter minimal"
            ),
            default_seconds=6,
        ),
    ),
}

SHOT_ORDER: tuple[str, ...] = ("S004", "S005", "S006", "S007", "S008", "S009", "S010")


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

    parser = argparse.ArgumentParser(description="S004–S010 CassetteAI SFX batch (no voice)")
    parser.add_argument("--video-dir", type=Path, default=DEFAULT_VIDEO_DIR)
    parser.add_argument("--ambient-cap", type=int, default=30)
    parser.add_argument(
        "--only",
        dest="only_shot",
        metavar="S00N",
        help="Single shot id e.g. S009 (default: all S004–S010)",
    )
    args = parser.parse_args()

    video_dir = args.video_dir.resolve()
    run_shots: tuple[str, ...]
    if args.only_shot:
        s = args.only_shot.strip().upper()
        if s not in SHOT_JOBS:
            print(f"Unknown shot {s!r}. Use one of: {list(SHOT_JOBS)}", file=sys.stderr)
            return 1
        run_shots = (s,)
    else:
        run_shots = SHOT_ORDER

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    meta_dir = ROOT / "outputs" / "fal"
    meta_dir.mkdir(parents=True, exist_ok=True)
    all_meta: dict = {
        "model": CASSETTE_MODEL,
        "timestamp_utc": ts,
        "shots": [],
    }

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

    label = args.only_shot.strip().upper() if args.only_shot else "S004_S010"
    meta_path = meta_dir / f"{label}_sfx_cassette_{ts}.json"
    meta_path.write_text(json.dumps(all_meta, indent=2), encoding="utf-8")
    print(f"Meta: {meta_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
