"""
Character bible registry for the beginner dashboard.

Lists cast members that have at least one docs/ bible file (appearance and/or
personality). Paths are resolved against the project root.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


@dataclass(frozen=True)
class ReferenceImage:
    path: Path
    caption: str
    source: str = "Reference"


def _caption_from_filename(path: Path) -> str:
    return path.stem.replace("_", " ").replace("-", " ")


def _add_image(
    out: list[ReferenceImage],
    seen: set[Path],
    path: Path,
    caption: str,
    source: str,
) -> None:
    resolved = path.resolve()
    if resolved.suffix.lower() not in _IMAGE_EXTS or not resolved.is_file():
        return
    if resolved in seen:
        return
    seen.add(resolved)
    out.append(ReferenceImage(path=resolved, caption=caption, source=source))


def _images_linked_in_doc(doc_path: Path) -> list[tuple[Path, str]]:
    """Local image paths linked from a markdown bible doc."""
    text = doc_path.read_text(encoding="utf-8")
    base = doc_path.parent
    found: list[tuple[Path, str]] = []
    seen: set[Path] = set()
    for match in re.finditer(r"!?\[([^\]]*)\]\(([^)]+)\)", text):
        label, target = match.group(1), match.group(2)
        if target.startswith(("http://", "https://", "#")):
            continue
        resolved = (base / target).resolve()
        if resolved.suffix.lower() not in _IMAGE_EXTS or not resolved.is_file():
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        cap = label.strip() or _caption_from_filename(resolved)
        found.append((resolved, cap))
    return found


def _panel_crop_path(shot_id: str) -> Path:
    sid = shot_id.strip().lower()
    return ROOT / "panels" / "eng" / f"panel_{sid}.png"


@dataclass(frozen=True)
class CharacterBible:
    id: str
    display_name: str
    appearance_doc: Path | None = None
    personality_doc: Path | None = None
    reference_dir: Path | None = None
    skill_relpath: str | None = None
    related_shots: tuple[str, ...] = ()
    voice_note: str = ""

    def has_bible(self) -> bool:
        docs = (self.appearance_doc, self.personality_doc)
        return any(p is not None and p.is_file() for p in docs)

    def reference_images(self) -> list[ReferenceImage]:
        out: list[ReferenceImage] = []
        seen: set[Path] = set()

        if self.reference_dir is not None and self.reference_dir.is_dir():
            for path in sorted(self.reference_dir.iterdir()):
                if path.suffix.lower() in _IMAGE_EXTS:
                    _add_image(
                        out,
                        seen,
                        path,
                        _caption_from_filename(path),
                        "Character reference",
                    )

        for doc_path in (self.appearance_doc, self.personality_doc):
            if doc_path is None or not doc_path.is_file():
                continue
            for path, caption in _images_linked_in_doc(doc_path):
                _add_image(out, seen, path, caption, "Bible doc")

        for shot_id in self.related_shots:
            panel = _panel_crop_path(shot_id)
            _add_image(out, seen, panel, f"{shot_id.upper()} panel crop", "Panel crop")

        try:
            from artifact_paths import hero_still
        except ImportError:
            hero_still = None  # type: ignore[assignment]

        if hero_still is not None:
            for shot_id in self.related_shots:
                still = hero_still(shot_id)
                if still is not None:
                    _add_image(
                        out,
                        seen,
                        still,
                        f"{shot_id.upper()} approved still",
                        "Approved still",
                    )

        return out

    def available_sections(self) -> tuple[str, ...]:
        out: list[str] = []
        if self.appearance_doc and self.appearance_doc.is_file():
            out.append("Appearance")
        if self.personality_doc and self.personality_doc.is_file():
            out.append("Personality")
        out.append("Reference images")
        return tuple(out)


# Registry — add rows when new character bibles land in docs/.
_CHARACTER_REGISTRY: tuple[CharacterBible, ...] = (
    CharacterBible(
        id="denken",
        display_name="Denken",
        appearance_doc=DOCS / "denken-appearance-reference.md",
        personality_doc=DOCS / "denken-qwen-personality-guide.md",
        skill_relpath=".cursor/skills/qwen-denken-dialogue/SKILL.md",
        related_shots=("S016", "S017", "S075"),
        voice_note="JP: Jiro Saito · EN: Ben Phillips · baritone elder mage",
    ),
    CharacterBible(
        id="macht",
        display_name="Macht of El Dorado",
        appearance_doc=DOCS / "macht-appearance-reference.md",
        reference_dir=DOCS / "reference" / "macht",
        related_shots=("S034", "S050"),
        voice_note="Silent in ch.81 pipeline shots — visual / flashback only",
    ),
    CharacterBible(
        id="stark",
        display_name="Stark",
        personality_doc=DOCS / "stark-qwen-personality-guide.md",
        skill_relpath=".cursor/skills/qwen-stark-dialogue/SKILL.md",
        related_shots=("S008", "S011", "S012", "S036"),
        voice_note="JP: Chiaki Kobayashi · EN: Jordan Dash Cruz",
    ),
    CharacterBible(
        id="fern",
        display_name="Fern",
        personality_doc=DOCS / "fern-qwen-personality-guide.md",
        skill_relpath=".cursor/skills/fern-dialogue-s005/SKILL.md",
        related_shots=("S004", "S005"),
        voice_note="JP clone from fernsource.mp4 · polite disciple register",
    ),
)


def list_characters_with_bibles() -> list[CharacterBible]:
    """Characters that have at least one on-disk bible doc (appearance or personality)."""
    return [c for c in _CHARACTER_REGISTRY if c.has_bible()]


def get_character(character_id: str) -> CharacterBible | None:
    key = character_id.strip().lower()
    for c in _CHARACTER_REGISTRY:
        if c.id == key:
            return c if c.has_bible() else None
    return None


def extract_one_line_summary(md_path: Path) -> str:
    """Pull ## One-line summary body, or first substantive paragraph."""
    if not md_path.is_file():
        return ""
    text = md_path.read_text(encoding="utf-8")
    m = re.search(
        r"^##\s+One-line summary\s*\n+(.+?)(?:\n##|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if m:
        line = m.group(1).strip().split("\n")[0].strip()
        return line
    for line in text.splitlines():
        s = line.strip()
        if s and not s.startswith("#") and not s.startswith("|") and s != "---":
            return s
    return ""


def read_markdown_section(md_path: Path, heading: str) -> str:
    """Return markdown under ## {heading} until the next ## heading."""
    if not md_path.is_file():
        return ""
    text = md_path.read_text(encoding="utf-8")
    pattern = rf"^##\s+{re.escape(heading)}\s*\n+(.*?)(?=\n## |\Z)"
    m = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    return m.group(1).strip() if m else ""


def markdown_for_display(content: str, doc_path: Path) -> str:
    """Rewrite relative doc links so Streamlit markdown resolves from project root."""
    base = doc_path.parent

    def _link_repl(match: re.Match[str]) -> str:
        target = match.group(1)
        if target.startswith(("http://", "https://", "#")):
            return match.group(0)
        resolved = (base / target).resolve()
        if resolved.is_file():
            try:
                rel = resolved.relative_to(ROOT)
                return f"]({rel.as_posix()})"
            except ValueError:
                return f"]({resolved.as_posix()})"
        return match.group(0)

    out = re.sub(r"\]\(([^)]+)\)", _link_repl, content)
    # Image refs: ![alt](./path) — Streamlit needs paths it can read; use docs/ relative.
    def _img_repl(match: re.Match[str]) -> str:
        alt, target = match.group(1), match.group(2)
        if target.startswith(("http://", "https://")):
            return match.group(0)
        resolved = (base / target).resolve()
        if resolved.is_file():
            try:
                rel = resolved.relative_to(ROOT)
                return f"![{alt}]({rel.as_posix()})"
            except ValueError:
                return f"![{alt}]({resolved.as_posix()})"
        return match.group(0)

    return re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", _img_repl, out)


def load_doc_body(md_path: Path, *, skip_title_block: bool = True) -> str:
    if not md_path.is_file():
        return ""
    text = md_path.read_text(encoding="utf-8")
    if skip_title_block:
        # Drop leading # title and metadata block before first ## section.
        m = re.search(r"^##\s+", text, re.MULTILINE)
        if m:
            text = text[m.start() :]
    return markdown_for_display(text.strip(), md_path)


def reference_images_for(character: CharacterBible) -> list[ReferenceImage]:
    return character.reference_images()
