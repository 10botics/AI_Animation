"""
Build print-friendly PDFs from the English student workbook.

Outputs:
  docs/cursor-student-workbook-en-cursor-guide.pdf  How to use Cursor
  docs/cursor-student-workbook-en-setup.pdf         Day 1 - setup, folders, manga
  docs/cursor-student-workbook-en-s006-first-try.pdf  Day 2 - S006 walkthrough
  docs/cursor-student-workbook-en.pdf             Skills workflow + reference

Requires: pip install fpdf2
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).resolve().parents[1]
OUT_SETUP = ROOT / "docs" / "cursor-student-workbook-en-setup.pdf"
OUT_CURSOR = ROOT / "docs" / "cursor-student-workbook-en-cursor-guide.pdf"
OUT_S006 = ROOT / "docs" / "cursor-student-workbook-en-s006-first-try.pdf"
OUT = ROOT / "docs" / "cursor-student-workbook-en.pdf"  # full reference

FAL_FREE = "FREE — no Fal.ai credits"
FAL_COST = "USES FAL CREDITS — costs money on your fal.ai account"
FAL_COST_VOICE = "USES FAL CREDITS — one charge per speaker WAV (Fern + Frieren = 2 calls on S006)"
FAL_COST_STILL = "USES FAL CREDITS — Nano Banana image generation"
FAL_COST_VIDEO = "USES FAL CREDITS — Seedance or Kling video generation"
FAL_COST_LIPSYNC = "USES FAL CREDITS — PixVerse lip-sync"

SKILL_MANGA_STUDY = "/manga-chapter-ingest-stages-1-3"


def resolve_manga_page_002() -> Path:
    for candidate in (
        ROOT / "Chapter-81" / "002.jpg",
        ROOT / "Frierien-chapter081" / "002.jpg",
        ROOT / "002.jpg",
    ):
        if candidate.is_file():
            return candidate
    return ROOT / "Chapter-81" / "002.jpg"


S006_ASSETS = {
    "manga_002": resolve_manga_page_002(),
    "panel_eng": ROOT / "panels" / "eng" / "panel_s006.png",
    "panel_jap": ROOT / "panels" / "jap" / "panel_s006jap.png",
    "still_s005": ROOT / "Tests" / "Final" / "S005_nano-banana-2-edit_20260330T034325Z.png",
    "still_s006": ROOT / "Tests" / "Final" / "S006_nano-banana-2-edit_20260330T035743Z.png",
    "still_s006a": ROOT / "Tests" / "Final" / "S006A_nano-banana-2-edit_20260605T020608Z.png",
    "still_s006b": ROOT / "Tests" / "Final" / "S006B_nano-banana-2-edit_20260330T035743Z.png",
}

# Approved stills for figures (camp sequence page 002)
FIGURES: list[tuple[str, Path, str]] = [
    (
        "Fig 1  - S002 wide establish (Stage 4 still)",
        ROOT / "Tests" / "Final" / "S002_nano-banana-2-edit_20260326T094158Z.png",
        "Wide camp shot: party at fire. Good first motion test with Seedance or Kling.",
    ),
    (
        "Fig 2  - S003 squirrel messenger (Stage 4 still)",
        ROOT / "Tests" / "Final" / "S003_extendcampsquirrel_nano-banana-2-edit_20260326T150111Z.png",
        "Recommended first still for beginners  - one face + small critter.",
    ),
    (
        "Fig 3  - Manga panel crop -> anime still",
        ROOT / "panels" / "eng" / "panel_s003.png",
        "Left: greyscale manga crop (panels/eng/panel_s003.png). Upload this to Nano Banana 2 edit.",
    ),
    (
        "Fig 4  - S005 Fern close-up (lip-sync friendly)",
        ROOT / "Tests" / "Final" / "S005_nano-banana-2-edit_20260330T034325Z.png",
        "Face visible  - use for dialogue and PixVerse lip-sync practice.",
    ),
    (
        "Fig 5  - S006 camp debate (medium shot)",
        ROOT / "Tests" / "Final" / "S006_nano-banana-2-edit_20260330T035743Z.png",
        "Frieren at tree, Fern by fire. Harder for lip-sync  - pair with S006A insert.",
    ),
    (
        "Fig 6  - S006A insert (bridge for Fern dialogue)",
        ROOT / "Tests" / "Final" / "S006A_nano-banana-2-edit_20260605T020608Z.png",
        "No manga panel  - multi-ref from S005 + S006. Fern mouth clear for lip-sync.",
    ),
]

MARGIN = 18
CONTENT_W = 210 - 2 * MARGIN  # A4 mm
ACCENT = (41, 98, 255)
ACCENT_DARK = (24, 52, 120)
CALLOUT_BG = (240, 245, 255)
CODE_BG = (245, 245, 245)


def _pdf_text(text: str) -> str:
    """fpdf Helvetica is Latin-1 only — normalize common Unicode punctuation."""
    for old, new in (
        ("\u2014", " - "),
        ("\u2013", "-"),
        ("\u2026", "..."),
        ("\u2192", "->"),
        ("\u2018", "'"),
        ("\u2019", "'"),
        ("\u201c", '"'),
        ("\u201d", '"'),
    ):
        text = text.replace(old, new)
    return text


class WorkbookPDF(FPDF):
    def __init__(self, *, booklet_title: str = "Student Workbook") -> None:
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=20)
        self._section = ""
        self._booklet_title = booklet_title
        self._toc: list[tuple[str, int, int]] = []  # title, level (1=h1, 2=h2), page_no

    def header(self) -> None:
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 6, f"AI Animation  - {self._booklet_title}", align="L")
        self.cell(0, 6, self._section, align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.4)
        self.line(MARGIN, self.get_y(), 210 - MARGIN, self.get_y())
        self.ln(4)
        self.set_text_color(0, 0, 0)

    def footer(self) -> None:
        self.set_y(-14)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, f"10botics AI_Animation  -  {date.today().isoformat()}  -  Page {self.page_no()}", align="C")

    def set_section(self, name: str) -> None:
        self._section = name

    def h1(self, text: str, *, record_toc: bool = True) -> None:
        text = _pdf_text(text)
        if record_toc:
            self._toc.append((text, 1, self.page_no()))
        self.set_section(text)
        self.ln(2)
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(*ACCENT_DARK)
        self.multi_cell(CONTENT_W, 10, text)
        self.set_text_color(0, 0, 0)
        self.ln(3)

    def h2(self, text: str, *, record_toc: bool = True) -> None:
        text = _pdf_text(text)
        if record_toc:
            self._toc.append((text, 2, self.page_no()))
        self.ln(2)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*ACCENT_DARK)
        self.multi_cell(CONTENT_W, 8, text)
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def h3(self, text: str, *, record_toc: bool = False) -> None:
        text = _pdf_text(text)
        if record_toc:
            self._toc.append((text, 2, self.page_no()))
        self.ln(1)
        self.set_font("Helvetica", "B", 11)
        self.multi_cell(CONTENT_W, 6, text)
        self.ln(1)

    def render_table_of_contents(self, entries: list[tuple[str, int, int]], *, page_offset: int) -> None:
        self.h1("Contents", record_toc=False)
        self.body("Jump to the section you need. Page numbers match this booklet.")
        self.ln(1)
        self.set_font("Helvetica", "", 10)
        for title, level, page in entries:
            if page <= 1:
                continue
            display_page = page + page_offset
            indent = 8 if level == 2 else 0
            title_w = CONTENT_W - indent - 14
            self.set_x(MARGIN + indent)
            self.cell(title_w, 6, title, new_x="RIGHT", new_y="NEXT")
            self.set_x(MARGIN + CONTENT_W - 12)
            self.set_font("Helvetica", "B", 10)
            self.cell(12, 6, str(display_page), align="R", new_x="LMARGIN", new_y="NEXT")
            self.set_font("Helvetica", "", 10)
            if self.get_y() > 270:
                self.add_page()
                self.h2("Contents (continued)", record_toc=False)  # noqa: page break only
        self.ln(4)

    def body(self, text: str) -> None:
        text = _pdf_text(text)
        self.set_font("Helvetica", "", 10)
        self.multi_cell(CONTENT_W, 5.5, text)
        self.ln(2)

    def bullet(self, text: str) -> None:
        text = _pdf_text(text)
        self.set_font("Helvetica", "", 10)
        x = self.get_x()
        self.cell(5, 5.5, chr(149))
        self.multi_cell(CONTENT_W - 5, 5.5, text)
        self.set_x(x)
        self.ln(1)

    def callout(self, title: str, text: str) -> None:
        title, text = _pdf_text(title), _pdf_text(text)
        y0 = self.get_y()
        self.set_fill_color(*CALLOUT_BG)
        self.set_font("Helvetica", "B", 10)
        self.set_x(MARGIN)
        self.multi_cell(CONTENT_W, 7, f"  {title}", fill=True)
        self.set_font("Helvetica", "", 9)
        self.set_x(MARGIN)
        self.multi_cell(CONTENT_W, 5, f"  {text}", fill=True)
        self.ln(3)
        if self.get_y() - y0 < 12:
            self.ln(2)

    def labeled_field(
        self,
        label: str,
        value: str,
        *,
        value_bold: bool = False,
        color: tuple[int, int, int] | None = None,
    ) -> None:
        """Label + value on one row; value wraps within content width."""
        label, value = _pdf_text(label), _pdf_text(value)
        label_w = 17
        self.set_x(MARGIN)
        self.set_font("Helvetica", "B", 10)
        self.cell(label_w, 5.5, label, align="R", new_x="RIGHT", new_y="TOP")
        if color:
            self.set_text_color(*color)
        self.set_font("Helvetica", "B" if value_bold else "", 10)
        self.multi_cell(CONTENT_W - label_w, 5.5, value)
        self.set_text_color(0, 0, 0)
        self.ln(1)

    def code_block(self, text: str) -> None:
        text = _pdf_text(text)
        self.set_fill_color(*CODE_BG)
        self.set_font("Courier", "", 8.5)
        for line in text.strip().splitlines() or [""]:
            self.set_x(MARGIN)
            self.multi_cell(CONTENT_W, 4.8, "  " + line, fill=True)
        self.ln(3)
        self.set_font("Helvetica", "", 10)

    def simple_table(self, headers: list[str], rows: list[list[str]], col_widths: list[float] | None = None) -> None:
        headers = [_pdf_text(h) for h in headers]
        rows = [[_pdf_text(c) for c in row] for row in rows]
        if col_widths is None:
            col_widths = [CONTENT_W / len(headers)] * len(headers)
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(*ACCENT)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=1, fill=True)
        self.ln()
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(0, 0, 0)
        fill = False
        for row in rows:
            if self.get_y() > 265:
                self.add_page()
            if fill:
                self.set_fill_color(248, 248, 248)
            else:
                self.set_fill_color(255, 255, 255)
            max_h = 7
            # measure row height
            for i, cell in enumerate(row):
                nb = self.multi_cell(col_widths[i], 5, cell, dry_run=True, output="LINES")
                max_h = max(max_h, 5 * len(nb))
            y_row = self.get_y()
            x0 = self.get_x()
            for i, cell in enumerate(row):
                self.set_xy(x0 + sum(col_widths[:i]), y_row)
                self.multi_cell(col_widths[i], 5, cell, border=1, fill=True)
            self.set_xy(x0, y_row + max_h)
            fill = not fill
        self.ln(3)

    def figure(self, title: str, path: Path, caption: str, *, max_h: float = 72) -> None:
        title, caption = _pdf_text(title), _pdf_text(caption)
        if not path.is_file():
            self.h3(title)
            self.body(f"[Image not found: {path.name}]")
            return
        if self.get_y() > 235:
            self.add_page()
        self.h3(title)
        self.image(str(path), w=CONTENT_W, h=max_h)
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(80, 80, 80)
        self.multi_cell(CONTENT_W, 5, caption)
        self.set_text_color(0, 0, 0)
        self.ln(4)

    def figure_pair(
        self,
        title: str,
        left: Path,
        right: Path,
        left_label: str,
        right_label: str,
        caption: str,
        *,
        max_h: float = 58,
    ) -> None:
        if self.get_y() > 220:
            self.add_page()
        title, caption = _pdf_text(title), _pdf_text(caption)
        left_label, right_label = _pdf_text(left_label), _pdf_text(right_label)
        self.h3(title)
        half = (CONTENT_W - 4) / 2
        y0 = self.get_y()
        x0 = MARGIN
        for path, label, x in ((left, left_label, x0), (right, right_label, x0 + half + 4)):
            self.set_xy(x, y0)
            self.set_font("Helvetica", "B", 8)
            self.cell(half, 5, label)
            if path.is_file():
                self.image(str(path), x=x, y=y0 + 5, w=half, h=max_h)
            else:
                self.set_xy(x, y0 + 10)
                self.set_font("Helvetica", "", 8)
                self.cell(half, 8, f"[missing: {path.name}]")
        self.set_y(y0 + 5 + max_h + 3)
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(80, 80, 80)
        self.multi_cell(CONTENT_W, 5, caption)
        self.set_text_color(0, 0, 0)
        self.ln(4)

    def pipeline_diagram(self) -> None:
        self.h2("Pipeline - dialogue drives timing")
        boxes = [
            ("Analyze", "JP balloons\n+ stage_03"),
            ("5b Voice", "Qwen TTS\nFIRST"),
            ("Timing", "Measure WAV\npick duration"),
            ("4 Still", "Nano Banana\nPNG"),
            ("5 Video", "Seedance FIRST\nKling fallback"),
            ("5c Lipsync", "Mask face\nPixVerse"),
            ("6 Assemble", "Scene any\nlength"),
        ]
        bw = CONTENT_W / 4 - 3
        bh = 22
        x0 = MARGIN
        y0 = self.get_y() + 2
        self.set_font("Helvetica", "B", 8)
        cols = 4
        for idx, (title, sub) in enumerate(boxes):
            col = idx % cols
            row = idx // cols
            x = x0 + col * (bw + 4)
            y = y0 + row * (bh + 10)
            self.set_fill_color(*CALLOUT_BG)
            self.set_draw_color(*ACCENT)
            self.rect(x, y, bw, bh, style="DF")
            self.set_xy(x + 2, y + 3)
            self.cell(bw - 4, 5, title)
            self.set_font("Helvetica", "", 7)
            self.set_xy(x + 2, y + 10)
            self.multi_cell(bw - 4, 4, sub)
            self.set_font("Helvetica", "B", 8)
        rows_used = (len(boxes) + cols - 1) // cols
        self.set_y(y0 + rows_used * (bh + 10) + 4)
        self.body(
            "VOICE BEFORE VIDEO LENGTH. Agent: analyze -> Qwen WAV -> measure seconds -> "
            "Seedance I2V first, Kling if MS two-face or policy fail."
        )

    def cover(self, *, subtitle: str, tagline: str) -> None:
        self.add_page()
        self.set_fill_color(*ACCENT_DARK)
        self.rect(0, 0, 210, 297, style="F")
        self.set_fill_color(*ACCENT)
        self.rect(0, 85, 210, 3, style="F")
        self.set_y(100)
        self.set_font("Helvetica", "B", 28)
        self.set_text_color(255, 255, 255)
        self.cell(0, 14, "AI Animation", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 16)
        self.cell(0, 10, self._booklet_title, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(6)
        self.set_font("Helvetica", "", 12)
        self.cell(0, 8, subtitle, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(16)
        self.set_font("Helvetica", "", 11)
        self.multi_cell(0, 7, tagline, align="C")
        self.set_y(240)
        self.set_font("Helvetica", "I", 10)
        self.cell(0, 6, "10botics 2026  -  Education / research use only", align="C")
        self.set_text_color(0, 0, 0)


def build_with_contents(
    *,
    booklet_title: str,
    cover_subtitle: str,
    cover_tagline: str,
    body,
    out_path: Path,
) -> Path:
    """Two-pass build: probe page numbers, then insert Contents after cover."""
    probe = WorkbookPDF(booklet_title=booklet_title)
    probe.set_margins(MARGIN, MARGIN, MARGIN)
    probe.cover(subtitle=cover_subtitle, tagline=cover_tagline)
    probe.add_page()
    body(probe)
    toc_snapshot = list(probe._toc)
    toc_pages = 1

    final = WorkbookPDF(booklet_title=booklet_title)
    final.set_margins(MARGIN, MARGIN, MARGIN)
    final.cover(subtitle=cover_subtitle, tagline=cover_tagline)
    final.add_page()
    final.render_table_of_contents(toc_snapshot, page_offset=toc_pages)
    final.add_page()
    body(final)
    return _write_pdf(final, out_path)


def _write_pdf(pdf: WorkbookPDF, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        pdf.output(str(path))
        return path
    except PermissionError:
        alt = path.with_name(f"{path.stem}_{date.today().strftime('%Y%m%d')}{path.suffix}")
        pdf.output(str(alt))
        print(f"WARNING: {path.name} is locked. Wrote: {alt}", flush=True)
        return alt


def _page_guide(pdf: WorkbookPDF) -> None:
    pdf.h1("Which booklet to read?")
    pdf.simple_table(
        ["Order", "PDF file", "When"],
        [
            ["0 Cursor", "cursor-student-workbook-en-cursor-guide.pdf", "How to use Cursor (@ files, /skills)"],
            ["1 Setup", "cursor-student-workbook-en-setup.pdf", "Day 1 - project + folders + manga"],
            ["2 S006", "cursor-student-workbook-en-s006-first-try.pdf", "Day 2 - first full shot lesson"],
            ["3 Reference", "cursor-student-workbook-en.pdf", "Skills workflow + troubleshooting"],
        ],
        [22, 68, CONTENT_W - 90],
    )
    pdf.body("Read booklets in order 0 then 1 then 2. You do not need coding or the terminal.")


def _explain_what_project_does(pdf: WorkbookPDF) -> None:
    pdf.h1("What can this project do?")
    pdf.body(
        "This folder is a workshop for turning ONE manga panel into a short anime clip. "
        "You are not learning to code. You chat with Cursor Agent; it runs programs for you."
    )
    pdf.simple_table(
        ["Output", "Plain English", "Example folder"],
        [
            ["Colored picture", "Anime still from grey manga crop", "Tests/Final/"],
            ["Voice files", "Characters speaking (.wav)", "outputs/voice/final/"],
            ["Moving clip", "Picture with motion (.mp4)", "outputs/video/"],
            ["Lip-sync clip", "Mouth moves with voice", "outputs/video/ (lipsync)"],
        ],
        [28, 58, CONTENT_W - 86],
    )
    pdf.callout(
        "One panel at a time",
        "Each clip starts from one manga panel. The project does not auto-animate a whole chapter.",
    )


def _explain_shot_id_s006(pdf: WorkbookPDF) -> None:
    pdf.h1("What is S006? (and S006A?)")
    pdf.body(
        "A shot ID like S006 is a label in the story notes (stage_02_shot_list.md). "
        "It means: this manga panel becomes this one anime clip."
    )
    pdf.simple_table(
        ["ID", "What it is", "Story beat"],
        [
            ["S006", "Main panel - camp debate", "Frieren at tree; Fern by fire; BOTH speak"],
            ["S006A", "Extra picture (not in manga)", "Close-up of Fern for her line lip-sync"],
            ["S006B", "Optional video extend", "Hold same angle if you need more time"],
        ],
        [22, 52, CONTENT_W - 74],
    )
    pdf.body(
        "Characters in S006: Fern (apprentice mage) and Frieren (elf mage). "
        "Both need voice WAV files before any video step."
    )


def _cursor_add_files_habit(pdf: WorkbookPDF) -> None:
    pdf.h2("How to add files in Cursor (do this every step)")
    pdf.bullet("Open Agent chat (not Ask mode for production)")
    pdf.bullet("Type / and pick the SKILL first (e.g. /nano-banana-2-prompting)")
    pdf.bullet("Click the @ button in the chat box (or type @)")
    pdf.bullet("Search the FILE NAME from the left sidebar - pick from the list")
    pdf.bullet("Do NOT copy long paths from this PDF - your file names may differ")
    pdf.bullet("Say the shot ID: S006 only")
    pdf.callout("Habit", "Every message = /skill + @ files you picked + S### only + plain English request")


def _at_picker_list(pdf: WorkbookPDF, file_names: list[str]) -> None:
    """List file names to pick in @ menu - never paste folder paths."""
    pdf.body("Click @ in chat and pick these names (search in the sidebar list):")
    for name in file_names:
        pdf.bullet(name)


def _ref_prompt_block(pdf: WorkbookPDF, pick: list[str], prompt: str) -> None:
    _at_picker_list(pdf, pick)
    pdf.body("Then tell Agent (plain English - no copied paths):")
    pdf.code_block(prompt)


def _fill_cursor_guide_body(pdf: WorkbookPDF) -> None:
    pdf.h1("What is Cursor?")
    pdf.body(
        "Cursor is a code editor with an AI assistant (Agent). For this course you use Agent chat "
        "to ask for manga crops, pictures, voice, and video. Agent reads files you pick with @ and runs scripts."
    )

    pdf.h1("Open your project")
    pdf.bullet("Install Cursor from cursor.com")
    pdf.bullet("File > Open Folder > select your AI_Animation folder")
    pdf.bullet("Left sidebar shows folders: Chapter-81, panels, docs, etc.")

    pdf.h1("Agent mode vs Ask mode")
    pdf.simple_table(
        ["Mode", "Use for"],
        [
            ["Agent", "Production — crop, voice, stills, video (DEFAULT for this course)"],
            ["Ask", "Questions only — Agent will NOT run programs"],
        ],
        [28, CONTENT_W - 28],
    )

    pdf.h1("The chat box — your main tool")
    _cursor_add_files_habit(pdf)

    pdf.h2("File names you will @ often")
    pdf.simple_table(
        ["Look for this name in @ picker", "What it is"],
        [
            ["stage_01_ingest.md", "Page read order (RTL) — which panel is 1st, 2nd on each page"],
            ["stage_02_shot_list.md", "List of shots S001, S002... what each panel is"],
            ["stage_03_series_bible.md", "Style + dialogue notes per shot"],
            ["002.jpg", "Full manga page photo (in Chapter-81/)"],
            ["panel_s006.png", "Cropped panel (panels/eng/)"],
            ["panel_s006jap.png", "Same panel with Japanese speech (panels/jap/)"],
            ["S006_....png in Tests/Final", "Your approved anime still (name varies by date)"],
        ],
        [62, CONTENT_W - 62],
    )

    pdf.add_page()
    pdf.h1("Skills — always call them out")
    pdf.body(
        "Type / in chat and choose a skill BEFORE you describe the task. "
        "Skills live in .cursor/skills/. They stop Agent from guessing wrong steps."
    )
    pdf.code_block(
        "Example — study page before crop:\n"
        "/manga-chapter-ingest-stages-1-3\n"
        "@ pick 002.jpg, stage_01_ingest.md, stage_02_shot_list.md\n"
        "Study page 002 RTL. Where is S006? READ only. No Fal credits."
    )
    pdf.code_block(
        "Example — video step:\n"
        "/anime-scene-i2v-prompting\n"
        "@ pick S006 still from Tests/Final\n"
        "@ pick stage_03_series_bible.md\n"
        "Try Seedance FIRST for S006 only. Report MP4 path."
    )

    pdf.h1("When Agent asks permission")
    pdf.simple_table(
        ["Agent asks", "What it means", "You do"],
        [
            ["Run terminal command", "Local setup (venv, pip)", "Allow if mentor said setup is OK"],
            ["Fal / API call", "USES FAL CREDITS", "Allow only if you expect that step to cost money"],
            ["Read file", "Usually FREE", "Allow"],
        ],
        [38, 58, CONTENT_W - 96],
    )

    pdf.h1("Credit cheat sheet")
    pdf.simple_table(
        ["Step", "Credits?"],
        [
            ["Explain shot, plan timing", "FREE"],
            ["Crop panel (local)", "FREE"],
            ["Qwen voice WAV", "USES CREDITS — each speaker = separate call"],
            ["Anime still (Nano Banana)", "USES CREDITS"],
            ["Video (Seedance or Kling)", "USES CREDITS — try Seedance first"],
            ["PixVerse lip-sync", "USES CREDITS — one pass per speaker"],
        ],
        [58, CONTENT_W - 58],
    )

    pdf.h1("Next booklets")
    pdf.bullet("Setup PDF — install project, folders, read manga right-to-left")
    pdf.bullet("S006 PDF — first full shot with pictures step by step")
    pdf.bullet("Reference PDF — full skills workflow")


def _folder_guide_plain(pdf: WorkbookPDF) -> None:
    pdf.h1("3. Project folders - simple guide")
    pdf.body("Two piles: files in the ZIP download vs files you or mentor add later.")
    pdf.simple_table(
        ["Folder", "Plain name", "What is inside", "When you need it"],
        [
            ["Chapter-81/", "Story notes", "stage_01 ingest, stage_02 shot list, stage_03 style", "Pick in @ menu each shot"],
            ["Chapter-81/002.jpg", "Manga page photo", "Full scanned page", "Read order; crop panels"],
            ["panels/eng/", "Panel crops", "One PNG per shot", "Before anime still"],
            ["panels/jap/", "JP balloons", "Japanese dialogue image", "Voice and lip-sync truth"],
            ["Tests/Final/", "Approved pictures", "Good anime stills", "Before video step"],
            ["outputs/voice/", "Dialogue audio", ".wav speech files", "After voice; before lip-sync"],
            ["outputs/video/", "Video clips", ".mp4 files", "After video step"],
            [".cursor/skills/", "Agent recipes", "Checklists for Agent", "Type /skill in chat"],
            [".env", "Your API key", "FAL_KEY only you", "Setup once - keep secret"],
        ],
        [28, 24, 48, CONTENT_W - 100],
    )
    pdf.callout("You do not open scripts/", "Cursor Agent runs programs. You write prompts and pick files with @.")


def _skills_workflow_detail(pdf: WorkbookPDF) -> None:
    """Short skills intro for Setup booklet."""
    pdf.add_page()
    pdf.h1("5. Skills - quick intro")
    pdf.body("Type /skill-name in Cursor. See Full Reference PDF for complete skills workflow.")
    pdf.code_block(
        "0. /manga-chapter-ingest-stages-1-3  (study page RTL + shot IDs — FREE)\n"
        "1. /manga-panel-crop-for-shots\n"
        "2. /qwen-frieren-dialogue  (voice BEFORE video)\n"
        "3. /nano-banana-2-prompting\n"
        "4. /anime-scene-i2v-prompting\n"
        "5. /pixverse-lipsync"
    )
    pdf.callout(
        "Study the page first",
        "Before cropping, use manga-chapter-ingest to read 002.jpg RTL and find your S### row in stage_02.",
    )


def _skills_workflow_full(pdf: WorkbookPDF) -> None:
    """Full skills workflow for Reference booklet."""
    pdf.h1("Skills workflow - complete guide")
    pdf.body(
        "Skills are checklists in .cursor/skills/. They tell Cursor Agent which files to read "
        "and which step comes next. Use them on EVERY production message."
    )

    pdf.h2("Golden rules")
    pdf.bullet("Click @ and pick files BY NAME (stage_02_shot_list.md, panel_s006jap.png, etc.)")
    pdf.bullet("Type /skill-name at the start of your message")
    pdf.bullet("Say one shot only: S006 only - never whole chapter")
    pdf.bullet("Voice audio BEFORE video length on any dialogue shot")
    pdf.bullet("Do NOT copy paths like @Chapter-81/... from examples - use the @ picker")

    pdf.h2("Three workflow paths")
    pdf.simple_table(
        ["Shot type", "Example", "Skills order"],
        [
            ["Silent panel", "S002 wide", "study page -> crop -> still -> video"],
            ["One speaker", "S005 Fern", "study page -> crop -> voice -> still -> video -> lipsync"],
            ["Two speakers", "S006 debate", "study page -> crop -> voice -> still -> S006A -> 2 videos -> 2 lipsync"],
        ],
        [28, 28, CONTENT_W - 56],
    )

    pdf.add_page()
    pdf.h2("Master order - dialogue shot (S006 class)")
    pdf.simple_table(
        ["#", "Skill", "You get", "Do not skip because"],
        [
            ["0", "manga-chapter-ingest-stages-1-3", "RTL order + S### on page", "Wrong panel = wrong story"],
            ["1", "manga-panel-crop-for-shots", "panel_s###.png", "Need correct panel rectangle"],
            ["2", "qwen-frieren-dialogue", ".wav + seconds", "Video length comes from speech"],
            ["3", "nano-banana-2-prompting", "Tests/Final still", "Video needs approved picture"],
            ["4", "nano-banana-2-prompting", "S006A insert if needed", "MS mouth too small for lip-sync"],
            ["5", "anime-scene-i2v-prompting", ".mp4 video", "Motion from still"],
            ["6", "pixverse-lipsync", "mouth sync MP4", "One pass per speaker; mask other face"],
        ],
        [10, 52, 38, CONTENT_W - 100],
    )

    def skill_block(
        name: str,
        when: str,
        pick_names: list[str],
        agent_steps: list[str],
        output: str,
        mistakes: str,
    ) -> None:
        if pdf.get_y() > 220:
            pdf.add_page()
        pdf.h2(name)
        pick_text = ", ".join(pick_names)
        pdf.simple_table(
            ["", ""],
            [
                ["When to use", when],
                ["Pick in @ menu", pick_text],
                ["Output folder", output],
                ["Stops mistakes", mistakes],
            ],
            [32, CONTENT_W - 32],
        )
        pdf.body("Agent steps:")
        for step in agent_steps:
            pdf.bullet(step)

    skill_block(
        "manga-chapter-ingest-stages-1-3",
        "Study a manga PAGE before crop or voice. Read RTL order, map panels to S###, read dialogue notes.",
        ["002.jpg", "stage_01_ingest.md", "stage_02_shot_list.md", "stage_03_series_bible.md"],
        [
            "Read stage_01: Japanese RTL read path on this page (right to left, top to bottom)",
            "Open stage_02 row for S###: framing, beat, who is on screen",
            "Cross-check balloons on JPG or panel_s###jap.png",
            "Students: READ only — do not rewrite stage files unless mentor asks",
            "Report plain-English summary for beginners",
        ],
        "You understand which panel is S006 (etc.) before spending credits",
        "Reading page left-to-right, guessing dialogue without stage_02/stage_03",
    )

    skill_block(
        "manga-panel-crop-for-shots",
        "No panel_s###.png yet, or crop is wrong panel.",
        ["stage_02_shot_list.md", "002.jpg (manga page in Chapter-81)"],
        [
            "Read shot row in stage_02 (framing, page tier)",
            "Open manga JPG; crop ONE panel only",
            "Save panels/eng/ and panels/jap/ if dialogue",
            "Report file paths - no Fal image spend yet",
        ],
        "panels/eng/panel_s###.png",
        "Full-page upload, LTR crop order, two panels in one file",
    )

    skill_block(
        "qwen-frieren-dialogue (+ Fern scripts on S006)",
        "Any shot with speech balloons. ALWAYS before video. S006 needs BOTH speakers.",
        ["panel_s###jap.png", "stage_03_series_bible.md"],
        [
            "Read Japanese balloon text and speaker order",
            "S006: run Fern voice AND Frieren voice (two separate WAV files)",
            "Save under outputs/voice/final/S006/",
            "Report each file path and duration in seconds",
            "Suggest --start-sec for lip-sync timing",
        ],
        "outputs/voice/final/S006/*.wav (one per speaker)",
        "Only Frieren WAV, missing Fern, video before voice",
    )

    pdf.add_page()
    skill_block(
        "nano-banana-2-prompting",
        "Have grey manga crop; need colored anime still. Or S006A multi-ref insert.",
        ["panel_s###.png", "stage_02_shot_list.md", "stage_03_series_bible.md"],
        [
            "Read S### notes in stage_03 and fal_common.py prompt",
            "Run Nano Banana 2 image edit",
            "Save to Tests/; copy to Tests/Final/ when you approve",
            "For S006A: multi-ref from S005 Fern + S006 camp still",
        ],
        "Tests/Final/S###_....png",
        "Color bleed, halftone left in, changing other shots",
    )

    skill_block(
        "anime-scene-i2v-prompting",
        "Approved still in Tests/Final/; ready for motion.",
        ["S### still from Tests/Final (pick by name)", "stage_03_series_bible.md"],
        [
            "ALWAYS try Seedance 2.0 FIRST (project default)",
            "If Seedance policy fails OR MS two-face (S004, S006): use Kling",
            "Pick duration from voice WAV length (Kling 5s or 10s)",
            "Short motion prompt - locked camera",
        ],
        "outputs/video/S###_....mp4",
        "Kling without trying Seedance, still prompt pasted into video",
    )

    skill_block(
        "pixverse-lipsync",
        "Have video MP4 + voice WAV; need mouth animation.",
        ["S### video MP4 from outputs/video/", "speaker WAV from outputs/voice/final/S###/"],
        [
            "If two faces visible: mask/block non-speaking face first",
            "One PixVerse pass per speaker",
            "Set --start-sec so line starts when mouth should move",
            "Dual speaker: combine two passes + mux audio",
        ],
        "outputs/video/LipsyncTests/ or lipsync final",
        "Wrong mouth, both speakers in one pass, no face mask",
    )

    pdf.callout(
        "S006 example",
        "Fern line -> S006A clip + pixverse. Frieren lines -> S006 clip + mask Fern + pixverse.",
    )


def _s006_step(
    pdf: WorkbookPDF,
    num: str,
    title: str,
    skill: str,
    fal_credits: str,
    files_to_add: list[str],
    you_do: list[str],
    agent_does: list[str],
    checks: list[str],
    say_to_agent: str,
) -> None:
    if pdf.get_y() > 185:
        pdf.add_page()
    pdf.h2(f"Step {num} - {title}")
    pdf.labeled_field("Skill:", skill, value_bold=True)
    credit_color = (180, 60, 0) if "USES" in fal_credits else (0, 120, 0)
    pdf.labeled_field("Credits:", fal_credits, value_bold=True, color=credit_color)
    pdf.ln(1)
    _at_picker_list(pdf, files_to_add)
    pdf.body("What YOU do:")
    for line in you_do:
        pdf.bullet(line)
    pdf.body("What AGENT does:")
    for line in agent_does:
        pdf.bullet(line)
    pdf.body("Check before next step:")
    for line in checks:
        pdf.bullet(line)
    pdf.body("Tell Agent (example - use @ files you picked, not copied paths):")
    pdf.code_block(say_to_agent)


def _fill_s006_body(pdf: WorkbookPDF) -> None:
    _explain_what_project_does(pdf)
    _explain_shot_id_s006(pdf)

    pdf.h1("Before you start")
    pdf.bullet("Read Cursor Guide PDF (how to @ files and /skills)")
    pdf.bullet("Finished Setup PDF (ZIP, .env, mentor 002.jpg)")
    pdf.bullet("Cursor mode = Agent (not Ask)")
    pdf.bullet("Start a NEW chat for this lesson")
    _cursor_add_files_habit(pdf)

    pdf.h1("Story on page 002")
    pdf.figure(
        "Full manga page - find S006",
        S006_ASSETS["manga_002"],
        "S006 is bottom MIDDLE panel (5th in read order). Frieren at tree; Fern by campfire.",
        max_h=120,
    )

    pdf.h1("12-step workflow map")
    pdf.simple_table(
        ["Step", "Task", "Skill", "Credits"],
        [
            ["1", "Study page (RTL + S006)", SKILL_MANGA_STUDY, "FREE"],
            ["2", "Understand dialogue", SKILL_MANGA_STUDY, "FREE"],
            ["3", "Crop panel", "/manga-panel-crop-for-shots", "FREE"],
            ["4", "Voice BOTH speakers", "/qwen-frieren-dialogue", "FAL — Fern + Frieren"],
            ["5", "Plan duration", "(none)", "FREE"],
            ["6", "Still S006", "/nano-banana-2-prompting", "FAL"],
            ["7", "Still S006A", "/nano-banana-2-prompting", "FAL"],
            ["8", "Video S006", "/anime-scene-i2v-prompting", "FAL — Seedance first"],
            ["9", "Video S006A", "/anime-scene-i2v-prompting", "FAL — Seedance first"],
            ["10", "Lip-sync Fern", "/pixverse-lipsync", "FAL"],
            ["11", "Lip-sync Frieren", "/pixverse-lipsync", "FAL"],
            ["12", "Handoff", "(none)", "FREE"],
        ],
        [10, 36, 52, CONTENT_W - 98],
    )

    pdf.add_page()
    pdf.h1("Steps 1-3 - Find, understand, crop")
    _s006_step(
        pdf, "1", "Study page 002 — find S006 (RTL)",
        skill=SKILL_MANGA_STUDY,
        fal_credits=FAL_FREE,
        files_to_add=[
            "002.jpg",
            "stage_01_ingest.md",
            "stage_02_shot_list.md",
        ],
        you_do=[
            "Open 002.jpg in Photos or Cursor sidebar",
            "Read Agent answer: which panel is S006 on this page?",
        ],
        agent_does=[
            "Reads stage_01 RTL read path for page 002",
            "Maps panels to S002, S003... S006 in story order",
            "Points to bottom middle panel (tree + campfire)",
        ],
        checks=["You can point at S006 panel; you know it is 5th in read order"],
        say_to_agent=(
            f"{SKILL_MANGA_STUDY}\n"
            "Study page 002.jpg only. Read RTL panel order from stage_01 + stage_02.\n"
            "Where is shot S006? Explain in simple words for a beginner.\n"
            "READ only — do not edit stage files. No Fal API calls."
        ),
    )
    pdf.figure_pair(
        "Panel crops you will make",
        S006_ASSETS["panel_eng"],
        S006_ASSETS["panel_jap"],
        "panel_s006.png (picture layout)",
        "panel_s006jap.png (Japanese dialogue text)",
        "Eng crop = still input. Jap crop = voice text for Fern AND Frieren lines.",
        max_h=52,
    )
    _s006_step(
        pdf, "2", "Understand S006 dialogue",
        skill=SKILL_MANGA_STUDY,
        fal_credits=FAL_FREE,
        files_to_add=[
            "002.jpg",
            "panel_s006jap.png",
            "stage_01_ingest.md",
            "stage_02_shot_list.md",
            "stage_03_series_bible.md",
        ],
        you_do=["Read Agent answer", "Note: Fern speaks first, then Frieren"],
        agent_does=[
            "Uses stage_02 row + stage_03 for S006",
            "Lists BOTH speakers and JP balloon order",
            "Explains why S006A extra picture is needed for Fern lip-sync",
        ],
        checks=["Agent names Fern AND Frieren; mentions S006A"],
        say_to_agent=(
            f"{SKILL_MANGA_STUDY}\n"
            "Explain shot S006 only for a beginner.\n"
            "Use stage_02, stage_03, and the JP panel I picked.\n"
            "Who speaks first? Why do we need S006A?\n"
            "READ only. No Fal credits."
        ),
    )
    _s006_step(
        pdf, "3", "Crop the panel",
        skill="/manga-panel-crop-for-shots",
        fal_credits=FAL_FREE,
        files_to_add=["stage_02_shot_list.md", "002.jpg"],
        you_do=[
            "Allow Agent if it runs a local crop script",
            "In sidebar, open panels/eng/panel_s006.png — one panel only?",
            "Open panels/jap/panel_s006jap.png — can you read balloons?",
        ],
        agent_does=["Crops eng + jap PNGs for S006", "Reports paths"],
        checks=["Fern + Frieren visible; not mirrored; jap has dialogue"],
        say_to_agent=(
            "/manga-panel-crop-for-shots for S006 only. "
            "Crop eng and jap panel files for bottom middle panel on 002.jpg."
        ),
    )

    pdf.add_page()
    pdf.h1("Steps 4-5 - Voice for EVERY speaker, then timing")
    pdf.callout(
        "Two speakers = two WAV files",
        "S006 needs Fern voice AND Frieren voice. Missing Fern is a common mistake.",
    )
    _s006_step(
        pdf, "4", "Generate dialogue audio (Fern + Frieren)",
        skill="/qwen-frieren-dialogue",
        fal_credits=FAL_COST_VOICE,
        files_to_add=[
            "panel_s006jap.png",
            "stage_03_series_bible.md",
        ],
        you_do=[
            "Allow Fal when Agent asks — this step COSTS credits",
            "Confirm TWO WAV files: one Fern, one Frieren",
            "Write down seconds Agent reports for each",
        ],
        agent_does=[
            "Runs Fern dialogue generation (Fern line)",
            "Runs Frieren dialogue generation (long lines)",
            "Saves under outputs/voice/final/S006/",
        ],
        checks=[
            "Two WAV files exist (Fern + Frieren)",
            "Agent reported duration in seconds for EACH",
            "Done BEFORE any still or video step",
        ],
        say_to_agent=(
            "/qwen-frieren-dialogue for S006 only. "
            "Generate Qwen voice for EVERY speaker: Fern AND Frieren. "
            "Two separate WAV files. Report paths and seconds for each. "
            "Voice before video. I approve Fal credits for both speakers."
        ),
    )
    _s006_step(
        pdf, "5", "Plan video length and model",
        skill="(none — planning)",
        fal_credits=FAL_FREE,
        files_to_add=["Folder outputs/voice/final/S006/ (pick any WAV inside @ menu)"],
        you_do=[
            "Read plan — no new Fal spend on this step",
            "Remember: project tries Seedance FIRST; Kling is fallback",
        ],
        agent_does=[
            "Adds speech times + pauses",
            "Plans S006A for Fern line; S006 for Frieren lines",
            "Says try Seedance first; expect Kling 10s on S006 if MS two-face",
        ],
        checks=["Plan mentions Seedance first rule; both speakers timed"],
        say_to_agent=(
            "From the S006 voice WAV files in outputs/voice/final/S006/: plan clip duration. "
            "Try Seedance FIRST per project rule. "
            "S006 is MS two-face - note if Kling 10s is needed after Seedance attempt. "
            "Plan S006A for Fern lip-sync. No new Fal API calls."
        ),
    )

    pdf.add_page()
    pdf.h1("Steps 6-7 - Anime stills")
    _s006_step(
        pdf, "6", "Still S006 (main picture)",
        skill="/nano-banana-2-prompting",
        fal_credits=FAL_COST_STILL,
        files_to_add=["panel_s006.png", "stage_02_shot_list.md", "stage_03_series_bible.md"],
        you_do=[
            "Allow Fal — USES CREDITS",
            "QC result in Tests/ folder",
            "Ask Agent to copy to Tests/Final/ when good",
        ],
        agent_does=["Nano Banana color edit from manga crop", "Saves anime still"],
        checks=["No manga bubbles in picture; both characters clear"],
        say_to_agent=(
            "/nano-banana-2-prompting for S006 only. "
            "Colored anime still from panel_s006. Save to Tests/Final when QC passes."
        ),
    )
    pdf.figure_pair(
        "Grey crop to colored still",
        S006_ASSETS["panel_eng"],
        S006_ASSETS["still_s006"],
        "Input",
        "Output S006",
        "This still is the driver for video step 8.",
        max_h=55,
    )
    _s006_step(
        pdf, "7", "Still S006A (Fern close-up for lip-sync)",
        skill="/nano-banana-2-prompting",
        fal_credits=FAL_COST_STILL,
        files_to_add=[
            "Your S006 still from Tests/Final (pick in @ menu)",
            "Your S005 still from Tests/Final (Fern face reference)",
            "stage_03_series_bible.md",
        ],
        you_do=["Allow Fal — USES CREDITS", "Check Fern face forward, mouth visible"],
        agent_does=["Multi-ref insert — not from manga", "Saves S006A still"],
        checks=["Fern mouth clear; same camp look as S006"],
        say_to_agent=(
            "/nano-banana-2-prompting for S006A insert only. "
            "MCU Fern for lip-sync. Multi-ref from S006 camp still + S005 Fern still."
        ),
    )
    pdf.figure_pair(
        "Refs for S006A",
        S006_ASSETS["still_s005"],
        S006_ASSETS["still_s006a"],
        "S005 Fern face",
        "S006A output",
        "Bridge picture for Fern spoken line only.",
        max_h=55,
    )

    pdf.add_page()
    pdf.h1("Steps 8-9 - Video (Seedance FIRST, then Kling if needed)")
    pdf.callout(
        "Seedance first",
        "Always ask Agent to try Seedance 2.0 FIRST. Use Kling only if Seedance fails or MS two-face blocks it.",
    )
    _s006_step(
        pdf, "8", "Video S006 (main clip)",
        skill="/anime-scene-i2v-prompting",
        fal_credits=FAL_COST_VIDEO,
        files_to_add=["S006 still from Tests/Final", "stage_03_series_bible.md"],
        you_do=["Allow Fal — USES CREDITS", "Play MP4 — stable faces? ~10s?"],
        agent_does=[
            "Tries Seedance 2.0 FIRST",
            "If MS two-face / policy fail: Kling 10s with --anime-limited",
            "Duration from Frieren WAV length",
        ],
        checks=["Seedance attempted or Agent explains why Kling direct", "Covers long Frieren speech"],
        say_to_agent=(
            "/anime-scene-i2v-prompting for S006 only. "
            "Try Seedance 2.0 FIRST. If MS two-face or policy fail, use Kling 10s. "
            "Duration from Frieren WAV. Report MP4 path."
        ),
    )
    pdf.figure("S006 still drives video", S006_ASSETS["still_s006"], "Input picture for motion.", max_h=75)
    _s006_step(
        pdf, "9", "Video S006A (Fern hold)",
        skill="/anime-scene-i2v-prompting",
        fal_credits=FAL_COST_VIDEO,
        files_to_add=["S006A still from Tests/Final"],
        you_do=["Allow Fal — USES CREDITS"],
        agent_does=[
            "Try Seedance FIRST on Fern CU",
            "Fallback Kling ~5s if needed",
        ],
        checks=["Short clip for Fern line lip-sync"],
        say_to_agent=(
            "/anime-scene-i2v-prompting for S006A only. "
            "Try Seedance FIRST; Kling ~5s fallback. Locked camera."
        ),
    )
    pdf.figure("S006A still", S006_ASSETS["still_s006a"], "Fern CU for her spoken line.", max_h=72)

    pdf.add_page()
    pdf.h1("Steps 10-11 - Lip-sync")
    pdf.body("One mouth per PixVerse pass. Fern on S006A clip; Frieren on S006 clip (mask Fern).")
    _s006_step(
        pdf, "10", "Lip-sync Fern",
        skill="/pixverse-lipsync",
        fal_credits=FAL_COST_LIPSYNC,
        files_to_add=[
            "S006A video MP4 from outputs/video/",
            "Fern WAV from outputs/voice/final/S006/",
        ],
        you_do=["Allow Fal — USES CREDITS", "Pick files by name in @ — not copied paths"],
        agent_does=["PixVerse on Fern video + Fern WAV only"],
        checks=["Fern mouth moves; Fern line audible"],
        say_to_agent=(
            "/pixverse-lipsync for S006A Fern only. "
            "Use S006A video MP4 and Fern WAV. Single speaker."
        ),
    )
    _s006_step(
        pdf, "11", "Lip-sync Frieren (mask Fern on S006)",
        skill="/pixverse-lipsync",
        fal_credits=FAL_COST_LIPSYNC,
        files_to_add=[
            "S006 video MP4 from outputs/video/",
            "Frieren WAV from outputs/voice/final/S006/",
        ],
        you_do=["Allow Fal — USES CREDITS", "Confirm Agent masks Fern face first"],
        agent_does=["Mask Fern", "PixVerse Frieren mouth only"],
        checks=["Frieren mouth on S006 clip; not Fern speaking on wrong face"],
        say_to_agent=(
            "/pixverse-lipsync for S006 Frieren only. "
            "Mask Fern face. Use S006 video MP4 and Frieren WAV."
        ),
    )
    pdf.figure(
        "Optional S006B extend",
        S006_ASSETS["still_s006b"],
        "Extra hold frame if dialogue needs more time (in-between B).",
        max_h=65,
    )

    pdf.add_page()
    pdf.h1("Step 12 - Handoff and QC")
    pdf.body("Ask Agent to list every file it created. FREE — no credits.")
    pdf.body("Tell Agent:")
    pdf.code_block(
        "Handoff for S006 + S006A: list all WAV (Fern + Frieren), stills, "
        "videos, lip-sync MP4s with paths. Play order: S006A Fern then S006 Frieren."
    )
    pdf.h2("Final QC checklist")
    pdf.bullet("TWO voice WAVs (Fern + Frieren) before any video")
    pdf.bullet("Seedance was tried first on video steps (or Agent explained skip)")
    pdf.bullet("S006A: Fern lip-sync OK")
    pdf.bullet("S006: Frieren lip-sync OK (Fern masked)")
    pdf.callout("Done", "Same workflow for other shots — change S### ID and @ files.")


def _fill_setup_body(pdf: WorkbookPDF) -> None:
    _page_guide(pdf)
    pdf.callout("Start with Cursor Guide PDF", "Read cursor-student-workbook-en-cursor-guide.pdf before this booklet.")

    _explain_what_project_does(pdf)

    pdf.h1("0. Before you start")
    pdf.simple_table(
        ["Topic", "Rule"],
        [
            ["Copyright", "Do not publish full manga or commercial cuts without permission."],
            ["API key", "Your own fal.ai key. Never share .env file."],
            ["Clip length", "How long characters speak decides video length - not a fixed 1 minute."],
            ["Main tool", "Cursor Agent + /skills. You write prompts; Agent runs programs."],
            ["Cost", "Each AI call uses credits. Start with one shot (S006)."],
        ],
        [42, CONTENT_W - 42],
    )

    pdf.h1("1. What you need")
    pdf.simple_table(
        ["Item", "Who", "Why"],
        [
            ["Cursor app", "You", "Main workspace"],
            ["Python on PC", "Mentor", "Agent uses it - you do not type commands"],
            ["Project ZIP", "You", "Download from GitHub"],
            ["Manga JPGs", "Mentor", "002.jpg etc. not in ZIP"],
            ["Fal API key", "You", "Pays for image, video, voice"],
        ],
        [32, 28, CONTENT_W - 60],
    )

    pdf.add_page()
    pdf.h1("2. Get the project (no terminal)")
    pdf.h3("2.1 Download ZIP")
    pdf.bullet("GitHub page > green Code > Download ZIP")
    pdf.bullet("Extract to C:\\Work\\AI_Animation")
    pdf.bullet("Check: see Chapter-81, docs, scripts, .cursor folders")
    pdf.h3("2.2 Copy from mentor")
    pdf.bullet("Chapter-81/001.jpg - 018.jpg (need 002.jpg)")
    pdf.h3("2.3 Open in Cursor")
    pdf.bullet("File > Open Folder > AI_Animation")
    pdf.h3("2.4 API key")
    pdf.bullet("Copy .env.example to .env in file tree; paste FAL_KEY; Save")
    pdf.h3("2.5 Ask Agent once")
    pdf.body(f"Credits: {FAL_FREE} (local Python install — not Fal.ai)")
    pdf.code_block(
        "First-time setup. Create .venv, pip install -r requirements.txt.\n"
        "I will not use the terminal myself. Report success plainly."
    )

    _folder_guide_plain(pdf)

    pdf.add_page()
    pdf.pipeline_diagram()
    pdf.callout("Golden rule", "Make voice audio BEFORE choosing video length.")

    pdf.add_page()
    pdf.h1("5. Read manga right to left")
    pdf.body(
        "Use Agent with /manga-chapter-ingest-stages-1-3 to study each page: "
        "RTL order, shot IDs, and who speaks. Students READ stage files — mentors edit them."
    )
    manga_002 = resolve_manga_page_002()
    pdf.figure(
        "Full page 002.jpg",
        manga_002,
        "Read: S002 top -> S003 middle RIGHT -> S004 middle LEFT -> S005 bottom RIGHT -> S006 bottom middle.",
        max_h=195,
    )
    pdf.simple_table(
        ["Order", "Shot", "Where on page"],
        [
            ["1", "S002", "Top wide shot"],
            ["2", "S003", "Middle right"],
            ["3", "S004", "Middle left"],
            ["4", "S005", "Bottom right"],
            ["5", "S006", "Bottom middle - your first lesson"],
        ],
        [18, 22, CONTENT_W - 40],
    )

    _skills_workflow_detail(pdf)

    pdf.add_page()
    pdf.h1("Next step")
    pdf.body("When setup is done, open the S006 First Try booklet and follow every step.")
    pdf.body("PDF: docs/cursor-student-workbook-en-s006-first-try.pdf")


def build_cursor_guide_pdf() -> Path:
    return build_with_contents(
        booklet_title="Cursor Guide",
        cover_subtitle="How to use Cursor for this course",
        cover_tagline="@ files, /skills, Agent mode, and when Fal credits are spent.",
        body=_fill_cursor_guide_body,
        out_path=OUT_CURSOR,
    )


def build_setup_pdf() -> Path:
    return build_with_contents(
        booklet_title="Setup Booklet",
        cover_subtitle="Day 1  -  Install, folders, manga, skills",
        cover_tagline="No terminal. Use File Explorer, browser, and Cursor Agent.",
        body=_fill_setup_body,
        out_path=OUT_SETUP,
    )


def build_s006_pdf() -> Path:
    return build_with_contents(
        booklet_title="S006 First Try",
        cover_subtitle="Day 2  -  Your first complete shot",
        cover_tagline="12 steps with pictures: voice, stills, video, S006A, lip-sync.",
        body=_fill_s006_body,
        out_path=OUT_S006,
    )


def _fill_reference_body(pdf: WorkbookPDF) -> None:
    _page_guide(pdf)
    pdf.body(
        "Booklet 3 = skills workflow (main) + prompt templates + troubleshooting. "
        "New students: read Setup PDF then S006 PDF first."
    )
    _skills_workflow_full(pdf)

    pdf.add_page()
    pdf.h1("Pipeline overview")
    pdf.pipeline_diagram()
    pdf.callout("Voice first", "On dialogue shots, never pick video length before WAV seconds.")

    # --- Prompt templates ---
    pdf.add_page()
    pdf.h1("7. Prompt: anime still (Stage 4)")
    pdf.body("Every template below: pick files with @ first, then paste the prompt. No copied folder paths.")
    pdf.h3("7.1 Panel crop")
    _ref_prompt_block(
        pdf,
        ["stage_02_shot_list.md", "002.jpg"],
        "/manga-panel-crop-for-shots\n"
        "Crop panel_s003.png for S003 only. One panel on page 002.",
    )
    pdf.h3("7.2 Generate still")
    _ref_prompt_block(
        pdf,
        ["panel_s003.png", "stage_02_shot_list.md", "stage_03_series_bible.md"],
        "/nano-banana-2-prompting for S003\n"
        "Generate Stage 4 still for S003 only. Save to Tests/Final/ if QC passes.",
    )
    pdf.h3("7.4 In-between A (S006A insert)")
    _ref_prompt_block(
        pdf,
        ["S005 still from Tests/Final", "S006 still from Tests/Final", "stage_03_series_bible.md"],
        "/nano-banana-2-prompting for S006A\n"
        "MCU Fern for lip-sync bridge. S006A only.",
    )
    pdf.figure(FIGURES[1][0], FIGURES[1][1], FIGURES[1][2])

    # --- Section 8 ---
    pdf.add_page()
    pdf.h1("8. Prompt: video (Seedance first, then Kling)")
    pdf.simple_table(
        ["Try first", "Fall back to Kling when"],
        [
            ["Seedance 2.0", "Policy fail; MS two-face (S004, S006); lip-sync CU"],
            ["Kling 2.6 Pro", "Seedance failed; --anime-limited; in-between B"],
        ],
        [55, CONTENT_W - 55],
    )
    pdf.h3("8.2 Prompt - Seedance (try first)")
    _ref_prompt_block(
        pdf,
        ["S002 still from Tests/Final", "stage_02_shot_list.md", "stage_03_series_bible.md"],
        "/anime-scene-i2v-prompting for S002\n"
        "Try Seedance 2.0 FIRST. Report MP4. If policy fails, propose Kling.",
    )
    pdf.h3("8.3 Prompt - Kling (MS two-face)")
    pdf.code_block(
        "/anime-scene-i2v-prompting for S004\n"
        "MS two-face - route to Kling (not Seedance). Duration from WAV totals."
    )
    pdf.body("Motion prompts are SHORT. Agent runs scripts; you write prompts.")

    # --- Section 9 ---
    pdf.add_page()
    pdf.h1("9. Work with Cursor Agent")
    pdf.body(
        "Use Agent mode. Click @ to pick files by name; type /skill first. "
        "Agent runs scripts; you approve credits and QC."
    )
    pdf.callout(
        "Session order",
        "Analyze -> voice (WAV sec) -> duration -> still -> Seedance first / Kling -> /pixverse-lipsync with masks.",
    )
    pdf.body("Example S004 session - pick files with @ at each step:")
    _at_picker_list(
        pdf,
        [
            "panel_s004jap.png (step 1 - dialogue)",
            "stage_03_series_bible.md",
            "panel_s004.png, stills, video MP4, voice WAVs (later steps)",
        ],
    )
    pdf.code_block(
        "Shot S004 only. /skill each step.\n"
        "STEP 1: list speakers and JP lines from panel_s004jap\n"
        "STEP 2: /qwen-frieren-dialogue - WAV paths + seconds\n"
        "STEP 3: Seedance first unless MS two-face -> Kling\n"
        "STEP 4: /nano-banana-2-prompting still\n"
        "STEP 5: /anime-scene-i2v-prompting video\n"
        "STEP 6: /pixverse-lipsync mask both faces, combine"
    )
    pdf.simple_table(
        ["Task", "Skill + why"],
        [
            ["Study manga page", "manga-chapter-ingest-stages-1-3 - RTL + S### before crop"],
            ["Panel crops", "manga-panel-crop-for-shots - correct tier/order"],
            ["Anime still", "nano-banana-2-prompting - fal_common + panel path"],
            ["Video", "anime-scene-i2v-prompting - Seedance first routing"],
            ["Voice", "qwen-frieren-dialogue - voice BEFORE video length"],
            ["Lip-sync", "pixverse-lipsync - mask before PixVerse"],
        ],
        [50, CONTENT_W - 50],
    )
    pdf.callout("Good prompt", "/skill first. @ pick files by name. Voice first. Seedance first. S### only.")
    pdf.callout("Bad prompt", "5 second video (no dialogue). Whole chapter anime. Paste API keys.")

    # --- Section 10 dialogue-driven timing ---
    pdf.add_page()
    pdf.h1("10. Dialogue-driven timing")
    pdf.body("Seedance: 4-15s or auto. Kling: 5s or 10s. Choose AFTER Qwen WAV + pauses.")
    pdf.simple_table(
        ["Step", "Action"],
        [
            ["1", "Agent reads panels/jap + stage_03"],
            ["2", "/qwen-frieren-dialogue - WAV per speaker"],
            ["3", "Report WAV duration in seconds"],
            ["4", "Map to Seedance sec or Kling 5/10"],
            ["5", "If over cap: in-between B or compact dialogue"],
        ],
        [18, CONTENT_W - 18],
    )
    pdf.simple_table(
        ["Shot", "Duration driver", "Video model"],
        [
            ["S002", "Silent establish", "Seedance"],
            ["S004", "2 WAVs + pause", "Kling (MS two-face)"],
            ["S006A", "Fern ~2s line", "Kling on insert"],
            ["S006", "Frieren ~9.9s", "Kling 10s"],
        ],
        [28, 58, CONTENT_W - 86],
    )

    pdf.h2("10.5 In-between shots (two methods)")
    pdf.simple_table(
        ["Method", "When", "How"],
        [
            ["A - New frame", "Need lip-sync CU; no good mouth in panel", "Nano multi-ref e.g. S006A -> Kling 5s/10s"],
            ["B - Extend frame", "Hold same angle; bridge time", "Screenshot last Kling frame -> S006B +5s/10s"],
        ],
        [32, 52, CONTENT_W - 84],
    )
    pdf.code_block(
        "# A: /nano-banana-2-prompting for S006A (see Section 7.4)\n"
        "# B: /anime-scene-i2v-prompting for S006B - extend last frame +5s"
    )

    for title, path, cap in [FIGURES[0], FIGURES[3], FIGURES[4], FIGURES[5]]:
        pdf.figure(title, path, cap)

    pdf.h3("Assemble scene (prompt)")
    pdf.code_block(
        "Assemble page 002 camp S002->S006B in story order.\n"
        "Use lipsync/final clips. Concat with ffmpeg. Report total duration."
    )

    # --- Section 11-13 ---
    pdf.add_page()
    pdf.h1("11. Voice and lip-sync (REQUIRED)")
    pdf.callout(
        "Voice FIRST",
        "Generate Qwen WAV before video duration or model. Measure seconds, then Seedance/Kling, then PixVerse.",
    )
    pdf.h3("11.1 Prompt - voice / audio")
    _ref_prompt_block(
        pdf,
        ["panel_s006jap.png", "stage_03_series_bible.md"],
        "/qwen-frieren-dialogue for S006\n"
        "Generate ALL dialogue WAVs - Fern AND Frieren. Voice BEFORE video. Report paths + seconds.",
    )

    pdf.h3("11.2 Prompt - lip-sync (mask first)")
    pdf.body("PixVerse = one mouth per pass. Mask non-speaking face. Two speakers = two passes.")
    _ref_prompt_block(
        pdf,
        ["S004 video MP4 from outputs/video/", "voice WAVs from outputs/voice/final/S004/"],
        "/pixverse-lipsync for S004 dual dialogue\n"
        "1. Fern line - block Frieren - start ~1.0s\n"
        "2. Frieren line - block Fern - start ~3.1s\n"
        "3. Combine + mux with 0.6s pause",
    )
    pdf.figure(
        FIGURES[5][0],
        FIGURES[5][1],
        "S006A in-between (method A): Fern face clear for single-speaker PixVerse.",
    )

    pdf.add_page()
    pdf.h1("12. Prompt cookbook")
    pdf.simple_table(
        ["You want", "Skill + starter"],
        [
            ["Study page RTL", "/manga-chapter-ingest-stages-1-3 + @ pick 002.jpg + stage_01 + stage_02"],
            ["Panel crop", "/manga-panel-crop-for-shots + @ pick stage_02 + 002.jpg"],
            ["Anime still", "/nano-banana-2-prompting + @ pick panel + stage files"],
            ["Voice", "/qwen-frieren-dialogue + @ pick panel_s###jap + stage_03"],
            ["Video", "/anime-scene-i2v-prompting + @ pick still from Tests/Final"],
            ["Lip-sync", "/pixverse-lipsync + @ pick video MP4 + speaker WAV"],
            ["First panel", "Section 6 S006 full workflow"],
            ["Full shot", "Section 9.2 session prompt"],
        ],
        [42, CONTENT_W - 42],
    )
    pdf.body("Agent runs scripts in scripts/ - you do not type Python for production steps.")

    pdf.h1("13. Common problems")
    pdf.simple_table(
        ["Symptom", "Fix"],
        [
            ["Agent guesses dialogue", "/skill + @ pick panel_s###jap + stage_03"],
            ["Wrong layout / mirrored", "Re-crop panels/eng/panel_s###.png"],
            ["Seedance policy fail", "Expected on MS two-face - switch to Kling"],
            ["Wrong lip-sync mouth", "/pixverse-lipsync - mask; one pass per speaker"],
            ["Dialogue cut off", "Voice first - longer Seedance or Kling 10s; in-between B"],
            ["Missing FAL_KEY", "Copy .env.example to .env"],
        ],
        [65, CONTENT_W - 65],
    )

    pdf.h1("14. Four-week syllabus")
    pdf.simple_table(
        ["Week", "Deliverable"],
        [
            ["1", "Manual Section 2 setup + Section 6 on S006"],
            ["2", "S004: voice-first; Seedance try then Kling; dual lip-sync"],
            ["3", "S005-S006: voice-first + S006A in-between"],
            ["4", "Assemble page 002 - length from dialogue sum"],
        ],
        [22, CONTENT_W - 22],
    )

    # --- Cheat sheet back ---
    pdf.add_page()
    pdf.h1("Cheat sheet - use in Cursor")
    pdf.body("Pick files with @ (by name). Do not copy paths from this page.")
    pdf.set_fill_color(*CODE_BG)
    pdf.set_font("Courier", "", 8)
    cheat = (
        "AI_Animation - Shot S### only.\n"
        "Complete S006 First Try PDF if new.\n"
        "EVERY step: /skill-name first, then @ pick files by name.\n"
        "Start: /manga-chapter-ingest-stages-1-3 to study page RTL + S###\n"
        "Pick often: stage_01_ingest.md, stage_02_shot_list.md, panel_s###jap.png\n"
        "ORDER: analyze -> voice (WAV sec) -> duration -> still ->\n"
        "video (Seedance FIRST, Kling fallback) -> /pixverse-lipsync masks\n"
        "In-between: A=/nano-banana-2-prompting OR B=extend last frame\n"
        "Do not commit .env. Ask for handoff block when done."
    )
    pdf.multi_cell(CONTENT_W, 5.5, cheat, fill=True)
    pdf.ln(8)
    pdf.set_font("Helvetica", "", 10)
    pdf.body("Full markdown workbook: docs/cursor-student-workbook-en.md")
    pdf.body("Cantonese version: docs/cursor-student-workbook-yue.md")
    pdf.callout(
        "Further reading",
        "docs/stage5-image-to-video-fal.md  -  docs/qwen-voice-pipeline-formula.md  -  manga-to-anime-fal-stages.plan.md",
    )

def build_reference_pdf() -> Path:
    return build_with_contents(
        booklet_title="Full Reference",
        cover_subtitle="Skills workflow + prompts + troubleshooting",
        cover_tagline="Use after Setup and S006 PDFs. Skills guide is the main section.",
        body=_fill_reference_body,
        out_path=OUT,
    )


def build_all() -> list[Path]:
    paths = [
        build_cursor_guide_pdf(),
        build_setup_pdf(),
        build_s006_pdf(),
        build_reference_pdf(),
    ]
    return paths


if __name__ == "__main__":
    for path in build_all():
        print(f"Wrote: {path}")
