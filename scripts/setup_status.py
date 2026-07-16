"""
Project setup checklist for AI Animation Studio.

Scans machine, mentor-pack content, and active-chapter requirements.
"""

from __future__ import annotations

import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from artifact_paths import ROOT
from chapter_paths import COMIC_SOURCE_DIR, chapter_display_path, is_chapter_dir
from fal_common import read_fal_key
from panel_crop import normalize_page_filename, resolve_chapter_page
from voice_paths import VOICE_REFERENCE, VR_JP_DENKEN, VR_JP_FERN, VR_JP_FRIEREN, VR_JP_STARK

SetupStatus = Literal["ok", "warn", "fail", "skip"]

_SPEAKER_RE = re.compile(r"\b(Frieren|Fern|Stark|Denken)\b", re.I)

_VOICE_REF_FILES: dict[str, tuple[Path, Path]] = {
    "frieren": (
        VR_JP_FRIEREN / "frieren_jp_qwen_ref.wav",
        VR_JP_FRIEREN / "frieren_jp_qwen_ref.txt",
    ),
    "fern": (
        VR_JP_FERN / "fern_jp_qwen_ref.wav",
        VR_JP_FERN / "fern_jp_qwen_ref.txt",
    ),
    "stark": (
        VR_JP_STARK / "stark_jp_qwen_ref.wav",
        VR_JP_STARK / "stark_jp_qwen_ref.txt",
    ),
    "denken": (
        VR_JP_DENKEN / "denken_jp_qwen_ref.wav",
        VR_JP_DENKEN / "denken_jp_qwen_ref.txt",
    ),
}

_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


@dataclass(frozen=True)
class SetupCheck:
    id: str
    group: str
    label: str
    status: SetupStatus
    detail: str = ""
    path_hint: str = ""
    fix_hint: str = ""


def _fix_for(status: SetupStatus, hint: str) -> str:
    """Return fix instructions for warn/fail items; empty when OK or skipped."""
    if status in ("fail", "warn") and hint:
        return hint
    return ""


@dataclass
class SetupReport:
    checks: list[SetupCheck] = field(default_factory=list)
    chapter_dir: Path | None = None

    @property
    def ok_count(self) -> int:
        return sum(1 for c in self.checks if c.status == "ok")

    @property
    def warn_count(self) -> int:
        return sum(1 for c in self.checks if c.status == "warn")

    @property
    def fail_count(self) -> int:
        return sum(1 for c in self.checks if c.status == "fail")

    @property
    def required_fail_count(self) -> int:
        return sum(1 for c in self.checks if c.status == "fail" and c.id not in _OPTIONAL_FAIL_IDS)

    def by_group(self) -> dict[str, list[SetupCheck]]:
        out: dict[str, list[SetupCheck]] = {}
        for check in self.checks:
            out.setdefault(check.group, []).append(check)
        return out


_OPTIONAL_FAIL_IDS = frozenset({"ffmpeg", "panels_eng", "panels_jap"})


def _venv_python() -> Path | None:
    if sys.platform == "win32":
        candidate = ROOT / ".venv" / "Scripts" / "python.exe"
    else:
        candidate = ROOT / ".venv" / "bin" / "python"
    return candidate if candidate.is_file() else None


def _check_imports() -> tuple[bool, str]:
    missing: list[str] = []
    for mod in ("streamlit", "fal_client", "dotenv", "PIL"):
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    if missing:
        return False, "Missing: " + ", ".join(missing)
    return True, "streamlit, fal-client, Pillow OK"


def _fal_key_ok() -> tuple[bool, str]:
    key = (read_fal_key() or "").strip()
    if not key:
        return False, "Empty — paste your key from fal.ai/dashboard/keys"
    if key.lower() in {"your_key_here", "paste_your_key_here", "changeme"}:
        return False, "Still a placeholder — replace with your real Fal key"
    return True, "Configured"


def _shot_ids(chapter_dir: Path) -> set[str]:
    try:
        from ingest_summary import _parse_stage2_shot_details

        return {d.shot_id.upper() for d in _parse_stage2_shot_details(chapter_dir)}
    except Exception:
        return set()


def _speakers_needed(chapter_dir: Path) -> set[str]:
    try:
        from ingest_summary import _parse_stage2_shot_details
    except ImportError:
        return set()

    speakers: set[str] = set()
    for detail in _parse_stage2_shot_details(chapter_dir):
        if not detail.has_dialogue:
            continue
        blob = " ".join(
            (
                detail.dialogue_jp,
                detail.dialogue_en,
                detail.what_we_see,
                detail.characters_on_screen,
            )
        )
        for match in _SPEAKER_RE.finditer(blob):
            speakers.add(match.group(1).lower())
    return speakers


