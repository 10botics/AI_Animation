"""
Scan AI_Animation project folders and report per-shot pipeline progress.

Used by the beginner Streamlit dashboard (and future pro Canvas board).
Read-only — no Fal calls.

Usage:
  python pipeline_status.py
  python pipeline_status.py --json
  python pipeline_status.py --shot S006
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from fal_common import ROOT
from artifact_paths import needs_promote, scan_shot_artifacts

CHAPTER_CANDIDATES = (
    ROOT / "Chapter-81",
    ROOT / "Frierien-chapter081",
)

SHOT_ROW_RE = re.compile(
    r"^\|\s*\*\*(S\d{3}[A-Z]?)\*\*\s*\|\s*`?([^`|]+)`?\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|",
    re.MULTILINE,
)
PAGE_HEADER_RE = re.compile(
    r"^###\s+Page\s+\d+\s+—\s+`(\d{3}\.jpg)`",
    re.MULTILINE,
)
STEP_LABELS = ("panel", "still", "final", "voice", "video", "lipsync")
STEP_LABELS_SILENT = ("panel", "still", "final", "video")


@dataclass
class ShotStatus:
    shot_id: str
    page: str = ""
    layer: str = ""
    framing: str = ""
    beat: str = ""
    summary: str = ""
    panel: bool = False
    panel_path: str = ""
    still: bool = False
    still_path: str = ""
    final: bool = False
    final_path: str = ""
    voice: bool = False
    voice_path: str = ""
    video: bool = False
    video_path: str = ""
    lipsync: bool = False
    lipsync_path: str = ""
    has_ref_edit_script: bool = False
    has_dialogue: bool = True
    next_step: str = ""
    steps_done: int = 0
    steps_total: int = len(STEP_LABELS)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ChapterProgress:
    chapter_dir: str
    shots: list[ShotStatus] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.shots)

    def count_with(self, attr: str) -> int:
        return sum(1 for s in self.shots if getattr(s, attr))

    def to_dict(self) -> dict:
        return {
            "chapter_dir": self.chapter_dir,
            "total_shots": self.total,
            "with_final": self.count_with("final"),
            "with_video": self.count_with("video"),
            "shots": [s.to_dict() for s in self.shots],
        }


def find_chapter_dir() -> Path | None:
    for candidate in CHAPTER_CANDIDATES:
        stage = candidate / "stage_02_shot_list.md"
        if stage.is_file():
            return candidate
    return None


def _scan_artifacts(shot_id: str) -> dict[str, tuple[bool, str]]:
    return scan_shot_artifacts(shot_id)


def _next_step(shot_id: str, flags: dict[str, bool], has_script: bool, *, has_dialogue: bool) -> str:
    if not flags["panel"]:
        return "panel"
    if not flags["still"] and not flags["final"]:
        return "picture"
    if not flags["final"]:
        return "final"
    if has_dialogue:
        if not flags["voice"]:
            return "voice"
        if needs_promote(shot_id, "voice"):
            return "voice"
    if not flags["video"]:
        return "video"
    if needs_promote(shot_id, "video"):
        return "video"
    if has_dialogue:
        if not flags["lipsync"]:
            return "lipsync"
        if needs_promote(shot_id, "lipsync"):
            return "lipsync"
    return "done"


def _steps_for_shot(flags: dict[str, bool], has_dialogue: bool) -> tuple[int, int]:
    """Return (steps_done, steps_total) for tracked pipeline slots."""
    keys = STEP_LABELS if has_dialogue else STEP_LABELS_SILENT
    done = sum(1 for k in keys if flags[k])
    return done, len(keys)


def parse_stage_02(chapter_dir: Path) -> list[dict[str, str]]:
    text = (chapter_dir / "stage_02_shot_list.md").read_text(encoding="utf-8")
    page_map: dict[int, str] = {}
    for m in PAGE_HEADER_RE.finditer(text):
        page_map[m.start()] = m.group(1)

    page_starts = sorted(page_map.keys())
    rows: list[dict[str, str]] = []

    for m in SHOT_ROW_RE.finditer(text):
        pos = m.start()
        page = ""
        for start in reversed(page_starts):
            if start <= pos:
                page = page_map[start]
                break
        rows.append(
            {
                "shot_id": m.group(1).upper(),
                "layer": m.group(2).strip().strip("`"),
                "framing": m.group(3).strip(),
                "beat": m.group(4).strip(),
                "summary": m.group(5).strip()[:200],
                "page": page,
            }
        )
    return rows


def build_shot_status(row: dict[str, str], dialogue_map: dict[str, bool] | None = None) -> ShotStatus:
    shot_id = row["shot_id"]
    artifacts = _scan_artifacts(shot_id)
    script = ROOT / "scripts" / f"generate_{shot_id.lower()}_ref_edit.py"
    has_script = script.is_file()

    flags = {k: artifacts[k][0] for k in STEP_LABELS}
    has_dialogue = dialogue_map.get(shot_id, True) if dialogue_map else True
    steps_done, steps_total = _steps_for_shot(flags, has_dialogue)

    status = ShotStatus(
        shot_id=shot_id,
        page=row.get("page", ""),
        layer=row.get("layer", ""),
        framing=row.get("framing", ""),
        beat=row.get("beat", ""),
        summary=row.get("summary", ""),
        panel=flags["panel"],
        panel_path=artifacts["panel"][1],
        still=flags["still"],
        still_path=artifacts["still"][1],
        final=flags["final"],
        final_path=artifacts["final"][1],
        voice=flags["voice"],
        voice_path=artifacts["voice"][1],
        video=flags["video"],
        video_path=artifacts["video"][1],
        lipsync=flags["lipsync"],
        lipsync_path=artifacts["lipsync"][1],
        has_ref_edit_script=has_script,
        has_dialogue=has_dialogue,
        next_step=_next_step(shot_id, flags, has_script, has_dialogue=has_dialogue),
        steps_done=steps_done,
        steps_total=steps_total,
    )
    return status


def scan_chapter(chapter_dir: Path | None = None) -> ChapterProgress:
    chapter = chapter_dir or find_chapter_dir()
    if chapter is None:
        return ChapterProgress(chapter_dir="", shots=[])

    dialogue_map: dict[str, bool] = {}
    try:
        from ingest_summary import build_dialogue_map

        dialogue_map = build_dialogue_map(chapter)
    except Exception:
        dialogue_map = {}

    rows = parse_stage_02(chapter)
    shots = [build_shot_status(r, dialogue_map) for r in rows]
    return ChapterProgress(chapter_dir=str(chapter), shots=shots)


def cursor_prompt_for_step(
    shot_id: str,
    step: str,
    *,
    still_path: str = "",
    artifact_path: str = "",
    has_dialogue: bool = True,
) -> str:
    """Beginner-friendly Agent prompt — paste into Cursor chat."""
    sid = shot_id.upper()
    sid_lower = sid.lower()
    chapter = find_chapter_dir()
    chapter_name = chapter.name if chapter else "Chapter-81"

    if step == "panel":
        return (
            f"/manga-panel-crop-for-shots\n\n"
            f"Create or fix the panel crop for shot **{sid}** only.\n"
            f"Read @{chapter_name}/stage_02_shot_list.md for framing.\n"
            f"Save to panels/eng/panel_{sid_lower}.png\n"
            f"Do not change other shots."
        )
    if step == "picture":
        return (
            f"/nano-banana-2-prompting\n\n"
            f"Stage 4 still for shot **{sid}** only.\n"
            f"Use panels/eng/panel_{sid_lower}.png as reference.\n"
            f"Run scripts/generate_{sid_lower}_ref_edit.py when the prompt is ready.\n"
            f"WIP saves to shots/{sid}/still/wip/{{model}}/{{timestamp}}.png\n"
            f"After QC: python scripts/promote_artifact.py still {sid} --from shots/{sid}/still/wip/...\n"
            f"Read @{chapter_name}/stage_02_shot_list.md and @{chapter_name}/stage_03_series_bible.md."
        )
    if step == "final":
        wip_line = ""
        if still_path:
            wip_line = f"Latest WIP still: `{still_path}`\n"
        return (
            f"Promote the QC-passed still for shot **{sid}**.\n"
            f"{wip_line}"
            f"Pick the best PNG from `shots/{sid}/still/wip/{{model}}/` after visual QC.\n"
            f"python scripts/promote_artifact.py still {sid} --from shots/{sid}/still/wip/{{model}}/{{timestamp}}.png\n"
            f"Approved path: `shots/{sid}/still/approved/{{timestamp}}.png`\n"
            f"Then continue to {'voice / video' if has_dialogue else 'video (no dialogue on this shot — skip voice and lip-sync)'}."
        )
    if step == "voice":
        if artifact_path and "/wip/" in artifact_path.replace("\\", "/"):
            return (
                f"Promote voice audio for shot **{sid}**.\n"
                f"Latest WIP: `{artifact_path}`\n"
                f"python scripts/promote_artifact.py voice {sid} --from {artifact_path} --speaker {{fern|frieren|stark|denken}}\n"
                f"Approved path: `shots/{sid}/voice/approved/{{speaker}}.wav`"
            )
        return (
            f"Generate dialogue audio for shot **{sid}** only.\n"
            f"Read @{chapter_name}/stage_02_shot_list.md and panels/jap/ for JP balloon text if present.\n"
            f"Use the appropriate dialogue skill (Fern / Frieren / Stark Qwen or MiniMax per shot).\n"
            f"Run the matching scripts/generate_{sid_lower}_*dialogue*.py\n"
            f"WIP: shots/{sid}/voice/wip/qwen/{{speaker}}_{{timestamp}}.wav\n"
            f"Approve: python scripts/promote_artifact.py voice {sid} --from ... --speaker ...\n"
            f"Voice first — measure WAV length before picking video duration."
        )
    if step == "video":
        if artifact_path and "/wip/" in artifact_path.replace("\\", "/"):
            return (
                f"Promote the QC-passed video for shot **{sid}**.\n"
                f"Latest WIP: `{artifact_path}`\n"
                f"python scripts/promote_artifact.py video {sid} --from {artifact_path}\n"
                f"Approved path: `shots/{sid}/video/approved/{{timestamp}}.mp4`"
            )
        return (
            f"/anime-scene-i2v-prompting\n\n"
            f"Stage 5 video for shot **{sid}** only.\n"
            f"Driver still: latest file in shots/{sid}/still/approved/ (or legacy Tests/Final/).\n"
            f"Save WIP to shots/{sid}/video/wip/{{model}}/{{timestamp}}.mp4\n"
            f"After QC: python scripts/promote_artifact.py video {sid} --from shots/{sid}/video/wip/...\n"
            f"Run scripts/generate_{sid_lower}_seedance_i2v.py or generate_{sid_lower}_kling_i2v.py"
            + (
                ""
                if has_dialogue
                else "\nNo dialogue on this shot — ambient motion / SFX only; skip voice and lip-sync."
            )
        )
    if step == "lipsync":
        if artifact_path and "/wip/" in artifact_path.replace("\\", "/"):
            return (
                f"Promote the QC-passed lip-sync clip for shot **{sid}**.\n"
                f"Latest WIP: `{artifact_path}`\n"
                f"python scripts/promote_artifact.py lipsync {sid} --from {artifact_path}\n"
                f"Approved path: `shots/{sid}/lipsync/approved/{{timestamp}}.mp4`"
            )
        return (
            f"/pixverse-lipsync\n\n"
            f"Lip-sync shot **{sid}** only.\n"
            f"Video: latest in shots/{sid}/video/approved/\n"
            f"Audio: shots/{sid}/voice/approved/\n"
            f"Save WIP to shots/{sid}/lipsync/wip/pixverse/\n"
            f"After QC: python scripts/promote_artifact.py lipsync {sid} --from shots/{sid}/lipsync/wip/...\n"
            f"Run scripts/lipsync_fal.py with the approved video + WAV."
        )
    return (
        f"Shot **{sid}** looks complete in the dashboard. "
        f"Review shots/{sid}/ and continue to the next incomplete shot."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan pipeline progress for Chapter shots")
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout")
    parser.add_argument("--shot", type=str, default="", help="Single shot e.g. S006")
    args = parser.parse_args()

    progress = scan_chapter()
    if args.shot:
        sid = args.shot.upper()
        match = [s for s in progress.shots if s.shot_id == sid]
        if not match:
            print(f"Shot not found in stage_02: {sid}", flush=True)
            return 1
        if args.json:
            print(json.dumps(match[0].to_dict(), indent=2))
        else:
            s = match[0]
            print(f"{s.shot_id}  done={s.steps_done}/{s.steps_total}  next={s.next_step}")
        return 0

    if args.json:
        print(json.dumps(progress.to_dict(), indent=2))
        return 0

    if not progress.shots:
        print("No chapter found (need Chapter-81/stage_02_shot_list.md)", flush=True)
        return 1

    print(f"Chapter: {progress.chapter_dir}")
    print(f"Shots: {progress.total}  Finals: {progress.count_with('final')}  Videos: {progress.count_with('video')}")
    for s in progress.shots[:20]:
        print(f"  {s.shot_id}  {s.steps_done}/{s.steps_total}  next={s.next_step}")
    if progress.total > 20:
        print(f"  … and {progress.total - 20} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
