"""
Canonical shot-folder layout for AI_Animation production artifacts.

Layout (per shot S###):
  shots/S###/still/wip/{model}/{timestamp}.png
  shots/S###/still/approved/{timestamp}.png
  shots/S###/voice/wip/qwen/{timestamp}.wav
  shots/S###/voice/approved/{speaker}.wav
  shots/S###/video/wip/{model}/{timestamp}.mp4
  shots/S###/video/approved/{timestamp}.mp4
  shots/S###/lipsync/wip/{model}/{timestamp}.mp4
  shots/S###/lipsync/approved/{timestamp}.mp4
  shots/S###/sfx/wip/{vendor}/{tag}_{timestamp}.wav
  audio/bgm/wip/{vendor}/{tag}_{timestamp}.mp3
  audio/bgm/approved/{tag}_{timestamp}.mp3

Legacy flat names (still/approved.png, video/approved.mp4) remain readable.
Legacy paths (Tests/, outputs/voice/, outputs/video/) remain readable via fallbacks.
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from fal_common import ROOT

__all__ = [
    "ROOT",
    "SHOTS",
    "utc_timestamp",
    "normalize_shot_id",
    "shot_root",
    "still_wip_dir",
    "still_approved_dir",
    "still_approved_path",
    "still_wip_path",
    "voice_wip_dir",
    "voice_approved_dir",
    "voice_wip_path",
    "voice_approved_path",
    "video_wip_dir",
    "video_approved_dir",
    "video_approved_path",
    "video_wip_path",
    "lipsync_wip_dir",
    "lipsync_approved_dir",
    "lipsync_approved_path",
    "lipsync_wip_path",
    "sfx_wip_dir",
    "sfx_wip_path",
    "bgm_wip_dir",
    "bgm_wip_path",
    "bgm_approved_dir",
    "bgm_approved_path",
    "AUDIO",
    "parse_sfx_tag",
    "parse_bgm_vendor",
    "promote_voice_wip",
    "hero_still",
    "resolve_still",
    "hero_video",
    "hero_lipsync",
    "hero_voice",
    "scan_shot_artifacts",
    "promote_file",
    "promote_to_approved",
    "parse_still_filename",
    "wip_still_dest",
    "migrate_flat_approved_files",
    "approved_filename_for",
    "ensure_shot_layout",
    "ensure_all_shot_layouts",
    "SHOT_KINDS_WITH_APPROVED",
    "has_approved_artifact",
    "has_wip_artifact",
    "needs_promote",
]

SHOTS = ROOT / "shots"
AUDIO = ROOT / "audio"

APPROVED_DIRNAME = "approved"

# Kinds that use {kind}/approved/ (sfx is wip-only in this repo)
SHOT_KINDS_WITH_APPROVED: tuple[str, ...] = ("still", "voice", "video", "lipsync")

# Legacy flat approved filenames (pre-folder layout)
LEGACY_FLAT_APPROVED: dict[str, str] = {
    "still": "approved.png",
    "video": "approved.mp4",
    "lipsync": "approved.mp4",
}
LEGACY_FLAT_BGM = "approved.mp3"

# Known model folder names (wip subfolders)
STILL_MODEL_SUFFIXES: tuple[tuple[str, str], ...] = (
    ("nano-banana-2-edit", "nano-banana-2"),
    ("flux-2-pro-edit", "flux-2-pro"),
    ("flux-2-flex-edit", "flux-2-flex"),
    ("flux-2-flash", "flux-2-flash"),
    ("seedream-v5-lite-edit", "seedream-v5-lite"),
)

VIDEO_MODEL_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"seedance-2-fast-i2v", re.I), "seedance-2-fast"),
    (re.compile(r"seedance-2-i2v", re.I), "seedance-2"),
    (re.compile(r"kling-v26-pro", re.I), "kling-v26-pro"),
    (re.compile(r"kling", re.I), "kling"),
)

LIPSYNC_MODEL_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"pixverse", re.I), "pixverse"),
    (re.compile(r"musetalk", re.I), "musetalk"),
    (re.compile(r"latentsync", re.I), "latentsync"),
    (re.compile(r"sync-pro", re.I), "sync-pro"),
    (re.compile(r"heygen", re.I), "heygen"),
)

# WIP artifact timestamps: YYYYMMDD_HHMMSS (UTC, no T/Z)
TIMESTAMP_FMT = "%Y%m%d_%H%M%S"
TIMESTAMP_RE = re.compile(r"(\d{8})[_T](\d{6})Z?")
SHOT_PREFIX_RE = re.compile(r"^(S\d{3}[A-Z]?)", re.I)
VOICE_SPEAKER_RE = re.compile(r"(frieren|fern|stark|denken|lernen)", re.I)

MEDIA_EXTENSIONS: dict[str, tuple[str, ...]] = {
    "still": (".png", ".jpg", ".jpeg", ".webp"),
    "video": (".mp4", ".webm", ".mov"),
    "lipsync": (".mp4", ".webm", ".mov"),
    "voice": (".wav", ".mp3"),
    "bgm": (".mp3", ".wav", ".flac"),
}


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime(TIMESTAMP_FMT)


def normalize_timestamp(raw: str) -> str:
    """Convert legacy 20260527_054046 or new 20260527_054046 to canonical form."""
    m = TIMESTAMP_RE.search(raw)
    if not m:
        return raw
    return f"{m.group(1)}_{m.group(2)}"


def normalize_shot_id(shot_id: str) -> str:
    return shot_id.upper()


def shot_root(shot_id: str) -> Path:
    return SHOTS / normalize_shot_id(shot_id)


def ensure_shot_layout(shot_id: str) -> list[Path]:
    """Create empty `{kind}/approved/` folders for a shot (idempotent)."""
    created: list[Path] = []
    root = shot_root(shot_id)
    for kind in SHOT_KINDS_WITH_APPROVED:
        approved = root / kind / APPROVED_DIRNAME
        if not approved.is_dir():
            approved.mkdir(parents=True, exist_ok=True)
            created.append(approved)
    return created


def ensure_all_shot_layouts(*, include_unsorted: bool = False) -> dict[str, int]:
    """Ensure approved/ folders exist under every shots/S### directory."""
    counts = {"shots": 0, "dirs_created": 0}
    if not SHOTS.is_dir():
        return counts
    for shot_dir in sorted(SHOTS.iterdir()):
        if not shot_dir.is_dir():
            continue
        name = shot_dir.name.upper()
        if not name.startswith("S"):
            continue
        if name == "_UNSORTED" and not include_unsorted:
            continue
        created = ensure_shot_layout(name)
        counts["shots"] += 1
        counts["dirs_created"] += len(created)
    return counts


