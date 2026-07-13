"""
Rename legacy timestamps: 20260527_054046 -> 20260527_054046

Updates filenames and text file contents (JSON logs, docs, skills).

Usage:
  python rename_timestamps.py --dry-run
  python rename_timestamps.py
  python rename_timestamps.py --filenames-only
  python rename_timestamps.py --content-only
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from fal_common import ROOT

OLD_TS = re.compile(r"(\d{8})T(\d{6})Z")
NEW_TS = r"\1_\2"

SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules"}
BINARY_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".ico",
    ".mp4", ".webm", ".mov", ".avi", ".mkv",
    ".wav", ".mp3", ".flac", ".ogg", ".m4a",
    ".zip", ".pdf", ".pyc", ".exe", ".dll", ".so",
}


def new_filename(name: str) -> str | None:
    if not OLD_TS.search(name):
        return None
    return OLD_TS.sub(NEW_TS, name)


def collect_renames(root: Path) -> list[tuple[Path, Path]]:
    pairs: list[tuple[Path, Path]] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        new_name = new_filename(path.name)
        if not new_name or new_name == path.name:
            continue
        dest = path.with_name(new_name)
        pairs.append((path, dest))
    # deepest paths first so parent renames do not break walks
    pairs.sort(key=lambda p: len(str(p[0])), reverse=True)
    return pairs


def collect_content_updates(root: Path) -> list[tuple[Path, str]]:
    updates: list[tuple[Path, str]] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in BINARY_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if not OLD_TS.search(text):
            continue
        updates.append((path, OLD_TS.sub(NEW_TS, text)))
    return updates


def main() -> int:
    parser = argparse.ArgumentParser(description="Rename T/Z timestamps in filenames and text")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--filenames-only", action="store_true")
    parser.add_argument("--content-only", action="store_true")
    args = parser.parse_args()

    do_filenames = not args.content_only
    do_content = not args.filenames_only

    renamed = 0
    skipped = 0
    if do_filenames:
        pairs = collect_renames(ROOT)
        for src, dest in pairs:
            if dest.exists() and dest != src:
                print(f"  skip (exists): {dest.relative_to(ROOT)}", file=sys.stderr)
                skipped += 1
                continue
            if args.dry_run:
                print(f"  {src.relative_to(ROOT)} -> {dest.name}")
            else:
                src.rename(dest)
            renamed += 1
        label = "Would rename" if args.dry_run else "Renamed"
        print(f"\n{label} filenames: {renamed}, skipped: {skipped}")

    content_updated = 0
    if do_content:
        updates = collect_content_updates(ROOT)
        for path, new_text in updates:
            if args.dry_run:
                print(f"  content: {path.relative_to(ROOT)}")
            else:
                path.write_text(new_text, encoding="utf-8", newline="\n")
            content_updated += 1
        label = "Would update" if args.dry_run else "Updated"
        print(f"\n{label} file contents: {content_updated}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
