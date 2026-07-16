"""
Stages 1–3 ingest summary for AI Animation Studio dashboard.

Parses stage_01/02/03 markdown and aggregates shot metadata from pipeline_status.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

from fal_common import ROOT
from chapter_paths import discover_chapter_dirs, find_chapter_dir

STAGE1_TITLE_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
STAGE1_BEAT_ROW_RE = re.compile(
    r"^\|\s*\*?\*?(B\d+)\*?\*?\s*\|\s*([^|]+)\|\s*([^|]+)\|",
    re.MULTILINE,
)
STAGE1_PAGE_INV_RE = re.compile(
    r"^\|\s*(\d+)\s*\|\s*`(\d{3}\.jpg)`\s*\|\s*([^|]+)\|",
    re.MULTILINE,
)
STAGE1_PAGE_ROW_RE = re.compile(r"`(\d{3}\.jpg)`", re.IGNORECASE)
STAGE2_PAGE_HEADER_RE = re.compile(
    r"^###\s+Page\s+\d+\s+—\s+`(\d{3}\.jpg)`",
    re.MULTILINE,
)
STAGE2_CHAR_SNAPSHOT_RE = re.compile(
    r"^\|\s*`(\d{3}\.jpg)`\s*\|\s*([^|]+)\|\s*([^|]+)\|",
    re.MULTILINE,
)
STAGE3_SHOT_RE = re.compile(r"\b(S\d{3}[A-Z]?)\b")

# Bold tokens that are staging notes, not character names
_BOLD_NAME_SKIP = frozenset({
    "JP", "EN", "Fal", "WS", "MS", "MCU", "CU", "EST", "VFX", "HERO", "OTS",
    "First", "Third", "Layered", "Walking", "Daytime", "Great", "Four", "Wide",
    "Ridge", "Split", "B2", "B3", "B4", "Macht", "Qual", "Lernen", "Himmel",
    "Flamme", "Serie", "Glück", "Weise", "El", "Dorado", "Daytime", "Personal",
})


@dataclass
class IngestBeat:
    beat_id: str
    after_page: str
    summary: str


@dataclass
class IngestPageInventory:
    order: int
    file: str
    role: str


@dataclass
class IngestShotDetail:
    shot_id: str
    page: str
    layer: str
    framing: str
    beat: str
    what_we_see: str
    continuity: str
    characters_on_screen: str = ""
    characters_vicinity: str = ""
    dialogue_jp: str = ""
    dialogue_en: str = ""
    dialogue_lines: list[str] | None = None
    has_dialogue: bool = True
    action_movement: str = ""
    scene_blocking: str = ""

    def __post_init__(self) -> None:
        if self.dialogue_lines is None:
            self.dialogue_lines = []


@dataclass
class IngestPageRow:
    page: str
    shot_count: int
    beats: str


@dataclass
class IngestSummary:
    chapter_name: str
    chapter_dir: str
    title: str
    stage1_ok: bool
    stage2_ok: bool
    stage3_ok: bool
    stage1_path: str
    stage2_path: str
    stage3_path: str
    page_files: list[str]
    page_inventory: list[IngestPageInventory]
    beats: list[IngestBeat]
    shot_details: list[IngestShotDetail]
    layers: dict[str, int]
    beat_shot_counts: dict[str, int]
    pages: list[IngestPageRow]
    stage3_shot_refs: int
    stage1_sections: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def _list_chapter_jpgs(chapter_dir: Path) -> list[str]:
    if not chapter_dir.is_dir():
        return []
    return sorted(p.name for p in chapter_dir.glob("*.jpg") if p.is_file())


def _parse_stage1_beats(text: str) -> list[IngestBeat]:
    beats: list[IngestBeat] = []
    seen: set[str] = set()
    for m in STAGE1_BEAT_ROW_RE.finditer(text):
        beat_id = m.group(1).upper()
        if beat_id in seen:
            continue
        after_page = m.group(2).strip()
        summary = m.group(3).strip()
        if after_page.lower() in ("after page", "beat id", "---", "—"):
            continue
        seen.add(beat_id)
        beats.append(
            IngestBeat(
                beat_id=beat_id,
                after_page=after_page,
                summary=summary[:500],
            )
        )
    return beats


def _parse_stage1_page_inventory(text: str) -> list[IngestPageInventory]:
    rows: list[IngestPageInventory] = []
    for m in STAGE1_PAGE_INV_RE.finditer(text):
        order = int(m.group(1))
        rows.append(
            IngestPageInventory(
                order=order,
                file=m.group(2),
                role=m.group(3).strip()[:400],
            )
        )
    return rows


def _split_md_table_row(line: str) -> list[str]:
    """Split a markdown table row on |, respecting escaped \\| in cells."""
    placeholder = "\x00"
    safe = line.replace("\\|", placeholder)
    parts = [p.replace(placeholder, "|").strip() for p in safe.split("|")]
    if parts and parts[0] == "":
        parts = parts[1:]
    if parts and parts[-1] == "":
        parts = parts[:-1]
    return parts


def _parse_character_snapshot(text: str) -> dict[str, tuple[str, str]]:
    """Page → (on-screen, vicinity) from Stage 2 character snapshot table."""
    by_page: dict[str, tuple[str, str]] = {}
    for m in STAGE2_CHAR_SNAPSHOT_RE.finditer(text):
        on_screen = m.group(2).strip()
        if on_screen.lower().startswith("on-screen"):
            continue
        by_page[m.group(1)] = (on_screen, m.group(3).strip())
    return by_page


def _split_scene_and_dialogue(what_we_see: str) -> tuple[str, str, str]:
    """Return (scene blocking, JP dialogue block, EN dialogue block)."""
    text = what_we_see.strip()
    jp_m = re.search(r"\*\*JP(?:[^*]*):\*\*\s*", text, re.IGNORECASE)
    if not jp_m:
        return text, "", ""
    scene = text[: jp_m.start()].strip().rstrip("—").strip()
    rest = text[jp_m.end() :]
    en_m = re.search(r"\s·\s*\*\*EN:\*\*\s*", rest, re.IGNORECASE)
    if en_m:
        return scene, rest[: en_m.start()].strip(), rest[en_m.end() :].strip()
    return scene, rest.strip(), ""


def _extract_bold_character_names(text: str) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for m in re.finditer(r"\*\*([^*]+)\*\*", text):
        token = m.group(1).strip()
        if not token or token.startswith("S0") or token in _BOLD_NAME_SKIP:
            continue
        name = re.split(r"[\s(/:]", token)[0]
        if not name or not name[0].isupper() or name in _BOLD_NAME_SKIP:
            continue
        if name not in seen:
            seen.add(name)
            names.append(name)
    return names


def _format_dialogue_lines(jp: str, en: str) -> list[str]:
    lines: list[str] = []
    if jp:
        for part in re.split(r"\s*/\s*", jp):
            part = part.strip()
            if part:
                lines.append(f"**JP** · {part}")
    if en:
        for part in re.split(r"\s*/\s*", en):
            part = part.strip().strip("*")
            if part:
                lines.append(f"**EN** · {part}")
    return lines


def _infer_action_movement(scene: str) -> str:
    if not scene:
        return "—"
    movement_markers = (
        "walking", "walk", "seated", "sit", "leaning", "looking", "look",
        "backs toward", "toward camera", "kneeling", "carries", "carry",
        "holds", "hold", "reaction", "profile", "delivers", "approach",
        "tiny vs", "overlook", "meet", "fence", "fire", "reading", "aw",
    )
    parts: list[str] = []
    for chunk in re.split(r"[.;]", scene):
        chunk = chunk.strip()
        if not chunk:
            continue
        lower = chunk.lower()
        if any(marker in lower for marker in movement_markers):
            parts.append(chunk)
    if parts:
        return "; ".join(parts)
    return scene


def _merge_character_lists(*sources: str) -> str:
    names: list[str] = []
    seen: set[str] = set()
    for source in sources:
        if not source or source == "—":
            continue
        for piece in re.split(r"[,·+/]", source):
            name = piece.strip().strip("*`")
            if not name or name == "—":
                continue
            key = name.lower()
            if key not in seen:
                seen.add(key)
                names.append(name)
    return ", ".join(names) if names else ""


_DIALOGUE_YES_RE = re.compile(r"dialogue\s*:\s*yes", re.I)
_SILENT_DIALOGUE_RE = re.compile(
    r"dialogue\s*:\s*none|no\s+dialogue|silent\s+(?:flashback|insert|beat|shot)|voice\s*:\s*none",
    re.I,
)
_HAS_JP_DIALOGUE_RE = re.compile(r"\*\*JP(?:[^*]*):\*\*", re.I)
_QUOTED_SPEECH_RE = re.compile(r'[「""][^""」]+[」""?]|—\s*[""「][^""」]+[""」]')
_SPEAKER_LINE_RE = re.compile(
    r"(?:Frieren|Fern|Stark|Denken|Macht|Lernen)\s*:\s*\*\*[^*]+\*\*",
    re.I,
)


def _dialogue_script_exists(shot_id: str) -> bool:
    scripts_dir = ROOT / "scripts"
    if not scripts_dir.is_dir():
        return False
    sid = shot_id.lower()
    return any(scripts_dir.glob(f"generate_{sid}*dialogue*.py"))


def infer_has_dialogue(
    row: IngestShotDetail,
    *,
    shot_id: str | None = None,
) -> bool:
    """True when shot needs voice / lip-sync steps (speech balloon or dialogue script)."""
    sid = (shot_id or row.shot_id).upper()
    combined = f"{row.what_we_see} {row.continuity}"
    if _SILENT_DIALOGUE_RE.search(combined):
        return False
    if _DIALOGUE_YES_RE.search(combined):
        return True
    if row.dialogue_jp or row.dialogue_en or (row.dialogue_lines or []):
        return True
    if _HAS_JP_DIALOGUE_RE.search(row.what_we_see):
        return True
    if _QUOTED_SPEECH_RE.search(row.what_we_see):
        return True
    if _SPEAKER_LINE_RE.search(row.what_we_see):
        return True
    if _dialogue_script_exists(sid):
        return True
    if re.search(
        r"(?:Frieren|Fern|Stark|Denken)\b[^|]{0,80}\?",
        combined,
        re.I,
    ):
        return True
    return False


def build_dialogue_map(chapter_dir: Path) -> dict[str, bool]:
    """Shot ID → has dialogue (from Stage 2 parse)."""
    details = _parse_stage2_shot_details(chapter_dir)
    return {d.shot_id: d.has_dialogue for d in details}


def _enrich_shot_detail(
    row: IngestShotDetail,
    char_by_page: dict[str, tuple[str, str]],
) -> IngestShotDetail:
    page_cast = char_by_page.get(row.page, ("", ""))
    scene, jp, en = _split_scene_and_dialogue(row.what_we_see)
    panel_names = _extract_bold_character_names(row.what_we_see)
    page_on, page_vic = page_cast

    on_screen = _merge_character_lists(page_on, ", ".join(panel_names))
    if not on_screen:
        on_screen = ", ".join(panel_names) if panel_names else (page_on or "—")

    row.scene_blocking = scene or row.what_we_see
    row.dialogue_jp = jp
    row.dialogue_en = en
    row.dialogue_lines = _format_dialogue_lines(jp, en)
    row.action_movement = _infer_action_movement(scene)
    row.characters_on_screen = on_screen or page_on or "—"
    row.characters_vicinity = page_vic or "—"
    row.has_dialogue = infer_has_dialogue(row)
    return row


def _parse_stage2_shot_row(line: str) -> IngestShotDetail | None:
    parts = _split_md_table_row(line)
    if len(parts) < 6:
        return None
    shot_m = re.match(r"\*\*(S\d{3}[A-Z]?)\*\*", parts[0])
    if not shot_m:
        return None
    layer = parts[1].strip().strip("`")
    return IngestShotDetail(
        shot_id=shot_m.group(1).upper(),
        page="",
        layer=layer,
        framing=parts[2].strip(),
        beat=parts[3].strip(),
        what_we_see=parts[4].strip(),
        continuity=parts[5].strip() if len(parts) > 5 else "—",
    )


def _parse_stage2_shot_details(chapter_dir: Path) -> list[IngestShotDetail]:
    path = chapter_dir / "stage_02_shot_list.md"
    if not path.is_file():
        return []

    text = path.read_text(encoding="utf-8")
    char_by_page = _parse_character_snapshot(text)
    page_map: dict[int, str] = {}
    for m in STAGE2_PAGE_HEADER_RE.finditer(text):
        page_map[m.start()] = m.group(1)
    page_starts = sorted(page_map.keys())

    details: list[IngestShotDetail] = []
    for line in text.splitlines():
        if not line.strip().startswith("| **S"):
            continue
        row = _parse_stage2_shot_row(line)
        if row is None:
            continue
        pos = text.find(line)
        page = ""
        for start in reversed(page_starts):
            if start <= pos:
                page = page_map[start]
                break
        row.page = page
        details.append(_enrich_shot_detail(row, char_by_page))
    return details


def _parse_stage1_pages(text: str) -> list[str]:
    found = STAGE1_PAGE_ROW_RE.findall(text)
    return sorted(set(found), key=lambda x: x.lower())


def _parse_stage1_sections(text: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"^##\s+(.+)$", text, re.MULTILINE)]


def _aggregate_pages_from_shots(shots) -> list[IngestPageRow]:
    by_page: dict[str, list] = defaultdict(list)
    for s in shots:
        by_page[s.page or "—"].append(s)

    rows: list[IngestPageRow] = []
    for page in sorted(by_page.keys(), key=lambda p: (p == "—", p)):
        group = by_page[page]
        beat_ids = sorted({s.beat for s in group if s.beat}, key=lambda b: b)
        rows.append(
            IngestPageRow(
                page=page,
                shot_count=len(group),
                beats=", ".join(beat_ids) if beat_ids else "—",
            )
        )
    return rows


def _shot_details_from_pipeline(shots) -> list[IngestShotDetail]:
    rows = [
        IngestShotDetail(
            shot_id=s.shot_id,
            page=s.page or "—",
            layer=s.layer or "—",
            framing=s.framing or "—",
            beat=s.beat or "—",
            what_we_see=s.summary or "—",
            continuity="—",
        )
        for s in shots
    ]
    return [_enrich_shot_detail(row, {}) for row in rows]


def shot_details_for_display(ingest: IngestSummary, shots=None) -> list[IngestShotDetail]:
    """Stage 2 panel rows for UI — parsed markdown first, pipeline shots as fallback."""
    details = getattr(ingest, "shot_details", None) or []
    if details:
        return details
    if shots:
        return _shot_details_from_pipeline(shots)
    return []


def load_ingest_summary(chapter_dir: Path | None = None, shots=None) -> IngestSummary:
    """Stages 1–3 ingest overview for the dashboard Ingest tab."""
    chapter = chapter_dir or find_chapter_dir()
    if chapter is None:
        return IngestSummary(
            chapter_name="",
            chapter_dir="",
            title="",
            stage1_ok=False,
            stage2_ok=False,
            stage3_ok=False,
            stage1_path="",
            stage2_path="",
            stage3_path="",
            page_files=[],
            page_inventory=[],
            beats=[],
            shot_details=[],
            layers={},
            beat_shot_counts={},
            pages=[],
            stage3_shot_refs=0,
            stage1_sections=[],
        )

    if shots is None:
        from pipeline_status import scan_chapter

        shots = scan_chapter(chapter).shots

    stage1 = chapter / "stage_01_ingest.md"
    stage2 = chapter / "stage_02_shot_list.md"
    stage3 = chapter / "stage_03_series_bible.md"

    title = chapter.name
    beats: list[IngestBeat] = []
    page_inventory: list[IngestPageInventory] = []
    page_files: list[str] = []
    stage1_sections: list[str] = []
    shot_details: list[IngestShotDetail] = []

    if stage1.is_file():
        text = stage1.read_text(encoding="utf-8")
        m = STAGE1_TITLE_RE.search(text)
        if m:
            title = m.group(1).strip()
        beats = _parse_stage1_beats(text)
        page_inventory = _parse_stage1_page_inventory(text)
        page_files = _parse_stage1_pages(text)
        stage1_sections = _parse_stage1_sections(text)

    if stage2.is_file():
        shot_details = _parse_stage2_shot_details(chapter)

    if not page_files:
        page_files = _list_chapter_jpgs(chapter)
    if not page_files and shots:
        page_files = sorted({s.page for s in shots if s.page})

    layers: dict[str, int] = {}
    beat_shot_counts: dict[str, int] = {}
    for s in shots:
        layer = s.layer.strip() or "—"
        layers[layer] = layers.get(layer, 0) + 1
        beat = s.beat.strip() or "—"
        beat_shot_counts[beat] = beat_shot_counts.get(beat, 0) + 1

    if not beats:
        beats = [
            IngestBeat(beat_id=b, after_page="—", summary=f"{n} shot(s) in Stage 2")
            for b, n in sorted(beat_shot_counts.items(), key=lambda x: x[0])
            if b != "—"
        ]

    if not shot_details and shots:
        shot_details = _shot_details_from_pipeline(shots)

    stage3_refs = 0
    if stage3.is_file():
        stage3_refs = len(set(STAGE3_SHOT_RE.findall(stage3.read_text(encoding="utf-8"))))

    return IngestSummary(
        chapter_name=chapter.name,
        chapter_dir=str(chapter),
        title=title,
        stage1_ok=stage1.is_file(),
        stage2_ok=stage2.is_file(),
        stage3_ok=stage3.is_file(),
        stage1_path=str(stage1) if stage1.is_file() else "",
        stage2_path=str(stage2) if stage2.is_file() else "",
        stage3_path=str(stage3) if stage3.is_file() else "",
        page_files=page_files,
        page_inventory=page_inventory,
        beats=beats,
        shot_details=shot_details,
        layers=dict(sorted(layers.items(), key=lambda x: (-x[1], x[0]))),
        beat_shot_counts=dict(sorted(beat_shot_counts.items(), key=lambda x: x[0])),
        pages=_aggregate_pages_from_shots(shots),
        stage3_shot_refs=stage3_refs,
        stage1_sections=stage1_sections,
    )