def still_wip_dir(shot_id: str, model_slug: str) -> Path:
    return shot_root(shot_id) / "still" / "wip" / normalize_model_slug(model_slug)


def still_approved_dir(shot_id: str) -> Path:
    return shot_root(shot_id) / "still" / APPROVED_DIRNAME


def still_approved_path(shot_id: str, filename: str) -> Path:
    """Path inside still/approved/ — keeps the WIP filename on promote."""
    return still_approved_dir(shot_id) / filename


def voice_wip_dir(shot_id: str, model_slug: str = "qwen") -> Path:
    return shot_root(shot_id) / "voice" / "wip" / normalize_model_slug(model_slug)


def voice_approved_dir(shot_id: str) -> Path:
    return shot_root(shot_id) / "voice" / "approved"


def video_wip_dir(shot_id: str, model_slug: str) -> Path:
    return shot_root(shot_id) / "video" / "wip" / normalize_model_slug(model_slug)


def video_approved_dir(shot_id: str) -> Path:
    return shot_root(shot_id) / "video" / APPROVED_DIRNAME


def video_approved_path(shot_id: str, filename: str) -> Path:
    return video_approved_dir(shot_id) / filename


def lipsync_wip_dir(shot_id: str, model_slug: str) -> Path:
    return shot_root(shot_id) / "lipsync" / "wip" / normalize_model_slug(model_slug)


