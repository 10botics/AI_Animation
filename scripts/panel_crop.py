"""Manga panel crop helpers for the beginner dashboard."""

from __future__ import annotations

import re
from pathlib import Path

from PIL import Image

from panel_paths import PANELS_ENG

PAGE_FILE_RE = re.compile(r"(\d{3}\.jpg)", re.I)


def panel_eng_path(shot_id: str) -> Path:
    sid = shot_id.lower()
    return PANELS_ENG / f"panel_{sid}.png"


def normalize_page_filename(page_field: str) -> str | None:
    if not page_field:
        return None
    match = PAGE_FILE_RE.search(page_field.strip())
    return match.group(1).lower() if match else None


def resolve_chapter_page(chapter_dir: Path, page_field: str) -> Path | None:
    name = normalize_page_filename(page_field)
    if not name:
        return None
    stem = name[:-4]
    for candidate in (
        chapter_dir / name,
        chapter_dir / f"{stem}.JPG",
        chapter_dir / f"{stem}.jpeg",
        chapter_dir / f"{stem}.JPEG",
    ):
        if candidate.is_file():
            return candidate
    return None


def save_panel_crop(shot_id: str, image: Image.Image) -> Path:
    PANELS_ENG.mkdir(parents=True, exist_ok=True)
    out = panel_eng_path(shot_id)
    image.convert("RGB").save(out, format="PNG")
    return out
