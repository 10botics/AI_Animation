"""
Normalize all legacy artifact paths and filenames into shot-folder + audio/bgm layout.

Usage:
  python normalize_artifacts.py --dry-run
  python normalize_artifacts.py
  python normalize_artifacts.py --copy   # keep legacy copies
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from artifact_paths import (
    AUDIO,
    SHOTS,
    TIMESTAMP_FMT,
    approved_filename_for,
    bgm_approved_path,
    bgm_wip_path,
    ensure_all_shot_layouts,
    ensure_parent,
    lipsync_approved_path,
    lipsync_wip_path,
    migrate_flat_approved_files,
    parse_bgm_vendor,
    parse_lipsync_model,
    parse_media_timestamp,
    parse_shot_from_name,
    parse_sfx_tag,
    parse_still_filename,
    parse_video_model,
    parse_voice_speaker,
    sfx_wip_path,
    still_approved_path,
    video_approved_path,
    video_wip_path,
    voice_approved_path,
    voice_wip_path,
    wip_still_dest,
)
from fal_common import ROOT

VIDEO_DIALOGUE_SKIP = ("compare", "qwen", "silent_for_lipsync")
UNSORTED = SHOTS / "_unsorted"


def _transfer(src: Path, dest: Path, *, copy: bool, dry_run: bool) -> bool:
    if not src.is_file():
        return False
    if dest.is_file():
        try:
            if dest.stat().st_size == src.stat().st_size:
                return False
        except OSError:
            pass
    if dry_run:
        print(f"  {'copy' if copy else 'move'} {src.name} -> {dest.relative_to(ROOT)}")
        return True
    ensure_parent(dest)
    if copy:
        shutil.copy2(src, dest)
    else:
        shutil.move(str(src), str(dest))
    return True


def _is_lipsync_name(name: str) -> bool:
    n = name.lower()
    return any(t in n for t in ("pixverse", "musetalk", "latentsync", "heygen", "lipsync", "sync-pro", "fernmask", "frirenmask"))


def _video_tag(name: str, timestamp: str) -> str:
    n = name.lower()
    if "post12fps" in n:
        return "post12fps"
    if "_12fps_" in n and "12fps" in n:
        return "12fps"
    return ""


def _parse_video_vendor_from_sfx(name: str) -> str:
    n = name.lower()
    if "mirelo" in n:
        return "mirelo-v2v"
    if "thinksound" in n:
        return "thinksound"
    if "kling_v2a" in n or "kling-v2a" in n:
        return "kling-v2a"
    return "sfx-video"


def migrate_stills(tests_dir: Path, *, copy: bool, dry_run: bool) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    if not tests_dir.is_dir():
        return counts

    for src in sorted(tests_dir.rglob("*")):
        if not src.is_file() or src.suffix.lower() not in (".png", ".jpg", ".webp"):
            continue
        if "old" in {p.lower() for p in src.parts}:
            continue
        if "Final" in src.parts:
            continue

        parsed = parse_still_filename(src.name)
        if not parsed:
            print(f"  skip still: {src.name}", file=sys.stderr)
            continue
        if _transfer(src, wip_still_dest(parsed), copy=copy, dry_run=dry_run):
            counts["still_wip"] += 1

    final_dir = tests_dir / "Final"
    if final_dir.is_dir():
        by_shot: dict[str, list[Path]] = defaultdict(list)
        for src in final_dir.iterdir():
            if src.is_file() and parse_shot_from_name(src.name):
                by_shot[parse_shot_from_name(src.name) or ""].append(src)

        for shot, paths in by_shot.items():
            if not shot:
                continue
            newest = max(paths, key=lambda p: p.stat().st_mtime)
            if _transfer(
                newest,
                still_approved_path(shot, approved_filename_for(newest, kind="still")),
                copy=True,
                dry_run=dry_run,
            ):
                counts["still_approved"] += 1
            for src in paths:
                parsed = parse_still_filename(src.name)
                if parsed and not wip_still_dest(parsed).is_file():
                    if _transfer(src, wip_still_dest(parsed), copy=True, dry_run=dry_run):
                        counts["still_wip"] += 1
    return counts


def migrate_voice(voice_root: Path, *, copy: bool, dry_run: bool) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    if not voice_root.is_dir():
        return counts

    for src in voice_root.rglob("*"):
        if not src.is_file() or src.suffix.lower() not in (".wav", ".mp3"):
            continue
        shot = None
        for part in src.parts:
            if hit := parse_shot_from_name(part):
                shot = hit
                break
        if not shot:
            shot = parse_shot_from_name(src.name)
        if not shot:
            continue

        ts = parse_media_timestamp(src.name) or datetime.fromtimestamp(src.stat().st_mtime, tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
        speaker = parse_voice_speaker(src.name)
        is_final = "final" in {p.lower() for p in src.parts}

        if is_final:
            if _transfer(src, voice_approved_path(shot, speaker, src.suffix), copy=True, dry_run=dry_run):
                counts["voice_approved"] += 1
        else:
            tag = parse_sfx_tag(src.name, ts) if speaker in ("unknown", src.stem.lower()) else speaker
            if _transfer(src, voice_wip_path(shot, ts, src.suffix, tag=tag), copy=copy, dry_run=dry_run):
                counts["voice_wip"] += 1
    return counts


def _classify_video(src: Path, video_root: Path) -> str:
    parts = {p.lower() for p in src.parts}
    if "lipsynctests" in parts or "voice added" in parts or "mask" in parts:
        return "lipsync"
    if _is_lipsync_name(src.name):
        return "lipsync"
    if "sfx" in parts:
        return "video_sfx"
    if any(s in src.name.lower() for s in VIDEO_DIALOGUE_SKIP):
        return "skip"
    return "video"


def migrate_videos(video_root: Path, *, copy: bool, dry_run: bool) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    if not video_root.is_dir():
        return counts

    final_dir = video_root / "final"
    buckets: dict[str, dict[str, list[Path]]] = defaultdict(lambda: defaultdict(list))

    for src in video_root.rglob("*"):
        if not src.is_file() or src.suffix.lower() not in (".mp4", ".webm", ".mov"):
            continue
        if "meta" in {p.lower() for p in src.parts}:
            continue

        shot = parse_shot_from_name(src.name)
        if not shot:
            continue

        kind = _classify_video(src, video_root)
        if kind == "skip":
            continue
        buckets[kind][shot].append(src)

    for shot, paths in buckets["video"].items():
        live = [p for p in paths if p.is_file()]
        if not live:
            continue
        final_paths = [p for p in live if final_dir.is_dir() and final_dir in p.parents]
        newest = max(final_paths or live, key=lambda p: p.stat().st_mtime)
        if _transfer(
            newest,
            video_approved_path(shot, approved_filename_for(newest, kind="video")),
            copy=True,
            dry_run=dry_run,
        ):
            counts["video_approved"] += 1
        for src in live:
            ts = parse_media_timestamp(src.name) or datetime.fromtimestamp(src.stat().st_mtime, tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
            tag = _video_tag(src.name, ts)
            dest = video_wip_path(shot, parse_video_model(src.name), ts, src.suffix, tag=tag)
            if _transfer(src, dest, copy=copy, dry_run=dry_run):
                counts["video_wip"] += 1

    for shot, paths in buckets["lipsync"].items():
        live = [p for p in paths if p.is_file()]
        if not live:
            continue
        newest = max(live, key=lambda p: p.stat().st_mtime)
        if _transfer(
            newest,
            lipsync_approved_path(shot, approved_filename_for(newest, kind="lipsync")),
            copy=True,
            dry_run=dry_run,
        ):
            counts["lipsync_approved"] += 1
        for src in live:
            ts = parse_media_timestamp(src.name) or datetime.fromtimestamp(src.stat().st_mtime, tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
            tag = "mask" if "mask" in src.name.lower() else ""
            dest = lipsync_wip_path(shot, parse_lipsync_model(src.name), ts, src.suffix, tag=tag)
            if _transfer(src, dest, copy=copy, dry_run=dry_run):
                counts["lipsync_wip"] += 1

    for shot, paths in buckets["video_sfx"].items():
        for src in [p for p in paths if p.is_file()]:
            ts = parse_media_timestamp(src.name) or datetime.fromtimestamp(src.stat().st_mtime, tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
            vendor = _parse_video_vendor_from_sfx(src.name)
            tag = parse_sfx_tag(src.name, ts)
            dest = video_wip_path(shot, vendor, ts, src.suffix, tag=tag)
            if _transfer(src, dest, copy=copy, dry_run=dry_run):
                counts["video_sfx"] += 1
    return counts


def migrate_videos_main(videos_main: Path, *, copy: bool, dry_run: bool) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    if not videos_main.is_dir():
        return counts

    for src in videos_main.iterdir():
        if not src.is_file() or src.suffix.lower() not in (".mp4", ".webm", ".mov"):
            continue

        shot = parse_shot_from_name(src.name)
        if not shot:
            ts = parse_media_timestamp(src.name) or datetime.fromtimestamp(src.stat().st_mtime, tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
            kind = "lipsync" if _is_lipsync_name(src.name) else "video"
            model = parse_lipsync_model(src.name) if kind == "lipsync" else "unknown"
            if kind == "lipsync":
                dest = UNSORTED / "lipsync" / "wip" / model / f"{src.stem[:32]}_{ts}{src.suffix}"
            else:
                dest = UNSORTED / "video" / "wip" / "unknown" / f"{ts}{src.suffix}"
            if _transfer(src, dest, copy=copy, dry_run=dry_run):
                counts["videos_main_unsorted"] += 1
            continue

        ts = parse_media_timestamp(src.name) or datetime.fromtimestamp(src.stat().st_mtime, tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
        if _is_lipsync_name(src.name):
            dest = lipsync_wip_path(shot, parse_lipsync_model(src.name), ts, src.suffix)
            if _transfer(src, dest, copy=copy, dry_run=dry_run):
                counts["videos_main_lipsync"] += 1
        else:
            dest = video_wip_path(shot, parse_video_model(src.name), ts, src.suffix)
            if _transfer(src, dest, copy=copy, dry_run=dry_run):
                counts["videos_main_video"] += 1
    return counts


def cleanup_videos_main(videos_main: Path, *, dry_run: bool) -> int:
    """Remove VideosMain files that already exist under shots/ (same size)."""
    if not videos_main.is_dir():
        return 0
    removed = 0
    for src in list(videos_main.iterdir()):
        if not src.is_file():
            continue
        shot = parse_shot_from_name(src.name)
        ts = parse_media_timestamp(src.name)
        if not shot or not ts:
            continue
        shot_dir = ROOT / "shots" / shot
        if not shot_dir.is_dir():
            continue
        if any(
            c.is_file() and c.stat().st_size == src.stat().st_size
            for c in shot_dir.rglob(f"*{ts}*")
        ):
            if dry_run:
                print(f"  remove duplicate {src.name}")
            else:
                src.unlink()
            removed += 1
    return removed


def migrate_audio_sfx(audio_root: Path, *, copy: bool, dry_run: bool) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    sfx_root = audio_root / "sfx"
    if not sfx_root.is_dir():
        return counts

    for src in sfx_root.rglob("*"):
        if not src.is_file() or src.suffix.lower() not in (".wav", ".mp3", ".flac"):
            continue
        shot = None
        for part in src.parts:
            if hit := parse_shot_from_name(part):
                shot = hit
                break
        if not shot:
            continue
        vendor = src.parent.name.lower().replace("_", "-")
        ts = parse_media_timestamp(src.name) or datetime.fromtimestamp(src.stat().st_mtime, tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
        tag = parse_sfx_tag(src.name, ts)
        dest = sfx_wip_path(shot, vendor, ts, src.suffix, tag=tag)
        if _transfer(src, dest, copy=copy, dry_run=dry_run):
            counts["sfx_wip"] += 1
    return counts


def migrate_bgm(audio_root: Path, *, copy: bool, dry_run: bool) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    bgm_root = audio_root / "bgm"
    if not bgm_root.is_dir():
        return counts

    tracks: list[Path] = []
    for src in bgm_root.iterdir():
        if not src.is_file() or src.suffix.lower() not in (".mp3", ".wav", ".flac"):
            continue
        if src.name.startswith("approved"):
            continue
        tracks.append(src)

    if not tracks:
        return counts

    newest = max(tracks, key=lambda p: p.stat().st_mtime)
    if _transfer(
        newest,
        bgm_approved_path(approved_filename_for(newest, kind="bgm")),
        copy=True,
        dry_run=dry_run,
    ):
        counts["bgm_approved"] += 1

    for src in tracks:
        ts = parse_media_timestamp(src.name) or datetime.fromtimestamp(src.stat().st_mtime, tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
        vendor = parse_bgm_vendor(src.name)
        tag = "trim" if "trim" in src.stem.lower() else "prototype"
        dest = bgm_wip_path(vendor, ts, src.suffix, tag=tag)
        if _transfer(src, dest, copy=copy, dry_run=dry_run):
            counts["bgm_wip"] += 1
    return counts


def write_manifest(dry_run: bool) -> None:
    manifest = SHOTS / "_migration.json"
    payload = {
        "normalized_at": datetime.now(timezone.utc).isoformat(),
        "layout": {
            "shots": "shots/S###/{still,voice,video,lipsync,sfx}/{wip,approved}",
            "bgm": "audio/bgm/{wip,approved}/",
        },
    }
    if dry_run:
        print(f"Would write {manifest.relative_to(ROOT)}")
        return
    ensure_parent(manifest)
    manifest.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize all artifact paths and filenames")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--copy", action="store_true", help="Copy instead of move")
    parser.add_argument(
        "--ensure-layout",
        action="store_true",
        help="Only create missing shots/S###/{still,voice,video,lipsync}/approved/ folders",
    )
    args = parser.parse_args()

    if args.ensure_layout:
        if args.dry_run:
            print("Would ensure approved/ folders under every shots/S### (no --dry-run effect; run without --dry-run)", flush=True)
            return 0
        counts = ensure_all_shot_layouts()
        print(f"Ensured layout for {counts['shots']} shot(s); created {counts['dirs_created']} approved/ folder(s)", flush=True)
        return 0

    totals: dict[str, int] = defaultdict(int)

    steps = (
        ("Tests/ stills", lambda: migrate_stills(ROOT / "Tests", copy=args.copy, dry_run=args.dry_run)),
        ("outputs/voice/", lambda: migrate_voice(ROOT / "outputs" / "voice", copy=args.copy, dry_run=args.dry_run)),
        ("outputs/video/", lambda: migrate_videos(ROOT / "outputs" / "video", copy=args.copy, dry_run=args.dry_run)),
        ("VideosMain/", lambda: migrate_videos_main(ROOT / "VideosMain", copy=args.copy, dry_run=args.dry_run)),
        ("VideosMain/ cleanup", lambda: {"videos_main_dupes": cleanup_videos_main(ROOT / "VideosMain", dry_run=args.dry_run)}),
        ("outputs/audio/sfx/", lambda: migrate_audio_sfx(ROOT / "outputs" / "audio", copy=args.copy, dry_run=args.dry_run)),
        ("outputs/audio/bgm/", lambda: migrate_bgm(ROOT / "outputs" / "audio", copy=args.copy, dry_run=args.dry_run)),
        ("flat approved/ files", lambda: migrate_flat_approved_files(dry_run=args.dry_run)),
    )

    for label, fn in steps:
        print(f"Normalizing {label}", flush=True)
        for k, n in fn().items():
            totals[k] += n

    write_manifest(args.dry_run)
    if not args.dry_run:
        layout = ensure_all_shot_layouts()
        totals["layout_dirs_created"] = layout["dirs_created"]

    print("\nSummary:", flush=True)
    for key, n in sorted(totals.items()):
        print(f"  {key}: {n}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
