"""Shared ffmpeg mux helpers for shot dialogue overlays."""

from __future__ import annotations

import subprocess
from pathlib import Path

from fal_common import ROOT


def probe_duration(path: Path) -> float:
    r = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(r.stdout.strip())


def latest_shot_video(shot_id: str, *, exclude_fragments: tuple[str, ...] = ()) -> Path:
    """Latest Kling MP4 for a shot, excluding dialogue/compare variants."""
    sid = shot_id.upper()
    defaults = ("_dialogue_", "_frieren_dialogue_", "_fern_dialogue_", "compare_", "_qwen_")
    skip = set(defaults + exclude_fragments)
    candidates: list[Path] = []
    for d in (ROOT / "outputs" / "video" / "final", ROOT / "outputs" / "video"):
        if not d.is_dir():
            continue
        for p in d.glob(f"{sid}_kling*.mp4"):
            if any(s in p.name for s in skip):
                continue
            candidates.append(p)
    if not candidates:
        raise FileNotFoundError(f"No {sid} Kling MP4 (non-dialogue) under outputs/video/")
    return max(candidates, key=lambda p: p.stat().st_mtime)


def mix_dialogue_stems(
    stems: list[tuple[Path, float]],
    out: Path,
    *,
    total_dur: float | None = None,
) -> Path:
    """Mix dialogue WAV/MP3 stems on one timeline (no video). For lip-sync / preview beds."""
    if not stems:
        raise ValueError("mix_dialogue_stems: no stems")
    end = max(probe_duration(wav) + start for wav, start in stems)
    dur = total_dur if total_dur is not None else end + 0.25
    out.parent.mkdir(parents=True, exist_ok=True)
    inputs: list[str] = []
    filters: list[str] = []
    mix_inputs: list[str] = []
    for i, (wav, start) in enumerate(stems):
        inputs.extend(["-i", str(wav)])
        ms = int(start * 1000)
        filters.append(f"[{i}:a]adelay={ms}|{ms},apad=whole_dur={dur:.3f}[d{i}]")
        mix_inputs.append(f"[d{i}]")
    n = len(mix_inputs)
    filters.append(f"{''.join(mix_inputs)}amix=inputs={n}:duration=longest:dropout_transition=0[aout]")
    cmd = [
        "ffmpeg",
        "-y",
        *inputs,
        "-filter_complex",
        ";".join(filters),
        "-map",
        "[aout]",
        "-t",
        f"{dur:.3f}",
        "-c:a",
        "pcm_s16le",
        str(out.with_suffix(".wav") if out.suffix.lower() != ".wav" else out),
    ]
    dest = out if out.suffix.lower() == ".wav" else out.with_suffix(".wav")
    cmd[-1] = str(dest)
    print(f"Timeline mix: {dest.name}", flush=True)
    subprocess.run(cmd, check=True)
    return dest


def mux_dialogue(video: Path, stems: list[tuple[Path, float]], out: Path, duck: float) -> None:
    dur = probe_duration(video)
    inputs = ["-i", str(video)]
    filters: list[str] = []
    mix_inputs: list[str] = []
    for i, (wav, start) in enumerate(stems):
        inputs.extend(["-i", str(wav)])
        idx = i + 1
        ms = int(start * 1000)
        filters.append(f"[{idx}:a]adelay={ms}|{ms},apad=whole_dur={dur}[d{i}]")
        mix_inputs.append(f"[d{i}]")
    filters.append(f"[0:a]volume={duck}[bg]")
    mix_inputs.insert(0, "[bg]")
    n = len(mix_inputs)
    filters.append(f"{''.join(mix_inputs)}amix=inputs={n}:duration=first:dropout_transition=0[aout]")
    cmd = [
        "ffmpeg",
        "-y",
        *inputs,
        "-filter_complex",
        ";".join(filters),
        "-map",
        "0:v",
        "-map",
        "[aout]",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        str(out),
    ]
    print(f"Mux: {out.name}", flush=True)
    subprocess.run(cmd, check=True)