def lipsync_approved_dir(shot_id: str) -> Path:
    return shot_root(shot_id) / "lipsync" / APPROVED_DIRNAME


def lipsync_approved_path(shot_id: str, filename: str) -> Path:
    return lipsync_approved_dir(shot_id) / filename


def normalize_model_slug(slug: str) -> str:
    s = slug.strip().lower()
    for suffix, folder in STILL_MODEL_SUFFIXES:
        if s == suffix or s == folder:
            return folder
    return s.replace("_", "-")


def still_wip_path(
    shot_id: str,
    model_slug: str,
    timestamp: str,
    ext: str,
    *,
    variant: str = "",
) -> Path:
    ext = ext if ext.startswith(".") else f".{ext}"
    fname = f"{variant}_{timestamp}{ext}" if variant else f"{timestamp}{ext}"
    return still_wip_dir(shot_id, model_slug) / fname


def video_wip_path(
    shot_id: str,
    model_slug: str,
    timestamp: str,
    ext: str = ".mp4",
    *,
    tag: str = "",
) -> Path:
    ext = ext if ext.startswith(".") else f".{ext}"
    fname = f"{tag}_{timestamp}{ext}" if tag else f"{timestamp}{ext}"
    return video_wip_dir(shot_id, model_slug) / fname


def lipsync_wip_path(
    shot_id: str,
    model_slug: str,
    timestamp: str,
    ext: str = ".mp4",
    *,
    tag: str = "",
) -> Path:
    ext = ext if ext.startswith(".") else f".{ext}"
    fname = f"{tag}_{timestamp}{ext}" if tag else f"{timestamp}{ext}"
    return lipsync_wip_dir(shot_id, model_slug) / fname


def sfx_wip_dir(shot_id: str, vendor: str) -> Path:
    return shot_root(shot_id) / "sfx" / "wip" / vendor.strip().lower().replace("_", "-")


def sfx_wip_path(
    shot_id: str,
    vendor: str,
    timestamp: str,
    ext: str,
    *,
    tag: str = "",
) -> Path:
    ext = ext if ext.startswith(".") else f".{ext}"
    fname = f"{tag}_{timestamp}{ext}" if tag else f"{timestamp}{ext}"
    return sfx_wip_dir(shot_id, vendor) / fname


def bgm_wip_dir(vendor: str = "minimax") -> Path:
    return AUDIO / "bgm" / "wip" / vendor.strip().lower().replace("_", "-")


def bgm_wip_path(vendor: str, timestamp: str, ext: str, *, tag: str = "") -> Path:
    ext = ext if ext.startswith(".") else f".{ext}"
    fname = f"{tag}_{timestamp}{ext}" if tag else f"{timestamp}{ext}"
    return bgm_wip_dir(vendor) / fname


def bgm_approved_dir() -> Path:
    return AUDIO / "bgm" / APPROVED_DIRNAME


def bgm_approved_path(filename: str) -> Path:
    return bgm_approved_dir() / filename


def parse_sfx_tag(name: str, timestamp: str) -> str:
    """Short stem before timestamp (e.g. 01_ambient from cassette stem names)."""
    stem = Path(name).stem
    if timestamp in stem:
        tag = stem.replace(timestamp, "").strip("_-")
    else:
        tag = stem
    tag = re.sub(r"^s\d{3}[a-z]?_", "", tag, flags=re.I)
    return tag[:48] if tag else "stem"


def parse_bgm_vendor(name: str) -> str:
    n = name.lower()
    if "minimax" in n:
        return "minimax"
    if "beatoven" in n:
        return "beatoven"
    return "minimax"


