"""Lip-sync run metadata — kept out of video output folders."""

from __future__ import annotations

import json
from pathlib import Path

from fal_common import ROOT

LIPSYNC_META_DIR = ROOT / "outputs" / "video" / "meta" / "lipsync"


def lipsync_meta_path(video_out: Path) -> Path:
    """JSON path keyed to the output MP4 stem (not beside the video file)."""
    LIPSYNC_META_DIR.mkdir(parents=True, exist_ok=True)
    return LIPSYNC_META_DIR / f"{video_out.stem}.json"


def write_lipsync_meta(video_out: Path, payload: dict) -> Path:
    path = lipsync_meta_path(video_out)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path