def _pages_required(chapter_dir: Path) -> list[str]:
    try:
        from ingest_summary import _parse_stage2_shot_details
    except ImportError:
        return []

    pages: set[str] = set()
    for detail in _parse_stage2_shot_details(chapter_dir):
        page = normalize_page_filename(detail.page)
        if page:
            pages.add(page)
    return sorted(pages)


def _count_reference_images(folder: Path) -> int:
    if not folder.is_dir():
        return 0
    return sum(1 for p in folder.iterdir() if p.suffix.lower() in _IMAGE_EXTS and p.is_file())


def _add(checks: list[SetupCheck], **kwargs: object) -> None:
    checks.append(SetupCheck(**kwargs))  # type: ignore[arg-type]


def scan_setup(chapter_dir: Path | None = None) -> SetupReport:
    """Build the full setup checklist for the dashboard Setup tab."""
    checks: list[SetupCheck] = []
    chapter = chapter_dir.resolve() if chapter_dir is not None else None
    comic_chapter_example = f"{COMIC_SOURCE_DIR.name}/Chapter-81"

    # ── PC ready ──
    venv_py = _venv_python()
    venv_status: SetupStatus = "ok" if venv_py else "fail"
    _add(
        checks,
        id="venv",
        group="PC ready",
        label="Python virtual environment",
        status=venv_status,
        detail="`.venv` found" if venv_py else "Not found",
        path_hint=".venv/",
        fix_hint=_fix_for(
            venv_status,
            "Double-click **`Start-Studio.bat`** at the project root — it creates `.venv` "
            "and runs `pip install -r requirements.txt` on first launch. "
            "Or ask Cursor Agent to run first-time setup (student workbook §2.5).",
        ),
    )

    deps_ok, deps_detail = _check_imports()
    deps_status: SetupStatus = "ok" if deps_ok else "fail"
    _add(
        checks,
        id="deps",
        group="PC ready",
        label="Python dependencies",
        status=deps_status,
        detail=deps_detail,
        path_hint="requirements.txt",
        fix_hint=_fix_for(
            deps_status,
            "Close the dashboard, then run **`Start-Studio.bat`** again (it installs from "
            "`requirements.txt`). If that fails, ask your mentor or Agent to run: "
            "`python -m pip install -r requirements.txt` inside `.venv`.",
        ),
    )

    env_path = ROOT / ".env"
    env_status: SetupStatus = "ok" if env_path.is_file() else "fail"
    _add(
        checks,
        id="env_file",
        group="PC ready",
        label="`.env` file",
        status=env_status,
        detail="Found at project root" if env_path.is_file() else "Missing",
        path_hint=".env",
        fix_hint=_fix_for(
            env_status,
            "In Cursor's file tree: **right-click** `.env.example` → **Copy** → **Paste** → "
            "rename the copy to **`.env`** (exact name, starts with a dot). Save at project root.",
        ),
    )

    key_ok, key_detail = _fal_key_ok()
    key_status: SetupStatus = "ok" if key_ok else "fail"
    _add(
        checks,
        id="fal_key",
        group="PC ready",
        label="FAL_KEY configured",
        status=key_status,
        detail=key_detail,
        path_hint=".env",
        fix_hint=_fix_for(
            key_status,
            "1. Create a free account at [fal.ai/dashboard/keys](https://fal.ai/dashboard/keys).\n"
            "2. Open **`.env`** in Cursor.\n"
            "3. Set `FAL_KEY=paste_your_key_here` (no quotes).\n"
            "4. **Save** and restart the dashboard.\n"
            "Never share `.env` or commit it to GitHub.",
        ),
    )

    ffmpeg = shutil.which("ffmpeg")
    ffmpeg_status: SetupStatus = "ok" if ffmpeg else "warn"
    _add(
        checks,
        id="ffmpeg",
        group="PC ready",
        label="ffmpeg on PATH",
        status=ffmpeg_status,
        detail="Available" if ffmpeg else "Not found (optional for first lesson)",
        path_hint="ffmpeg",
        fix_hint=_fix_for(
            ffmpeg_status,
            "Optional for stills and voice only. Ask your mentor to install **ffmpeg** "
            "and add it to PATH when you need lip-sync mux, BGM trim, or subtitle burn-in.",
        ),
    )

    # ── Chapter ──
    if chapter is None or not is_chapter_dir(chapter):
        _add(
            checks,
            id="chapter",
            group="Chapter",
            label="Chapter folder with stage_02",
            status="fail",
            detail="No valid chapter folder found",
            path_hint=comic_chapter_example,
            fix_hint=(
                f"1. Extract the **mentor pack ZIP** into the project root (merge folders), **or** "
                f"create **`{comic_chapter_example}/`** yourself.\n"
                f"2. The folder must include **`stage_02_shot_list.md`** — that is how the "
                "dashboard finds a chapter.\n"
                f"3. Also copy **`stage_01_ingest.md`**, **`stage_03_series_bible.md`**, and "
                "manga JPGs (`001.jpg`, `002.jpg`, …) from the mentor USB.\n"
                f"4. Refresh this page or pick the chapter in the sidebar **Comic chapter** dropdown."
            ),
        )
    else:
        rel = chapter_display_path(chapter)
        try:
            chapter.relative_to(COMIC_SOURCE_DIR)
            loc_detail = f"`{rel}`"
            loc_status = "ok"
            loc_fix = ""
        except ValueError:
            loc_detail = f"`{rel}` (outside Comic Source)"
            loc_status = "warn"
            loc_fix = (
                f"This chapter works, but the recommended layout is **`{comic_chapter_example}/`**. "
                "Move or copy the folder under **`Comic Source/`** when convenient."
            )

        _add(
            checks,
            id="chapter",
            group="Chapter",
            label="Chapter folder with stage_02",
            status=loc_status,
            detail=loc_detail,
            path_hint=rel,
            fix_hint=_fix_for(loc_status, loc_fix),
        )

        stage2 = chapter / "stage_02_shot_list.md"
        shots = _shot_ids(chapter)
        s2_status: SetupStatus = "ok" if stage2.is_file() and shots else "fail"
        _add(
            checks,
            id="stage_02",
            group="Ingest files",
            label="Stage 2 — shot list",
            status=s2_status,
            detail=f"{len(shots)} shot(s) in stage_02" if shots else "Missing or empty",
            path_hint=f"{rel}/stage_02_shot_list.md",
            fix_hint=_fix_for(
                s2_status,
                f"Copy **`stage_02_shot_list.md`** from the mentor pack into **`{rel}/`**, "
                "or run Cursor Agent with **`/manga-chapter-ingest-stages-1-3`** to build ingest "
                "for a new chapter. The file must list shots (`S001`, `S002`, …) in a markdown table.",
            ),
        )

        stage1 = chapter / "stage_01_ingest.md"
        s1_status: SetupStatus = "ok" if stage1.is_file() else "warn"
        _add(
            checks,
            id="stage_01",
            group="Ingest files",
            label="Stage 1 — ingest",
            status=s1_status,
            detail="Story beats and page order" if stage1.is_file() else "Missing",
            path_hint=f"{rel}/stage_01_ingest.md",
            fix_hint=_fix_for(
                s1_status,
                f"Copy **`stage_01_ingest.md`** from the mentor pack into **`{rel}/`**, "
                "or ask Agent to ingest the chapter with **`/manga-chapter-ingest-stages-1-3`**. "
                "Stage 1 defines page order, RTL read path, and story beats.",
            ),
        )

        stage3 = chapter / "stage_03_series_bible.md"
        s3_status: SetupStatus = "ok" if stage3.is_file() else "warn"
        _add(
            checks,
            id="stage_03",
            group="Ingest files",
            label="Stage 3 — series bible",
            status=s3_status,
            detail="Prompt canon for Agent" if stage3.is_file() else "Missing",
            path_hint=f"{rel}/stage_03_series_bible.md",
            fix_hint=_fix_for(
                s3_status,
                f"Copy **`stage_03_series_bible.md`** from the mentor pack into **`{rel}/`**, "
                "or extend ingest with Agent. Stage 3 holds Fal prompt notes and per-shot style rules.",
            ),
        )

        required_pages = _pages_required(chapter)
        if required_pages:
            found = sum(1 for p in required_pages if resolve_chapter_page(chapter, p))
            missing = len(required_pages) - found
            missing_names = [
                p for p in required_pages if not resolve_chapter_page(chapter, p)
            ]
            if missing == 0:
                page_status = "ok"
                page_detail = f"{found}/{len(required_pages)} manga pages on disk"
                page_fix = ""
            elif found == 0:
                page_status = "fail"
                page_detail = f"0/{len(required_pages)} pages on disk"
                page_fix = (
                    f"Copy manga page scans from the mentor USB into **`{rel}/`**. "
                    f"Expected files include: {', '.join(f'`{p}`' for p in required_pages[:6])}"
                    f"{' …' if len(required_pages) > 6 else ''}.\n"
                    "File names must match the **Page** column in `stage_02_shot_list.md` (e.g. `002.jpg`)."
                )
            else:
                page_status = "warn"
                page_detail = f"{found}/{len(required_pages)} pages found"
                page_fix = (
                    f"Add these missing JPGs to **`{rel}/`**: "
                    f"{', '.join(f'`{p}`' for p in missing_names[:8])}"
                    f"{' …' if len(missing_names) > 8 else ''}."
                )
            _add(
                checks,
                id="manga_pages",
                group="Ingest files",
                label="Manga page JPGs",
                status=page_status,
                detail=page_detail,
                path_hint=f"{rel}/002.jpg …",
                fix_hint=_fix_for(page_status, page_fix),
            )
        else:
            jpg_count = len(list(chapter.glob("*.jpg")))
            mp_status: SetupStatus = "ok" if jpg_count else "warn"
            _add(
                checks,
                id="manga_pages",
                group="Ingest files",
                label="Manga page JPGs",
                status=mp_status,
                detail=f"{jpg_count} JPG(s) in folder" if jpg_count else "No JPGs yet",
                path_hint=f"{rel}/",
                fix_hint=_fix_for(
                    mp_status,
                    f"Copy scanned manga pages (`001.jpg`, `002.jpg`, …) from the mentor pack "
                    f"into **`{rel}/`**. You need at least the pages used in your shot list "
                    "(camp lesson uses **`002.jpg`**).",
                ),
            )

    # ── Voice ──
    vr_ok = VOICE_REFERENCE.is_dir()
    vr_status: SetupStatus = "ok" if vr_ok else "fail"
    _add(
        checks,
        id="voice_reference_dir",
        group="Voice reference",
        label="Voice Reference folder",
        status=vr_status,
        detail="Mentor pack voice clips" if vr_ok else "Folder missing",
        path_hint="Voice Reference/",
        fix_hint=_fix_for(
            vr_status,
            "Copy the entire **`Voice Reference/`** folder from the mentor USB or pack ZIP "
            "into the project root (same level as `scripts/` and `docs/`). "
            "It should contain `Japanese/Frieren/`, `Japanese/Fern/`, `Japanese/Stark/`, etc.",
        ),
    )

    if chapter is not None and is_chapter_dir(chapter):
        speakers = _speakers_needed(chapter)
        if not speakers:
            speakers = {"frieren", "fern", "stark"}
            speaker_note = "Default lesson cast"
        else:
            speaker_note = "Required for dialogue in this chapter"
    else:
        speakers = {"frieren", "fern", "stark"}
        speaker_note = "Core lesson cast"

    for speaker in sorted(speakers):
        wav_path, txt_path = _VOICE_REF_FILES.get(
            speaker,
            (VOICE_REFERENCE / speaker / f"{speaker}_jp_qwen_ref.wav", Path()),
        )
        if speaker not in _VOICE_REF_FILES:
            continue
        wav_ok = wav_path.is_file()
        txt_ok = txt_path.is_file()
        if wav_ok and txt_ok:
            st: SetupStatus = "ok"
            detail = "wav + transcript ready"
            voice_fix = ""
        elif wav_ok or txt_ok:
            st = "warn"
            detail = "Partial — need both .wav and .txt"
            voice_fix = (
                f"Both files are required under **`Voice Reference/Japanese/{speaker.title()}/`**: "
                f"`{speaker}_jp_qwen_ref.wav` and `{speaker}_jp_qwen_ref.txt`. "
                "Re-copy from the mentor pack or ask Agent to run the prepare script for that character."
            )
        else:
            st = "fail"
            detail = speaker_note
            voice_fix = (
                f"Copy from mentor pack to **`Voice Reference/Japanese/{speaker.title()}/`**: "
                f"`{speaker}_jp_qwen_ref.wav` and `{speaker}_jp_qwen_ref.txt`. "
                "These are ~12s Qwen clone clips — not the same as `voice_refs/` processing files."
            )
        hint_path = wav_path if wav_path.is_file() else txt_path
        try:
            path_hint = hint_path.relative_to(ROOT).as_posix()
        except ValueError:
            path_hint = str(hint_path)
        _add(
            checks,
            id=f"voice_{speaker}",
            group="Voice reference",
            label=f"{speaker.title()} JP ref (wav + txt)",
            status=st,
            detail=detail,
            path_hint=path_hint,
            fix_hint=_fix_for(st, voice_fix),
        )

    registry = ROOT / "voice_registry.local.json"
    reg_status: SetupStatus = "ok" if registry.is_file() else "skip"
    _add(
        checks,
        id="voice_registry",
        group="Voice reference",
        label="voice_registry.local.json",
        status=reg_status,
        detail="Cached Qwen embeddings" if registry.is_file() else "Optional — not created yet",
        path_hint="voice_registry.local.json",
        fix_hint="",
    )

    # ── Character references ──
    if chapter is not None and is_chapter_dir(chapter):
        shot_ids = _shot_ids(chapter)
        try:
            from character_bibles import list_characters_with_bibles

            for character in list_characters_with_bibles():
                needed = {s.upper() for s in character.related_shots} & shot_ids
                if not needed:
                    continue
                if character.reference_dir is not None:
                    img_count = _count_reference_images(character.reference_dir)
                    rel_ref = character.reference_dir.relative_to(ROOT).as_posix()
                    if img_count >= 1:
                        cref_status = "ok"
                        cref_detail = f"{img_count} image(s) for {', '.join(sorted(needed))}"
                        cref_fix = ""
                    else:
                        cref_status = "warn"
                        cref_detail = f"Needed for {', '.join(sorted(needed))}"
                        cref_fix = (
                            f"Add PNG/JPG portrait refs under **`{rel_ref}/`** "
                            f"(for {character.display_name}, shots {', '.join(sorted(needed))}). "
                            "Copy from mentor pack `docs/reference/` or export approved stills. "
                            "Open the **Characters** tab to preview when files land."
                        )
                    _add(
                        checks,
                        id=f"char_ref_{character.id}",
                        group="Character references",
                        label=f"{character.display_name} portraits",
                        status=cref_status,
                        detail=cref_detail,
                        path_hint=rel_ref,
                        fix_hint=_fix_for(cref_status, cref_fix),
                    )
                elif not character.has_bible():
                    continue
        except ImportError:
            pass

    if not any(c.group == "Character references" for c in checks):
        _add(
            checks,
            id="char_ref_none",
            group="Character references",
            label="Portrait folders",
            status="skip",
            detail="No extra portrait refs required for this chapter",
            path_hint="docs/reference/",
            fix_hint="",
        )

    # ── Lesson folders (informational) ──
    panels_eng = ROOT / "panels" / "eng"
    panels_jap = ROOT / "panels" / "jap"
    eng_count = len(list(panels_eng.glob("panel_s*.png"))) if panels_eng.is_dir() else 0
    eng_status: SetupStatus = "ok" if eng_count else "warn"
    _add(
        checks,
        id="panels_eng",
        group="Lesson progress",
        label="Panel crops (panels/eng/)",
        status=eng_status,
        detail=f"{eng_count} crop(s) saved" if eng_count else "None yet",
        path_hint="panels/eng/panel_s###.png",
        fix_hint=_fix_for(
            eng_status,
            "Created during the lesson — not in the mentor pack. "
            "Open **Ingest** → pick a page → crop a panel, **or** ask Cursor Agent with "
            "**`/manga-panel-crop-for-shots`** for a shot ID (e.g. S006). "
            "Saves to `panels/eng/panel_s006.png`.",
        ),
    )
    jap_count = len(list(panels_jap.glob("panel_s*.png"))) if panels_jap.is_dir() else 0
    jap_status: SetupStatus = "ok" if jap_count else "warn"
    _add(
        checks,
        id="panels_jap",
        group="Lesson progress",
        label="JP panel crops (panels/jap/)",
        status=jap_status,
        detail=f"{jap_count} crop(s)" if jap_count else "None yet",
        path_hint="panels/jap/panel_s###.png",
        fix_hint=_fix_for(
            jap_status,
            "Same crop as English, but from the **Japanese balloon** scan — used for dialogue truth. "
            "Crop via **Ingest** (JP page) or Agent **`/manga-panel-crop-for-shots`**. "
            "Save under `panels/jap/panel_s###.png`.",
        ),
    )

    skills = ROOT / ".cursor" / "skills"
    skills_status: SetupStatus = "ok" if skills.is_dir() else "warn"
    _add(
        checks,
        id="cursor_skills",
        group="Repo",
        label="Cursor Agent skills",
        status=skills_status,
        detail="`.cursor/skills/` present" if skills.is_dir() else "Missing",
        path_hint=".cursor/skills/",
        fix_hint=_fix_for(
            skills_status,
            "Re-download or re-clone the **AI_Animation** project from GitHub — "
            "`.cursor/skills/` ships with the repo skeleton.",
        ),
    )

    return SetupReport(checks=checks, chapter_dir=chapter if chapter and is_chapter_dir(chapter) else None)
