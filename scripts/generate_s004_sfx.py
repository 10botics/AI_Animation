"""
S004 â€” AI SFX for the Weise camp grimoire + envelope beat (see stage_02 / S004_PROMPT_FLUX).

Runs **both** Fal text-to-SFX models:
  - `cassetteai/sound-effects-generator` (~$0.01 / gen per Fal docs)
  - `beatoven/sound-effect-generation` (~$0.1 / req per Fal docs)

Defaults:
  - Resolve reference clip: `outputs/video/final/` â€” first file whose name contains `s004` (case-insensitive).
  - Writes WAV/MP3 to `outputs/audio/sfx/S004/<model_id>/`.

Requires: FAL_KEY in project `.env`, `fal-client`, optional `ffprobe` (PATH) to size ambient bed to picture length.
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

SHOT_ID = "S004"
DEFAULT_VIDEO_DIR = ROOT / "outputs" / "video" / "final"
CASSETTE_MODEL = "cassetteai/sound-effects-generator"
BEATOVEN_MODEL = "beatoven/sound-effect-generation"


@dataclass(frozen=True)
class SfxJob:
    # Foley jobs use fixed short lengths; ambient bed uses video duration when ffprobe works.
    slug: str
    cassette_prompt: str
    beatoven_prompt: str
    beatoven_negative: str
    foley_seconds_cassette: int
    foley_seconds_beatoven: float


# Derived from Chapter-81 stage_02 S004 + fal_common S004 (Northern forest camp, open grimoire, sealed envelope, quiet beat).
S004_JOBS: tuple[SfxJob, ...] = (
    SfxJob(
        slug="01_ambient_forest_bed",
        cassette_prompt=(
            "Cool Northern forest daytime ambience, soft breeze through trees, subtle dry leaves on the ground, "
            "distant single bird very sparse, open air campsite feel, calm and quiet, no music, no voices"
        ),
        beatoven_prompt=(
            "Fantasy anime forest camp daytime ambience: gentle wind in pine and bare branches, faint leaf rustle, "
            "soft outdoor air, peaceful and intimate, very low bird presence, cinematic wide natural space"
        ),
        beatoven_negative="speech, dialogue, voices, singing, music, melody, crowd, traffic, urban, explosion, laughter",
        foley_seconds_cassette=15,
        foley_seconds_beatoven=12.0,
    ),
    SfxJob(
        slug="02_grimoire_pages_soft",
        cassette_prompt=(
            "Close-up dry foley only: heavy spellbook pages rustling, thick paper, slow careful turn, spine and board weight, "
            "unmanned book — no reader, no breathing. Absolutely no human voice, whisper, mumble, hum, reading aloud, or music"
        ),
        beatoven_prompt=(
            "Intimate foley: bound grimoire pages shifting and turning slowly, parchment weight, close mic, "
            "object-only — no person, no mouth, no vocalization"
        ),
        beatoven_negative=(
            "speech, voice, whisper, murmur, humming, reading aloud, vocals, human dialogue, music, singing, "
            "loud crack, explosion, wind storm, footsteps outdoors"
        ),
        foley_seconds_cassette=5,
        foley_seconds_beatoven=5.0,
    ),
    SfxJob(
        slug="03_envelope_paper_crinkle",
        cassette_prompt=(
            "Soft paper envelope in hands, subtle crinkle and stiffness, small handheld movement, close foley only, "
            "no human voice, whisper, hum, or mouth noise, no music"
        ),
        beatoven_prompt=(
            "Delicate paper envelope handling: light crinkle, rigid flap, one quiet shift as if presenting a letter, "
            "very subtle, indoors-outdoor quiet forest backdrop only as room tone not wind blast"
        ),
        beatoven_negative=(
            "speech, voice, whisper, murmur, humming, reading, vocals, music, tearing rip, loud plastic, thunder"
        ),
        foley_seconds_cassette=4,
        foley_seconds_beatoven=4.0,
    ),
    SfxJob(
        slug="04_cloth_winter_soft",
        cassette_prompt=(
            "Very soft winter coat and scarf fabric rustle, person seated on forest floor, minimal movement, no steps, "
            "no voice"
        ),
        beatoven_prompt=(
            "Ultra-subtle foley: heavy winter coat and woven scarf micro-rustle from seated posture adjustment, "
            "forest floor very faint, no footsteps, no voice"
        ),
        beatoven_negative="speech, music, loud zipper, jangling keys, strong wind gust",
        foley_seconds_cassette=4,
        foley_seconds_beatoven=4.0,
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


def _audio_url_from_beatoven(payload: dict) -> str | None:
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
        print("Missing FAL_KEY â€” set it in .env at repo root.", file=sys.stderr)
        return 1

    parser = argparse.ArgumentParser(description=f"{SHOT_ID} dual-model SFX batch (CassetteAI + Beatoven)")
    parser.add_argument(
        "--video-dir",
        type=Path,
        default=DEFAULT_VIDEO_DIR,
        help=f"Folder to scan for *{SHOT_ID}* video (default: {DEFAULT_VIDEO_DIR})",
    )
    parser.add_argument(
        "--ambient-cap-cassette",
        type=int,
        default=30,
        help="Max seconds for CassetteAI ambient bed (API max 30)",
    )
    parser.add_argument(
        "--ambient-cap-beatoven",
        type=float,
        default=35.0,
        help="Max seconds for Beatoven ambient bed (API max 35)",
    )
    parser.add_argument("--skip-cassette", action="store_true")
    parser.add_argument("--skip-beatoven", action="store_true")
    args = parser.parse_args()

    video_dir = args.video_dir.resolve()
    ref_video = find_shot_video(video_dir, SHOT_ID)
    vid_dur: float | None = probe_duration_seconds(ref_video) if ref_video else None

    if ref_video:
        print(f"Reference video: {ref_video}", flush=True)
        if vid_dur is not None:
            print(f"ffprobe duration: {vid_dur:.2f}s", flush=True)
        else:
            print("ffprobe unavailable or failed â€” using default ambient lengths from jobs.", flush=True)
    else:
        print(
            f"No *{SHOT_ID}* video under {video_dir} â€” ambient bed uses default job seconds.",
            flush=True,
        )

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_root = ROOT / "outputs" / "audio" / "sfx" / SHOT_ID
    cassette_dir = out_root / "cassetteai"
    beatoven_dir = out_root / "beatoven"
    meta_dir = ROOT / "outputs" / "fal"
    meta_dir.mkdir(parents=True, exist_ok=True)
    cassette_dir.mkdir(parents=True, exist_ok=True)
    beatoven_dir.mkdir(parents=True, exist_ok=True)

    ambient_c: int
    ambient_b: float
    if vid_dur is not None:
        ambient_c = max(1, min(int(round(vid_dur)), args.ambient_cap_cassette))
        ambient_b = max(
            1.0,
            min(round(float(vid_dur), 2), round(args.ambient_cap_beatoven, 2)),
        )
    else:
        ambient_c = S004_JOBS[0].foley_seconds_cassette
        ambient_b = S004_JOBS[0].foley_seconds_beatoven

    meta_log: dict = {
        "shot": SHOT_ID,
        "timestamp_utc": ts,
        "reference_video": str(ref_video) if ref_video else None,
        "video_duration_sec": vid_dur,
        "ambient_seconds": {"cassetteai": ambient_c, "beatoven": ambient_b},
        "generations": [],
    }

    for job in S004_JOBS:
        is_bed = job.slug.startswith("01_")
        dur_c = ambient_c if is_bed else job.foley_seconds_cassette
        dur_b = float(ambient_b if is_bed else round(job.foley_seconds_beatoven, 2))

        if not args.skip_cassette:
            print(f"[CassetteAI] {job.slug} ({dur_c}s) â€¦", flush=True)
            try:
                res_c = fal_client.subscribe(
                    CASSETTE_MODEL,
                    arguments={"prompt": job.cassette_prompt, "duration": dur_c},
                    with_logs=True,
                )
            except Exception as e:
                print(f"ERROR CassetteAI {job.slug}: {e}", file=sys.stderr)
                return 1
            pay_c = _unwrap_payload(res_c)
            url_c = _audio_url_from_cassette(pay_c)
            if not url_c:
                print(f"No audio_file URL in response for {job.slug}: {res_c}", file=sys.stderr)
                return 1
            ext_c = extension_from_url(url_c)
            if ext_c not in (".wav", ".mp3", ".flac"):
                ext_c = ".wav"
            dest_c = cassette_dir / f"{job.slug}_{ts}{ext_c}"
            download_file(url_c, dest_c)
            print(f"  saved: {dest_c}", flush=True)
            meta_log["generations"].append(
                {
                    "model": CASSETTE_MODEL,
                    "slug": job.slug,
                    "duration": dur_c,
                    "prompt": job.cassette_prompt,
                    "local_path": str(dest_c),
                }
            )

        if not args.skip_beatoven:
            print(f"[Beatoven] {job.slug} ({dur_b}s) â€¦", flush=True)
            b_args: dict = {
                "prompt": job.beatoven_prompt,
                "negative_prompt": job.beatoven_negative,
                "duration": float(dur_b),
                "refinement": 40,
                "creativity": 14,
            }
            try:
                res_b = fal_client.subscribe(BEATOVEN_MODEL, arguments=b_args, with_logs=True)
            except Exception as e:
                print(f"ERROR Beatoven {job.slug}: {e}", file=sys.stderr)
                return 1
            pay_b = _unwrap_payload(res_b)
            url_b = _audio_url_from_beatoven(pay_b)
            if not url_b:
                print(f"No audio URL in response for {job.slug}: {res_b}", file=sys.stderr)
                return 1
            ext_b = extension_from_url(url_b)
            if ext_b not in (".wav", ".mp3", ".flac"):
                ext_b = ".wav"
            dest_b = beatoven_dir / f"{job.slug}_{ts}{ext_b}"
            download_file(url_b, dest_b)
            print(f"  saved: {dest_b}", flush=True)
            meta_log["generations"].append(
                {
                    "model": BEATOVEN_MODEL,
                    "slug": job.slug,
                    "duration": dur_b,
                    "prompt": job.beatoven_prompt,
                    "negative_prompt": job.beatoven_negative,
                    "local_path": str(dest_b),
                }
            )

    meta_path = meta_dir / f"{SHOT_ID}_sfx_dual_{ts}.json"
    meta_path.write_text(json.dumps(meta_log, indent=2), encoding="utf-8")
    print(f"Meta: {meta_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