def promote_voice_wip(wip: Path, shot_id: str, speaker: str) -> Path:
    dest = voice_approved_path(shot_id, speaker, wip.suffix)
    return promote_file(wip, dest)


def voice_wip_path(
    shot_id: str,
    timestamp: str,
    ext: str,
    *,
    model_slug: str = "qwen",
    tag: str = "",
) -> Path:
    ext = ext if ext.startswith(".") else f".{ext}"
    name = f"{tag}_{timestamp}{ext}" if tag else f"{timestamp}{ext}"
    return voice_wip_dir(shot_id, model_slug) / name


def voice_approved_path(shot_id: str, speaker: str, ext: str = ".wav") -> Path:
    ext = ext if ext.startswith(".") else f".{ext}"
    return voice_approved_dir(shot_id) / f"{speaker.lower()}{ext}"


def ensure_parent(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def promote_file(src: Path, dest: Path) -> Path:
    """Copy src to dest (overwrite). Keeps src in place."""
    ensure_parent(dest)
    shutil.copy2(src, dest)
    return dest


def promote_to_approved(src: Path, shot_id: str, kind: str) -> Path:
    """Copy WIP file into {kind}/approved/ keeping its filename."""
    dest_map = {
        "still": still_approved_path(shot_id, src.name),
        "video": video_approved_path(shot_id, src.name),
        "lipsync": lipsync_approved_path(shot_id, src.name),
    }
    if kind not in dest_map:
        raise ValueError(f"promote_to_approved does not support kind={kind!r}")
    return promote_file(src, dest_map[kind])


@dataclass(frozen=True)
class ParsedStillName:
    shot_id: str
    model_slug: str
    variant: str
    timestamp: str
    ext: str


@dataclass(frozen=True)
class ParsedMediaName:
    shot_id: str
    model_slug: str
    timestamp: str
    ext: str


def parse_still_filename(name: str) -> ParsedStillName | None:
    """Parse legacy Tests/S###_{variant?}{model}_{ts}.png names."""
    m = re.match(
        r"^(S\d{3}[A-Z]?)(?:_(.+))?_(\d{8})[_T](\d{6})Z?(\.[^.]+)$",
        name,
        re.I,
    )
    if not m:
        return None
    shot_id = m.group(1).upper()
    middle = m.group(2) or ""
    timestamp = f"{m.group(3)}_{m.group(4)}"
    ext = m.group(4)

    model_slug = "unknown"
    variant = middle
    for suffix, folder in STILL_MODEL_SUFFIXES:
        if middle == suffix or middle.endswith(f"_{suffix}"):
            model_slug = folder
            variant = middle[: -len(suffix)].rstrip("_") if middle != suffix else ""
            break

    if model_slug == "unknown" and middle:
        model_slug = middle.split("_")[-1] if "_" in middle else middle

    return ParsedStillName(shot_id, model_slug, variant, timestamp, ext)


def wip_still_dest(parsed: ParsedStillName) -> Path:
    fname = f"{parsed.timestamp}{parsed.ext}"
    if parsed.variant:
        fname = f"{parsed.variant}_{parsed.timestamp}{parsed.ext}"
    return still_wip_dir(parsed.shot_id, parsed.model_slug) / fname


def parse_video_model(name: str) -> str:
    for pattern, slug in VIDEO_MODEL_PATTERNS:
        if pattern.search(name):
            return slug
    return "unknown"


def parse_lipsync_model(name: str) -> str:
    for pattern, slug in LIPSYNC_MODEL_PATTERNS:
        if pattern.search(name):
            return slug
    return "pixverse"


def parse_media_timestamp(name: str) -> str | None:
    m = TIMESTAMP_RE.search(name)
    if not m:
        return None
    return f"{m.group(1)}_{m.group(2)}"


def parse_shot_from_name(name: str) -> str | None:
    m = SHOT_PREFIX_RE.match(name)
    return m.group(1).upper() if m else None


def parse_voice_speaker(name: str) -> str:
    m = VOICE_SPEAKER_RE.search(name)
    if m:
        return m.group(1).lower()
    stem = Path(name).stem.lower()
    if stem.startswith("s") and len(stem) > 4:
        rest = stem.split("_", 2)
        if len(rest) >= 2:
            return rest[1][:32]
    return Path(name).stem.lower()[:32]


def _latest_file(paths: list[Path]) -> Path | None:
    hits = [p for p in paths if p.is_file()]
    if not hits:
        return None
    return max(hits, key=lambda p: p.stat().st_mtime)


def _approved_dir_for(shot_id: str | None, kind: str) -> Path:
    if kind == "bgm":
        return bgm_approved_dir()
    if shot_id is None:
        raise ValueError(f"shot_id required for kind={kind!r}")
    return shot_root(shot_id) / kind / APPROVED_DIRNAME


def _list_approved_media(
    shot_id: str | None,
    kind: str,
    extensions: tuple[str, ...] | None = None,
) -> list[Path]:
    exts = extensions or MEDIA_EXTENSIONS.get(kind, ())
    root = _approved_dir_for(shot_id, kind)
    if not root.is_dir():
        return []
    ext_set = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in exts}
    return sorted(
        (p for p in root.iterdir() if p.is_file() and p.suffix.lower() in ext_set),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def _legacy_flat_approved(shot_id: str, kind: str) -> Path | None:
    legacy_name = LEGACY_FLAT_APPROVED.get(kind)
    if not legacy_name:
        return None
    flat = shot_root(shot_id) / kind / legacy_name
    return flat if flat.is_file() else None


def _legacy_flat_bgm() -> Path | None:
    flat = AUDIO / "bgm" / LEGACY_FLAT_BGM
    return flat if flat.is_file() else None


def _latest_approved_media(shot_id: str, kind: str) -> Path | None:
    hits = _list_approved_media(shot_id, kind)
    if hits:
        return hits[0]
    return _legacy_flat_approved(shot_id, kind)


def approved_filename_for(src: Path, *, kind: str = "") -> str:
    """Pick a stable name when promoting or migrating into approved/."""
    if src.name not in LEGACY_FLAT_APPROVED.values() and src.name != LEGACY_FLAT_BGM:
        return src.name
    ts = parse_media_timestamp(src.name)
    if not ts:
        ts = datetime.fromtimestamp(src.stat().st_mtime, tz=timezone.utc).strftime(TIMESTAMP_FMT)
    return f"{ts}{src.suffix.lower()}"


def migrate_flat_approved_files(*, dry_run: bool = False) -> dict[str, int]:
    """Move legacy still/approved.png (etc.) into still/approved/{timestamp}.ext folders."""
    counts: dict[str, int] = {}

    if not SHOTS.is_dir():
        return counts

    for shot_dir in sorted(SHOTS.iterdir()):
        if not shot_dir.is_dir() or not shot_dir.name.upper().startswith("S"):
            continue
        shot_id = shot_dir.name.upper()
        for kind in ("still", "video", "lipsync"):
            legacy_name = LEGACY_FLAT_APPROVED[kind]
            flat = shot_dir / kind / legacy_name
            if not flat.is_file():
                continue
            dest = _approved_dir_for(shot_id, kind) / approved_filename_for(flat, kind=kind)
            if dest.is_file():
                if not dry_run:
                    flat.unlink()
                counts[f"{kind}_flat_removed"] = counts.get(f"{kind}_flat_removed", 0) + 1
                continue
            if dry_run:
                print(f"  move {flat.relative_to(ROOT)} -> {dest.relative_to(ROOT)}")
            else:
                ensure_parent(dest)
                shutil.move(str(flat), str(dest))
            counts[f"{kind}_migrated"] = counts.get(f"{kind}_migrated", 0) + 1

    flat_bgm = AUDIO / "bgm" / LEGACY_FLAT_BGM
    if flat_bgm.is_file():
        dest = bgm_approved_dir() / approved_filename_for(flat_bgm, kind="bgm")
        if not dest.is_file():
            if dry_run:
                print(f"  move {flat_bgm.relative_to(ROOT)} -> {dest.relative_to(ROOT)}")
            else:
                ensure_parent(dest)
                shutil.move(str(flat_bgm), str(dest))
            counts["bgm_migrated"] = counts.get("bgm_migrated", 0) + 1
        elif not dry_run:
            flat_bgm.unlink()
            counts["bgm_flat_removed"] = counts.get("bgm_flat_removed", 0) + 1

    return counts


def _legacy_still_wip(shot_id: str) -> Path | None:
    sid = normalize_shot_id(shot_id)
    tests = ROOT / "Tests"
    if not tests.is_dir():
        return None
    candidates = [
        p
        for p in tests.glob(f"{sid}_*")
        if p.is_file() and "Final" not in p.parts and p.suffix.lower() in (".png", ".jpg", ".webp")
    ]
    return _latest_file(candidates)


def _legacy_still_final(shot_id: str) -> Path | None:
    sid = normalize_shot_id(shot_id)
    final_dir = ROOT / "Tests" / "Final"
    if not final_dir.is_dir():
        return None
    return _latest_file(list(final_dir.glob(f"{sid}_*")))


def hero_still(shot_id: str) -> Path | None:
    hit = _latest_approved_media(shot_id, "still")
    if hit is not None:
        return hit
    return _legacy_still_final(shot_id)


def resolve_still(shot_id: str, legacy: Path | None = None) -> Path:
    """Approved hero still, else legacy path if it exists, else legacy path for argparse default."""
    hit = hero_still(shot_id)
    if hit is not None:
        return hit
    if legacy is not None and legacy.is_file():
        return legacy
    if legacy is not None:
        return legacy
    raise FileNotFoundError(f"No still for {shot_id}; run Stage 4 or pass --start-image")


def _list_wip_media(
    shot_id: str,
    kind: str,
    extensions: tuple[str, ...] = (".mp4", ".webm", ".mov", ".wav", ".mp3", ".png", ".jpg", ".webp"),
) -> list[Path]:
    wip = shot_root(shot_id) / kind / "wip"
    if not wip.is_dir():
        return []
    exts = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in extensions}
    return sorted(
        (p for p in wip.rglob("*") if p.is_file() and p.suffix.lower() in exts),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def _latest_wip_media(shot_id: str, kind: str, extensions: tuple[str, ...]) -> Path | None:
    hits = _list_wip_media(shot_id, kind, extensions)
    return hits[0] if hits else None


def hero_video(shot_id: str) -> Path | None:
    hit = _latest_approved_media(shot_id, "video")
    if hit is not None:
        return hit
    wip = _latest_wip_media(shot_id, "video", (".mp4", ".webm", ".mov"))
    if wip is not None:
        return wip
    sid = normalize_shot_id(shot_id)
    skip = ("lipsync", "dialogue", "compare", "qwen", "pixverse", "musetalk")
    candidates: list[Path] = []
    for root in (ROOT / "outputs" / "video" / "final", ROOT / "outputs" / "video"):
        if not root.is_dir():
            continue
        for p in root.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in (".mp4", ".webm", ".mov"):
                continue
            if sid not in p.name.upper():
                continue
            if any(s in p.name.lower() for s in skip):
                continue
            candidates.append(p)
    return _latest_file(candidates)


def hero_lipsync(shot_id: str) -> Path | None:
    hit = _latest_approved_media(shot_id, "lipsync")
    if hit is not None:
        return hit
    wip = _latest_wip_media(shot_id, "lipsync", (".mp4", ".webm", ".mov"))
    if wip is not None:
        return wip
    sid = normalize_shot_id(shot_id)
    lipsync_dir = ROOT / "outputs" / "video" / "LipsyncTests"
    if not lipsync_dir.is_dir():
        return None
    candidates = [
        p
        for p in lipsync_dir.iterdir()
        if p.is_file() and sid in p.name.upper() and p.suffix.lower() in (".mp4", ".webm", ".mov")
    ]
    final_va = ROOT / "outputs" / "video" / "final" / "Voice Added"
    if final_va.is_dir():
        candidates.extend(
            p
            for p in final_va.iterdir()
            if p.is_file() and sid in p.name.upper() and p.suffix.lower() in (".mp4", ".webm", ".mov")
        )
    return _latest_file(candidates)


def hero_voice(shot_id: str) -> Path | None:
    approved_dir = voice_approved_dir(shot_id)
    if approved_dir.is_dir():
        wavs = sorted(approved_dir.glob("*.wav"), key=lambda p: p.stat().st_mtime, reverse=True)
        if wavs:
            return wavs[0]
        mp3s = sorted(approved_dir.glob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
        if mp3s:
            return mp3s[0]
    wip = _latest_wip_media(shot_id, "voice", (".wav", ".mp3"))
    if wip is not None:
        return wip
    sid = normalize_shot_id(shot_id)
    for vd in (ROOT / "outputs" / "voice" / "final" / sid, ROOT / "outputs" / "voice" / sid):
        if not vd.is_dir():
            continue
        hits = sorted(vd.rglob("*.wav"), key=lambda p: p.stat().st_mtime, reverse=True)
        if hits:
            return hits[0]
        hits = sorted(vd.rglob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
        if hits:
            return hits[0]
    return None


def list_still_wip(shot_id: str) -> list[Path]:
    return _list_wip_media(shot_id, "still", (".png", ".jpg", ".jpeg", ".webp"))


def has_approved_artifact(shot_id: str, kind: str) -> bool:
    """True when `{kind}/approved/` has at least one media file."""
    if kind == "bgm":
        return bool(_list_approved_media(None, "bgm"))
    exts = MEDIA_EXTENSIONS.get(kind, ())
    return bool(_list_approved_media(shot_id, kind, exts))


def has_wip_artifact(shot_id: str, kind: str) -> bool:
    """True when `{kind}/wip/` has at least one media file."""
    exts = MEDIA_EXTENSIONS.get(kind, ())
    if kind == "still":
        exts = (".png", ".jpg", ".jpeg", ".webp")
    return _latest_wip_media(shot_id, kind, exts) is not None


def needs_promote(shot_id: str, kind: str) -> bool:
    """WIP on disk but nothing approved yet — user should run promote_artifact."""
    return has_wip_artifact(shot_id, kind) and not has_approved_artifact(shot_id, kind)


def scan_shot_artifacts(shot_id: str) -> dict[str, tuple[bool, str]]:
    """Return pipeline flags + paths (new layout first, legacy fallback)."""
    from panel_paths import PANELS_ENG

    sid_lower = normalize_shot_id(shot_id).lower()
    panel = PANELS_ENG / f"panel_{sid_lower}.png"

    still_wip = list_still_wip(shot_id)
    still_wip_path_hit = still_wip[0] if still_wip else _legacy_still_wip(shot_id)
    approved_still = hero_still(shot_id)
    voice_path = hero_voice(shot_id)
    video_path = hero_video(shot_id)
    lipsync_path = hero_lipsync(shot_id)

    return {
        "panel": (panel.is_file(), str(panel) if panel.is_file() else ""),
        "still": (still_wip_path_hit is not None, str(still_wip_path_hit) if still_wip_path_hit else ""),
        "final": (approved_still is not None, str(approved_still) if approved_still else ""),
        "voice": (voice_path is not None, str(voice_path) if voice_path else ""),
        "video": (video_path is not None, str(video_path) if video_path else ""),
        "lipsync": (lipsync_path is not None, str(lipsync_path) if lipsync_path else ""),
    }
