"""
Discover comic chapter folders for the pipeline and dashboard.

A folder is a chapter when it contains stage_02_shot_list.md. Discovery scans the
whole project tree (Comic Source/, legacy root Chapter-*/, mentor test packs, etc.)
while skipping virtualenv and build folders.

Primary layout:
  Comic Source/Chapter-81/stage_02_shot_list.md
"""

from __future__ import annotations

import functools
from pathlib import Path

from fal_common import ROOT

COMIC_SOURCE_DIR = ROOT / "Comic Source"
STAGE2_SHOT_LIST = "stage_02_shot_list.md"

# Skip these directory names when walking the repo for stage_02 files.
_EXCLUDE_DIR_NAMES = frozenset(
    {".venv", ".git", "node_modules", "__pycache__", "dist", ".cursor", ".streamlit"}
)

# Legacy chapter folder name patterns at repo root (still scanned via rglob).
ROOT_CHAPTER_GLOBS = (
    "Chapter-*",
    "chapter-*",
    "Frierien-chapter*",
    "ch[0-9][0-9][0-9]",
)


def is_chapter_dir(path: Path) -> bool:
    return path.is_dir() and (path / STAGE2_SHOT_LIST).is_file()


def chapter_display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def chapter_key(path: Path) -> str:
    """Stable id for URLs and session state (relative path from repo root)."""
    return chapter_display_path(path)


def _should_skip_path(path: Path) -> bool:
    return any(part in _EXCLUDE_DIR_NAMES for part in path.parts)


def _walk_chapter_dirs() -> list[Path]:
    """Uncached discovery — prefer Comic Source, then legacy root patterns, then rglob fallback."""
    seen: set[Path] = set()
    chapters: list[Path] = []

    def _add(path: Path) -> None:
        resolved = path.resolve()
        if not is_chapter_dir(resolved) or _should_skip_path(resolved):
            return
        if resolved in seen:
            return
        seen.add(resolved)
        chapters.append(resolved)

    if COMIC_SOURCE_DIR.is_dir():
        for child in sorted(COMIC_SOURCE_DIR.iterdir()):
            if child.is_dir():
                _add(child)

    if ROOT.is_dir():
        for pattern in ROOT_CHAPTER_GLOBS:
            for hit in ROOT.glob(pattern):
                if hit.is_dir():
                    _add(hit)

    if chapters:
        return sorted(chapters, key=lambda p: chapter_key(p).lower())

    for hit in ROOT.rglob(STAGE2_SHOT_LIST):
        parent = hit.parent.resolve()
        if _should_skip_path(parent):
            continue
        if parent in seen:
            continue
        seen.add(parent)
        chapters.append(parent)

    return sorted(chapters, key=lambda p: chapter_key(p).lower())


@functools.lru_cache(maxsize=1)
def _discover_chapter_dirs_cached() -> tuple[str, ...]:
    return tuple(str(p) for p in _walk_chapter_dirs())


def clear_chapter_discovery_cache() -> None:
    _discover_chapter_dirs_cached.cache_clear()


def discover_chapter_dirs(*, refresh: bool = False) -> list[Path]:
    """All chapter folders with stage_02, sorted by path (cached until refresh)."""
    if refresh:
        clear_chapter_discovery_cache()
    return [Path(p) for p in _discover_chapter_dirs_cached()]


def _name_matches(chapters: list[Path], name: str) -> list[Path]:
    key = name.strip().lower()
    if not key:
        return []
    return [path for path in chapters if path.name.lower() == key]


def find_chapter_by_key(key: str) -> Path | None:
    ref = key.strip().replace("\\", "/").strip("/")
    if not ref:
        return None
    ref_lower = ref.lower()
    for path in discover_chapter_dirs():
        if chapter_key(path).lower() == ref_lower:
            return path
    return None


def find_chapter_by_name(name: str) -> Path | None:
    """Match folder basename; prefer Comic Source/ when names collide."""
    matches = _name_matches(discover_chapter_dirs(), name)
    if not matches:
        return None
    if len(matches) == 1:
        return matches[0]
    for path in matches:
        try:
            path.relative_to(COMIC_SOURCE_DIR)
            return path
        except ValueError:
            continue
    return matches[0]


def resolve_chapter_ref(ref: str) -> Path | None:
    """Resolve a chapter from a relative path key or folder basename."""
    ref = ref.strip()
    if not ref:
        return None
    hit = find_chapter_by_key(ref)
    if hit is not None:
        return hit
    return find_chapter_by_name(ref)


def chapter_select_label(path: Path, chapters: list[Path] | None = None) -> str:
    """Short label when unique; full path when the same name appears in multiple places."""
    all_chapters = chapters if chapters is not None else discover_chapter_dirs()
    same_name = sum(1 for c in all_chapters if c.name.lower() == path.name.lower())
    if same_name > 1:
        return chapter_key(path)
    return path.name


def chapter_url_value(path: Path, chapters: list[Path] | None = None) -> str:
    """URL query value: basename when unique, else relative path."""
    all_chapters = chapters if chapters is not None else discover_chapter_dirs()
    same_name = sum(1 for c in all_chapters if c.name.lower() == path.name.lower())
    if same_name > 1:
        return chapter_key(path)
    return path.name


def find_chapter_dir(*, preferred_name: str = "") -> Path | None:
    """Default chapter: preferred ref if set, else the first discovered folder."""
    if preferred_name:
        hit = resolve_chapter_ref(preferred_name)
        if hit is not None:
            return hit
    chapters = discover_chapter_dirs()
    return chapters[0] if chapters else None
