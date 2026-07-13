"""
Build print-friendly PDFs from the English student workbook.

Outputs (read in this order):
  docs/cursor-student-workbook-en-setup.pdf         Booklet 1 - setup, folders, manga
  docs/cursor-student-workbook-en-cursor-guide.pdf  Booklet 2 - how to use Cursor
  docs/cursor-student-workbook-en-s006-first-try.pdf  Booklet 3 - S006 walkthrough
  docs/cursor-student-workbook-en.pdf             Booklet 4 - skills workflow + reference
  docs/cursor-student-workbook-en-combined.pdf    All booklets 1-4 in order (print once)

Requires: pip install fpdf2 pypdf
"""

from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path

from fpdf import FPDF
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT_SETUP = ROOT / "docs" / "cursor-student-workbook-en-setup.pdf"
OUT_CURSOR = ROOT / "docs" / "cursor-student-workbook-en-cursor-guide.pdf"
OUT_S006 = ROOT / "docs" / "cursor-student-workbook-en-s006-first-try.pdf"
OUT = ROOT / "docs" / "cursor-student-workbook-en.pdf"  # full reference
OUT_COMBINED = ROOT / "docs" / "cursor-student-workbook-en-combined.pdf"

BOOKLET_PDFS_IN_ORDER = (OUT_SETUP, OUT_CURSOR, OUT_S006, OUT)

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
    "still_s005": ROOT / "Tests" / "Final" / "S005_nano-banana-2-edit_20260330_034325.png",
    "still_s006": ROOT / "Tests" / "Final" / "S006_nano-banana-2-edit_20260330_035743.png",
    "still_s006a": ROOT / "Tests" / "Final" / "S006A_nano-banana-2-edit_20260605_020608.png",
    "still_s006b": ROOT / "Tests" / "Final" / "S006B_nano-banana-2-edit_20260330_035743.png",
}

# Approved stills for figures (camp sequence page 002)
FIGURES: list[tuple[str, Path, str]] = [
    (
        "Fig 1  - S002 wide establish (Stage 4 still)",
        ROOT / "Tests" / "Final" / "S002_nano-banana-2-edit_20260326_094158.png",
        "Wide camp shot: party at fire. Good first motion test with Seedance or Kling.",
    ),
    (
        "Fig 2  - S003 squirrel messenger (Stage 4 still)",
        ROOT / "Tests" / "Final" / "S003_extendcampsquirrel_nano-banana-2-edit_20260326_150111.png",
        "Recommended first still for beginners  - one face + small critter.",
    ),
    (
        "Fig 3  - Manga panel crop -> anime still",
        ROOT / "panels" / "eng" / "panel_s003.png",
        "Left: greyscale manga crop (panels/eng/panel_s003.png). Upload this to Nano Banana 2 edit.",
    ),
    (
        "Fig 4  - S005 Fern close-up (lip-sync friendly)",
        ROOT / "Tests" / "Final" / "S005_nano-banana-2-edit_20260330_034325.png",
        "Face visible  - use for dialogue and PixVerse lip-sync practice.",
    ),
    (
        "Fig 5  - S006 camp debate (medium shot)",
        ROOT / "Tests" / "Final" / "S006_nano-banana-2-edit_20260330_035743.png",
        "Frieren at tree, Fern by fire. Lip-sync both speakers on one video; mask non-speaking face.",
    ),
    (
        "Fig 6  - S006B video extend (optional)",
        ROOT / "Tests" / "Final" / "S006B_nano-banana-2-edit_20260330_035743.png",
        "Hold same angle longer if speech needs more time — no separate extra picture.",
    ),
]

MARGIN = 16
CONTENT_W = 210 - 2 * MARGIN  # A4 mm
PAGE_BREAK_MARGIN = 16
ACCENT = (41, 98, 255)
ACCENT_DARK = (24, 52, 120)
CALLOUT_BG = (240, 245, 255)
CODE_BG = (245, 245, 245)
# Embed at print resolution (300 DPI at on-page mm size). Cap huge sources so PDFs stay emailable.
PRINT_IMAGE_DPI = 300
PRINT_JPEG_QUALITY = 92
PRINT_MAX_LONG_EDGE_PX = 2800


def _mm_to_px(mm: float, dpi: int = PRINT_IMAGE_DPI) -> int:
    return max(1, int(mm * dpi / 25.4))


def _prepare_image_for_pdf(path: Path, *, max_w_mm: float, max_h_mm: float) -> BytesIO:
    """Resize to print pixels for the on-page box; keep panels as PNG, photos as high-quality JPEG."""
    max_w_px = _mm_to_px(max_w_mm)
    max_h_px = _mm_to_px(max_h_mm)
    with Image.open(path) as im:
        src_mode = im.mode
        has_alpha = src_mode in ("RGBA", "LA") or (src_mode == "P" and "transparency" in im.info)
        if has_alpha:
            rgba = im.convert("RGBA")
            bg = Image.new("RGB", rgba.size, (255, 255, 255))
            bg.paste(rgba, mask=rgba.split()[-1])
            im = bg
        elif src_mode == "P":
            im = im.convert("RGB")
        elif src_mode == "L":
            pass
        else:
            im = im.convert("RGB")

        im.thumbnail((max_w_px, max_h_px), Image.Resampling.LANCZOS)
        if max(im.size) > PRINT_MAX_LONG_EDGE_PX:
            im.thumbnail((PRINT_MAX_LONG_EDGE_PX, PRINT_MAX_LONG_EDGE_PX), Image.Resampling.LANCZOS)

        buf = BytesIO()
        # Greyscale panel crops: PNG preserves line art; colour stills use JPEG.
        use_png = src_mode == "L" or (
            path.suffix.lower() == ".png" and max(im.size) <= 1400
        )
        if use_png:
            save_im = im if im.mode in ("L", "RGB") else im.convert("RGB")
            save_im.save(buf, format="PNG", optimize=True)
        else:
            if im.mode != "RGB":
                im = im.convert("RGB")
            im.save(
                buf,
                format="JPEG",
                quality=PRINT_JPEG_QUALITY,
                subsampling=0,
                optimize=True,
            )
        buf.seek(0)
        return buf


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
        self.set_auto_page_break(auto=True, margin=PAGE_BREAK_MARGIN)
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

    def new_page(self, *, section: str | None = None) -> None:
        """Start a new printed page (use for each major section / S006 step)."""
        if section:
            self.set_section(section)
        self.add_page()

    def _page_bottom(self) -> float:
        return 297 - PAGE_BREAK_MARGIN

    def ensure_space(self, min_mm: float) -> None:
        """Add a page break only when the remaining space is too small."""
        if self.get_y() > self._page_bottom() - min_mm:
            self.add_page()

    def _reserve_heading(
        self,
        text: str,
        *,
        font_pt: float,
        line_mm: float,
        before_mm: float,
        after_mm: float,
        min_follow_mm: float,
    ) -> None:
        """Keep headings off the page bottom — require room for title + follow-on content."""
        text = _pdf_text(text)
        self.set_font("Helvetica", "B", font_pt)
        line_count = len(self.multi_cell(CONTENT_W, line_mm, text, dry_run=True, output="LINES"))
        heading_mm = before_mm + line_count * line_mm + after_mm
        self.ensure_space(heading_mm + min_follow_mm)

    def h1(self, text: str, *, record_toc: bool = True, min_follow_mm: float = 48) -> None:
        text = _pdf_text(text)
        self._reserve_heading(
            text, font_pt=20, line_mm=9, before_mm=1, after_mm=2, min_follow_mm=min_follow_mm
        )
        if record_toc:
            self._toc.append((text, 1, self.page_no()))
        self.set_section(text)
        self.ln(1)
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(*ACCENT_DARK)
        self.multi_cell(CONTENT_W, 9, text)
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def h2(self, text: str, *, record_toc: bool = True, min_follow_mm: float = 38) -> None:
        text = _pdf_text(text)
        self._reserve_heading(
            text, font_pt=14, line_mm=7, before_mm=1, after_mm=1, min_follow_mm=min_follow_mm
        )
        if record_toc:
            self._toc.append((text, 2, self.page_no()))
        self.ln(1)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*ACCENT_DARK)
        self.multi_cell(CONTENT_W, 7, text)
        self.set_text_color(0, 0, 0)
        self.ln(1)

    def h3(self, text: str, *, record_toc: bool = False, min_follow_mm: float = 28) -> None:
        text = _pdf_text(text)
        self._reserve_heading(
            text, font_pt=11, line_mm=6, before_mm=1, after_mm=1, min_follow_mm=min_follow_mm
        )
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
            self.cell(title_w, 5.5, title, new_x="RIGHT", new_y="NEXT")
            self.set_x(MARGIN + CONTENT_W - 12)
            self.set_font("Helvetica", "B", 10)
            self.cell(12, 5.5, str(display_page), align="R", new_x="LMARGIN", new_y="NEXT")
            self.set_font("Helvetica", "", 10)
            if self.get_y() > 270:
                self.add_page()
                self.h2("Contents (continued)", record_toc=False)  # noqa: page break only
        self.ln(4)

    def body(self, text: str) -> None:
        text = _pdf_text(text)
        self.set_font("Helvetica", "", 10)
        self.multi_cell(CONTENT_W, 5.2, text)
        self.ln(1)

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
        self.set_font("Helvetica", "B", 10)
        title_lines = len(self.multi_cell(CONTENT_W, 7, f"  {title}", dry_run=True, output="LINES"))
        self.set_font("Helvetica", "", 9)
        body_lines = len(self.multi_cell(CONTENT_W, 5, f"  {text}", dry_run=True, output="LINES"))
        self.ensure_space(title_lines * 7 + body_lines * 5 + 6)
        y0 = self.get_y()
        self.set_fill_color(*CALLOUT_BG)
        self.set_font("Helvetica", "B", 10)
        self.set_x(MARGIN)
        self.multi_cell(CONTENT_W, 7, f"  {title}", fill=True)
        self.set_font("Helvetica", "", 9)
        self.set_x(MARGIN)
        self.multi_cell(CONTENT_W, 5, f"  {text}", fill=True)
        self.ln(2)
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
        self.ln(2)
        self.set_font("Helvetica", "", 10)

    def simple_table(self, headers: list[str], rows: list[list[str]], col_widths: list[float] | None = None) -> None:
        headers = [_pdf_text(h) for h in headers]
        rows = [[_pdf_text(c) for c in row] for row in rows]
        if col_widths is None:
            col_widths = [CONTENT_W / len(headers)] * len(headers)
        first_row_h = 7
        if rows:
            for i, cell in enumerate(rows[0]):
                nb = self.multi_cell(col_widths[i], 5, cell, dry_run=True, output="LINES")
                first_row_h = max(first_row_h, 5 * len(nb))
        self.ensure_space(7 + first_row_h + 12)
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
            row_h = 7
            for i, cell in enumerate(row):
                nb = self.multi_cell(col_widths[i], 5, cell, dry_run=True, output="LINES")
                row_h = max(row_h, 5 * len(nb))
            if self.get_y() > self._page_bottom() - row_h - 2:
                self.add_page()
            if fill:
                self.set_fill_color(248, 248, 248)
            else:
                self.set_fill_color(255, 255, 255)
            max_h = row_h
            y_row = self.get_y()
            x0 = self.get_x()
            for i, cell in enumerate(row):
                self.set_xy(x0 + sum(col_widths[:i]), y_row)
                self.multi_cell(col_widths[i], 5, cell, border=1, fill=True)
            self.set_xy(x0, y_row + max_h)
            fill = not fill
        self.ln(3)

    def _embed_image(
        self,
        path: Path,
        *,
        w: float,
        h: float,
        x: float | None = None,
        y: float | None = None,
    ) -> None:
        buf = _prepare_image_for_pdf(path, max_w_mm=w, max_h_mm=h)
        if x is None:
            self.image(buf, w=w, h=h)
        else:
            self.image(buf, x=x, y=y, w=w, h=h)

    def _fit_image_dims(self, path: Path, box_w: float, box_h: float) -> tuple[float, float, float]:
        """Return draw width, height, and left x to fit inside box_w x box_h (aspect preserved)."""
        with Image.open(path) as im:
            aspect = im.width / im.height
        box_aspect = box_w / box_h
        if aspect >= box_aspect:
            w = box_w
            h = box_w / aspect
        else:
            h = box_h
            w = box_h * aspect
        x = MARGIN + (box_w - w) / 2
        return w, h, x

    def figure_fill_page(
        self,
        title: str,
        path: Path,
        caption: str,
        *,
        page_break: bool = True,
        heading: str = "h2",
    ) -> None:
        """Place image as large as possible below title, down to near page bottom."""
        title, caption = _pdf_text(title), _pdf_text(caption)
        if not path.is_file():
            if page_break:
                self.new_page()
            if heading == "h1":
                self.h1(title)
            else:
                self.h2(title)
            self.body(f"[Image not found: {path.name}]")
            return
        if page_break:
            self.new_page()
        if heading == "h1":
            self.h1(title, min_follow_mm=50)
        else:
            self.h2(title, min_follow_mm=50)
        self.set_font("Helvetica", "I", 9)
        caption_h = 5 * len(
            self.multi_cell(CONTENT_W, 5, caption, dry_run=True, output="LINES")
        ) + 6
        box_h = self._page_bottom() - self.get_y() - caption_h
        w, h, x = self._fit_image_dims(path, CONTENT_W, max(box_h, 40))
        y = self.get_y()
        self._embed_image(path, x=x, y=y, w=w, h=h)
        self.set_y(y + h + 2)
        self.set_text_color(80, 80, 80)
        self.multi_cell(CONTENT_W, 5, caption)
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def figure(self, title: str, path: Path, caption: str, *, max_h: float = 72) -> None:
        title, caption = _pdf_text(title), _pdf_text(caption)
        if not path.is_file():
            self.h3(title)
            self.body(f"[Image not found: {path.name}]")
            return
        self.h3(title, min_follow_mm=max_h + 16)
        self._embed_image(path, w=CONTENT_W, h=max_h)
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
        title, caption = _pdf_text(title), _pdf_text(caption)
        left_label, right_label = _pdf_text(left_label), _pdf_text(right_label)
        self.h3(title, min_follow_mm=max_h + 22)
        half = (CONTENT_W - 4) / 2
        y0 = self.get_y()
        x0 = MARGIN
        for path, label, x in ((left, left_label, x0), (right, right_label, x0 + half + 4)):
            self.set_xy(x, y0)
            self.set_font("Helvetica", "B", 8)
            self.cell(half, 5, label)
            if path.is_file():
                self._embed_image(path, x=x, y=y0 + 5, w=half, h=max_h)
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
        self.ensure_space(66)
        boxes = [
            ("Step 1 Study", "JP balloons\n+ stage files"),
            ("Step 2 Voice", "Qwen TTS\nFIRST"),
            ("Step 3 Timing", "Measure WAV\npick duration"),
            ("Step 4 Still", "Nano Banana\nPNG"),
            ("Step 5 Video", "Seedance FIRST\nKling fallback"),
            ("Step 6 Lipsync", "Mask face\nPixVerse"),
            ("Step 7 Assemble", "Join clips\nwhen scene done"),
        ]
        bw = CONTENT_W / 4 - 3
        bh = 18
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
        self.set_y(y0 + rows_used * (bh + 8) + 2)
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
    final.new_page()
    final.render_table_of_contents(toc_snapshot, page_offset=toc_pages)
    final.new_page()
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
            ["1 Setup", "cursor-student-workbook-en-setup.pdf", "Day 1 - install project, folders, manga"],
            ["2 Cursor", "cursor-student-workbook-en-cursor-guide.pdf", "How to drag files, /skills, credits"],
            ["3 S006", "cursor-student-workbook-en-s006-first-try.pdf", "Day 2 - first full shot lesson"],
            ["4 Reference", "cursor-student-workbook-en.pdf", "Skills workflow + troubleshooting (after S006)"],
        ],
        [22, 68, CONTENT_W - 90],
    )
    pdf.body("Read booklets in order 1 then 2 then 3. Use booklet 4 when you need extra detail.")


def _explain_what_project_does(pdf: WorkbookPDF) -> None:
    pdf.h2("What can this project do?")
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
    pdf.h2("What is S006?")
    pdf.body(
        "S006 is the label for one manga panel on the camp page — the bottom-middle panel "
        "where Frieren stands by the tree and Fern is by the campfire. Both characters speak."
    )
    pdf.simple_table(
        ["ID", "What it is", "Story beat"],
        [
            ["S006", "Camp debate panel", "Frieren at tree; Fern by fire; BOTH speak"],
            ["S006B", "Optional video extend", "Same angle held longer if speech needs more time"],
        ],
        [22, 52, CONTENT_W - 74],
    )
    pdf.body(
        "Both characters speak. Fern faces away (voice-over only). Frieren gets lip-sync. "
        "If the clip is too short, extend the video — do not make a separate extra picture."
    )


def _cursor_add_files_habit(pdf: WorkbookPDF) -> None:
    pdf.h2("How to add files in Cursor (do this every step)")
    pdf.bullet("Open Agent chat (not Ask mode for production)")
    pdf.bullet("Type / and pick the SKILL first (e.g. /nano-banana-2-prompting)")
    pdf.bullet("From the LEFT sidebar, DRAG a file or folder into the chat box and drop it")
    pdf.bullet("Repeat drag-and-drop for each file Agent needs (manga page, notes, picture, etc.)")
    pdf.bullet("Describe files in plain English in your message — do not hunt for exact file names")
    pdf.bullet("Say one shot only: S006 only (never whole chapter)")
    pdf.callout("Habit", "Every message = /skill + drag files into chat + one shot ID + plain English request")


def _prompt_structure_guide(pdf: WorkbookPDF) -> None:
    pdf.h2("Prompt structure (copy this shape — fill in your words)")
    pdf.code_block(
        "Line 1: /skill-name\n"
        "\n"
        "Lines 2+: drag files from the left sidebar into chat (one drop per file)\n"
        "\n"
        "Then write in plain English:\n"
        "  - Shot ID only (e.g. S006 only)\n"
        "  - What you want Agent to do\n"
        "  - What to show you when finished\n"
        "\n"
        "Do NOT paste file names or folder paths from this PDF."
    )
    pdf.body("Filled examples (describe what you dragged - not technical names):")
    pdf.code_block(
        "Example A - understand the page (FREE, no Fal spend):\n"
        "/manga-chapter-ingest-stages-1-3\n"
        "\n"
        "[I dragged the camp manga page photo from Chapter-81]\n"
        "[I dragged the shot list and story notes from Chapter-81]\n"
        "\n"
        "S006 only. Help me read this page in Japanese manga order.\n"
        "Show me where the S006 panel is and who speaks. Explain only."
    )
    pdf.code_block(
        "Example B - make a moving clip (USES FAL CREDITS):\n"
        "/anime-scene-i2v-prompting\n"
        "\n"
        "[I dragged my approved anime picture for this shot]\n"
        "[I dragged the story notes for this shot]\n"
        "\n"
        "S006 only. Turn this still into a short video clip.\n"
        "When done, tell me where the video is saved so I can check it."
    )


def _drag_files_list(pdf: WorkbookPDF, files_plain: list[str]) -> None:
    """Plain-English list of what to drag from the sidebar into chat."""
    if not files_plain:
        return
    pdf.body("Drag into chat from the left sidebar:")
    for line in files_plain:
        pdf.bullet(line)


def _ref_prompt_block(pdf: WorkbookPDF, drag_plain: list[str], prompt: str) -> None:
    _drag_files_list(pdf, drag_plain)
    pdf.body("Tell Agent (plain English - see Cursor Guide prompt shape):")
    pdf.code_block(prompt)


def _fill_cursor_guide_body(pdf: WorkbookPDF) -> None:
    pdf.h1("Overview")
    pdf.callout("Booklet 2 of 4", "Read Setup PDF (booklet 1) before this guide.")
    pdf.h2("What is Cursor?")
    pdf.body(
        "Cursor is a code editor with an AI assistant (Agent). For this course you use Agent chat "
        "to ask for manga crops, pictures, voice, and video. Agent reads files you drag into chat and runs scripts."
    )

    pdf.h2("Open your project")
    pdf.body(
        "Cursor should already be on your laptop (download from cursor.com if your mentor installed it for you). "
        "No extra install steps in this booklet."
    )
    pdf.bullet("Launch Cursor from the Start menu")
    pdf.bullet("Menu File > Open Folder > select C:\\AI_Animation (see Setup booklet)")
    pdf.bullet("Left sidebar shows your project folders (Chapter-81, panels, docs, etc.)")

    pdf.h2("Agent mode vs Ask mode")
    pdf.simple_table(
        ["Mode", "Use for"],
        [
            ["Agent", "Production - crop, voice, stills, video (DEFAULT for this course)"],
            ["Ask", "Questions only - Agent will NOT run programs"],
        ],
        [28, CONTENT_W - 28],
    )

    pdf.h2("The chat box - your main tool")
    _cursor_add_files_habit(pdf)

    pdf.ensure_space(70)
    pdf.h1("Skills and prompts")
    pdf.body(
        "Type / in chat and choose a skill BEFORE you describe the task. "
        "Skills live in .cursor/skills/. They stop Agent from guessing wrong steps."
    )
    _prompt_structure_guide(pdf)

    pdf.ensure_space(60)
    pdf.h1("Permissions and credits")
    pdf.h2("When Agent asks permission")
    pdf.simple_table(
        ["Agent asks", "What it means", "You do"],
        [
            ["Run terminal command", "Local setup (venv, pip)", "Allow if mentor said setup is OK"],
            ["Fal / API call", "USES FAL CREDITS", "Allow only if you expect that step to cost money"],
            ["Read file", "Usually FREE", "Allow"],
        ],
        [38, 58, CONTENT_W - 96],
    )

    pdf.h2("Credit cheat sheet")
    pdf.simple_table(
        ["Step", "Credits?"],
        [
            ["Explain shot, plan timing", "FREE"],
            ["Crop panel (local)", "FREE"],
            ["Qwen voice WAV", "USES CREDITS - each speaker = separate call"],
            ["Anime still (Nano Banana)", "USES CREDITS"],
            ["Video (Seedance or Kling)", "USES CREDITS - try Seedance first"],
            ["PixVerse lip-sync", "USES CREDITS - one pass per speaker"],
        ],
        [58, CONTENT_W - 58],
    )

    pdf.h2("Next booklet", min_follow_mm=20)
    pdf.body("Next: S006 First Try PDF (booklet 3). Reference PDF (booklet 4) is optional extra detail.")


def _folder_guide_plain(pdf: WorkbookPDF) -> None:
    pdf.h1("3. What goes where")
    pdf.body(
        "Three groups — not everything comes from GitHub. "
        "The ZIP has tools and docs; your mentor copies manga and voice files; you create secrets and outputs on this PC."
    )
    pdf.h3("Group A — inside the GitHub ZIP", min_follow_mm=40)
    pdf.simple_table(
        ["Path", "What it is"],
        [
            ["scripts/", "Programs Agent runs (you do not edit these)"],
            ["docs/", "Workbooks and how-to guides"],
            [".cursor/skills/", "Agent checklists — type /skill in chat"],
            [".env.example", "Template — copy to .env in step 2.4"],
            ["requirements.txt", "Python packages list for setup"],
        ],
        [40, CONTENT_W - 40],
    )
    pdf.h3("Group B — mentor copies in (USB or shared drive)", min_follow_mm=40)
    pdf.simple_table(
        ["Path", "What it is"],
        [
            ["Chapter-81/", "Manga JPGs (002.jpg …) + stage_01–03 story notes"],
            ["panels/eng/ and panels/jap/", "Panel crops per shot (optional if Agent crops)"],
            ["Voice Reference/", "Qwen voice reference clips (.wav + .txt)"],
        ],
        [48, CONTENT_W - 48],
    )
    pdf.h3("Group C — you create on this laptop", min_follow_mm=40)
    pdf.simple_table(
        ["Path", "What it is"],
        [
            [".env", "Your FAL_KEY (never share)"],
            [".venv/", "Python environment (Agent creates in step 2.5)"],
            ["Tests/", "Anime stills Agent generates"],
            ["outputs/", "Voice WAVs, videos, lip-sync clips"],
        ],
        [40, CONTENT_W - 40],
    )
    pdf.callout("You do not open scripts/", "Cursor Agent runs programs. You write prompts and drag files into chat.")


def _skills_workflow_detail(pdf: WorkbookPDF) -> None:
    """Short skills intro for Setup booklet."""
    pdf.h2("6. Skills - quick intro")
    pdf.body("Type /skill-name in Cursor. See Full Reference PDF for complete skills workflow.")
    pdf.code_block(
        "0. /manga-chapter-ingest-stages-1-3  (study page RTL + shot IDs - FREE)\n"
        "1. /manga-panel-crop-for-shots\n"
        "2. /qwen-frieren-dialogue  (voice BEFORE video)\n"
        "3. /nano-banana-2-prompting\n"
        "4. /anime-scene-i2v-prompting\n"
        "5. /pixverse-lipsync"
    )
    pdf.callout(
        "Study the page first",
        "Before cropping, drag the manga page photo and use manga-chapter-ingest. The skill reads story notes for you.",
    )


def _skills_workflow_full(pdf: WorkbookPDF) -> None:
    """Full skills workflow for Reference booklet."""
    pdf.body(
        "Skills are checklists in .cursor/skills/. They tell Cursor Agent which files to read "
        "and which step comes next. Use them on EVERY production message."
    )

    pdf.h2("Golden rules")
    pdf.bullet("Drag files from the left sidebar into chat - describe them in plain English")
    pdf.bullet("Type /skill-name at the start of your message")
    pdf.bullet("Say one shot only: S006 only - never whole chapter")
    pdf.bullet("Voice audio BEFORE video length on any dialogue shot")
    pdf.bullet("Ingest skill reads story notes in the project - you do not hunt for shot-list files")

    pdf.h2("Three workflow paths")
    pdf.simple_table(
        ["Shot type", "Example", "Skills order"],
        [
            ["Silent panel", "S002 wide", "study page -> crop -> still -> video"],
            ["One speaker", "S005 Fern", "study page -> crop -> voice -> still -> video -> lipsync"],
            ["Two speakers", "S006 debate", "study page -> crop -> voice -> still -> video (+ extend) -> Frieren lip-sync"],
        ],
        [28, 28, CONTENT_W - 56],
    )

    pdf.new_page()
    pdf.h2("Production skills (use in this order)")
    pdf.body(
        "Type /skill-name first, then drag files from the left sidebar. "
        "One shot only (e.g. S006 only). Never skip a row on dialogue shots."
    )
    pdf.simple_table(
        ["#", "/skill", "Drag into chat", "You get", "Remember"],
        [
            [
                "1",
                "manga-chapter-ingest-stages-1-3",
                "manga page photo",
                "RTL order + S###",
                "Study BEFORE crop",
            ],
            [
                "2",
                "manga-panel-crop-for-shots",
                "full manga page",
                "panel_s###.png",
                "ONE panel only",
            ],
            [
                "3",
                "qwen-frieren-dialogue",
                "Voice Ref + JP panel",
                "voice WAV clips",
                "BEFORE video length",
            ],
            [
                "4",
                "nano-banana-2-prompting",
                "English panel crop",
                "Tests/Final/ still",
                "QC still first",
            ],
            [
                "5",
                "anime-scene-i2v-prompting",
                "still + voice clips",
                "video .mp4",
                "Seedance first",
            ],
            [
                "6",
                "pixverse-lipsync",
                "video + speaker WAV",
                "lipsync .mp4",
                "Mask other face",
            ],
        ],
        [8, 56, 32, 30, CONTENT_W - 126],
    )

    pdf.callout(
        "S006 example",
        "Fern faces away (voice only). One video + extend if needed; Frieren lip-sync only.",
    )


def _s006_step_content(
    pdf: WorkbookPDF,
    skill: str,
    fal_credits: str,
    files_to_drag: list[str],
    you_do: list[str],
    agent_does: list[str],
    checks: list[str],
    say_to_agent: str,
) -> None:
    pdf.labeled_field("Skill:", skill, value_bold=True)
    credit_color = (180, 60, 0) if "USES" in fal_credits else (0, 120, 0)
    pdf.labeled_field("Credits:", fal_credits, value_bold=True, color=credit_color)
    pdf.ln(1)
    _drag_files_list(pdf, files_to_drag)
    pdf.body("What YOU do:")
    for line in you_do:
        pdf.bullet(line)
    pdf.body("What AGENT does:")
    for line in agent_does:
        pdf.bullet(line)
    pdf.body("Check before next step:")
    for line in checks:
        pdf.bullet(line)
    pdf.body("Tell Agent (example - drag files first, then your words):")
    pdf.code_block(say_to_agent)


def _s006_step_page(
    pdf: WorkbookPDF,
    num: str,
    title: str,
    *,
    skill: str,
    fal_credits: str,
    files_to_drag: list[str],
    you_do: list[str],
    agent_does: list[str],
    checks: list[str],
    say_to_agent: str,
    callout: tuple[str, str] | None = None,
    figure_pair: tuple[str, Path, Path, str, str, str] | None = None,
    figure: tuple[str, Path, str] | None = None,
    figure_pair_h: float = 40,
    figure_h: float = 48,
    page_break: bool = True,
    heading: str = "h1",
) -> None:
    if page_break:
        pdf.new_page()
    step_title = f"Step {num} - {title}"
    if heading == "h2":
        pdf.h2(step_title)
    else:
        pdf.h1(step_title)
    if callout:
        pdf.callout(callout[0], callout[1])
    _s006_step_content(
        pdf,
        skill,
        fal_credits,
        files_to_drag,
        you_do,
        agent_does,
        checks,
        say_to_agent,
    )
    if figure_pair:
        title_fp, left, right, left_lbl, right_lbl, cap = figure_pair
        pdf.figure_pair(title_fp, left, right, left_lbl, right_lbl, cap, max_h=figure_pair_h)
    if figure:
        pdf.figure(figure[0], figure[1], figure[2], max_h=figure_h)


def _fill_s006_body(pdf: WorkbookPDF) -> None:
    pdf.h1("Overview")
    pdf.callout("Booklet 3 of 4", "Each workflow step starts on its own page. Drag files into chat - see Cursor Guide.")
    pdf.simple_table(
        ["Step", "Task", "Credits"],
        [
            ["1", "Study page - find S006", "FREE"],
            ["2", "Understand dialogue", "FREE"],
            ["3", "Crop panel from full page", "FREE"],
            ["4", "Voice BOTH speakers", "FAL"],
            ["5", "Still S006 (Nano Banana)", "FAL"],
            ["6", "Video (+ extend if short)", "FAL"],
            ["7", "Lip-sync Frieren only", "FAL"],
            ["8", "Handoff", "FREE"],
        ],
        [12, 58, CONTENT_W - 70],
    )
    pdf.h2("Before you start")
    pdf.bullet("Finished Setup PDF (booklet 1) and Cursor Guide PDF (booklet 2)")
    pdf.bullet("Mentor copied camp manga page + Voice Reference folder (3 main characters)")
    pdf.bullet("Cursor mode = Agent (not Ask); start a NEW chat for this lesson")
    pdf.figure_fill_page(
        "Camp page 002 - where is S006?",
        S006_ASSETS["manga_002"],
        "S006 = bottom MIDDLE panel (5th in read order).",
    )
    _explain_shot_id_s006(pdf)
    pdf.callout(
        "Fern faces away",
        "Fern is not facing the camera. Generate her voice clip; skip lip-sync on Fern.",
    )

    _s006_step_page(
        pdf, "1", "Study page 002 - find S006 (RTL)",
        skill=SKILL_MANGA_STUDY,
        fal_credits=FAL_FREE,
        files_to_drag=["The camp manga page photo (from Chapter-81 folder)"],
        you_do=[
            "Drag the full page into chat - ingest skill finds story notes for you",
            "Read Agent answer: which panel is S006 on this page?",
        ],
        agent_does=[
            "Reads story notes already in the project",
            "Explains Japanese read order on this page",
            "Points to bottom middle panel (tree + campfire)",
        ],
        checks=["You can point at S006 panel; you know it is 5th in read order"],
        say_to_agent=(
            f"{SKILL_MANGA_STUDY}\n\n"
            "[I dragged the camp manga page photo]\n\n"
            "S006 only. Help me read this page in Japanese manga order.\n"
            "Show me where the S006 panel is. Explain only - no Fal credits."
        ),
    )
    _s006_step_page(
        pdf, "2", "Understand S006 dialogue",
        skill=SKILL_MANGA_STUDY,
        fal_credits=FAL_FREE,
        files_to_drag=["The camp manga page photo (same page as step 1)"],
        you_do=["Read Agent answer", "Note: Fern speaks first, then Frieren"],
        agent_does=[
            "Reads shot notes from the project automatically",
            "Lists BOTH speakers and line order",
            "Quotes Japanese dialogue from the balloons",
        ],
        checks=[
            "Agent names Fern AND Frieren; who speaks first is clear",
            "Agent notes Fern faces away - voice only, no lip-sync",
        ],
        say_to_agent=(
            f"{SKILL_MANGA_STUDY}\n\n"
            "[I dragged the camp manga page photo]\n\n"
            "S006 only. Who speaks and what do they say?\n"
            "Explain for a beginner. No Fal credits."
        ),
    )
    _s006_step_page(
        pdf, "3", "Crop the S006 panel from the full page",
        skill="/manga-panel-crop-for-shots",
        fal_credits=FAL_FREE,
        files_to_drag=["The camp manga page photo (full page - not a small crop yet)"],
        you_do=[
            "Allow Agent if it runs a local crop script",
            "After crop: open panels folder - small S006 picture + JP version",
            "Check both characters visible and JP balloons readable",
        ],
        agent_does=[
            "Cuts the S006 rectangle from the full page",
            "Saves English-layout crop + Japanese-balloon crop",
        ],
        checks=["Two panel images exist; Fern + Frieren visible; not mirrored"],
        say_to_agent=(
            "/manga-panel-crop-for-shots\n\n"
            "[I dragged the camp manga page photo]\n\n"
            "S006 only. Crop the bottom-middle panel from this full page.\n"
            "Make English and Japanese panel images."
        ),
    )

    _s006_step_page(
        pdf, "4", "Generate dialogue audio (Fern + Frieren)",
        skill="/qwen-frieren-dialogue",
        fal_credits=FAL_COST_VOICE,
        files_to_drag=[
            "Voice Reference folder (mentor - Frieren, Fern, Stark)",
            "Japanese S006 panel crop (speech balloons)",
        ],
        you_do=[
            "Allow Fal when Agent asks - this step COSTS credits",
            "Confirm TWO voice clips: one Fern, one Frieren",
            "Ask Agent how long each clip plays - video length depends on this",
        ],
        agent_does=[
            "Uses mentor voice references for character timbre",
            "Generates Fern line and Frieren lines as separate clips",
            "Saves under outputs/voice/final/S006/",
            "Tells you how long each clip is",
        ],
        checks=[
            "Two voice clips exist (Fern + Frieren)",
            "You know which clip is longer (usually Frieren)",
            "Done BEFORE still or video steps",
        ],
        say_to_agent=(
            "/qwen-frieren-dialogue\n\n"
            "[I dragged Voice Reference folder]\n"
            "[I dragged the Japanese S006 panel crop]\n\n"
            "S006 only. Make voice for Fern AND Frieren - two separate clips.\n"
            "Tell me how long each clip plays. I approve Fal credits."
        ),
        callout=(
            "Mentor voice pack",
            "Your teacher provides Voice Reference/ for Frieren, Fern, and Stark. "
            "S006 needs Fern voice AND Frieren voice - two separate clips.",
        ),
    )
    _s006_step_page(
        pdf, "5", "Still S006 (colored anime picture)",
        skill="/nano-banana-2-prompting",
        fal_credits=FAL_COST_STILL,
        files_to_drag=["English S006 panel crop (from step 3)"],
        you_do=[
            "Allow Fal - USES CREDITS",
            "QC the picture in Tests/ folder",
            "Ask Agent to save a good one as your approved still",
        ],
        agent_does=["Colors the manga crop into anime style", "Saves still image"],
        checks=["No manga speech bubbles in picture; both characters clear"],
        say_to_agent=(
            "/nano-banana-2-prompting\n\n"
            "[I dragged the English S006 panel crop]\n\n"
            "S006 only. Make a colored anime still. Save when it looks good."
        ),
        figure_pair=(
            "Example - grey manga crop to Nano Banana still",
            S006_ASSETS["panel_eng"],
            S006_ASSETS["still_s006"],
            "Manga panel crop",
            "Colored anime still",
            "Left = input crop. Right = Nano Banana output (your still for video).",
        ),
        figure_pair_h=44,
    )

    _s006_step_page(
        pdf, "6", "Video S006 - extend if speech is longer than clip",
        skill="/anime-scene-i2v-prompting",
        fal_credits=FAL_COST_VIDEO,
        files_to_drag=[
            "Approved S006 anime still (from step 5)",
            "Both voice clips from step 4",
        ],
        you_do=[
            "Allow Fal - USES CREDITS",
            "Play MP4 - does it cover both speakers?",
            "If too short: ask Agent to extend the same video (hold camera)",
        ],
        agent_does=[
            "Makes video from still; length fits voice clips",
            "Tries Seedance first; Kling if needed",
            "Can extend last frame if dialogue needs more time (S006B)",
            "Muxes Fern voice as audio only (she faces away - no mouth sync)",
        ],
        checks=[
            "One S006 video covers the scene",
            "Extended if speech was longer than first clip",
            "Fern line is audible (voice-over, not lip-synced)",
        ],
        say_to_agent=(
            "/anime-scene-i2v-prompting\n\n"
            "[I dragged my approved S006 still]\n"
            "[I dragged both voice clips]\n\n"
            "S006 only. Turn this still into video long enough for both voices.\n"
            "Extend the clip if speech does not fit. Layer Fern audio (no lip-sync - she faces away).\n"
            "Tell me where the video is saved."
        ),
        figure=(
            "S006B extend - hold same angle longer",
            S006_ASSETS["still_s006b"],
            "If the first clip is too short, extend from the last frame instead of making a new picture.",
        ),
        figure_h=34,
    )

    _s006_step_page(
        pdf, "7", "Lip-sync Frieren only",
        skill="/pixverse-lipsync",
        fal_credits=FAL_COST_LIPSYNC,
        files_to_drag=[
            "S006 video from step 6",
            "Frieren voice clip from step 4",
        ],
        you_do=[
            "Allow Fal - USES CREDITS",
            "Play result - Frieren mouth moves on her lines",
            "Fern line should already be heard from step 6 (no lip-sync on Fern)",
        ],
        agent_does=[
            "PixVerse on Frieren mouth + Frieren voice only",
            "Leaves Fern as-is (back turned, voice already in clip)",
        ],
        checks=[
            "Frieren mouth syncs on her dialogue",
            "Fern line still audible without mouth movement",
        ],
        say_to_agent=(
            "/pixverse-lipsync\n\n"
            "[I dragged the S006 video]\n"
            "[I dragged Frieren voice clip]\n\n"
            "S006 only. Lip-sync Frieren only. Fern faces away - do not lip-sync Fern."
        ),
        callout=(
            "Skip Fern lip-sync",
            "In this panel Fern faces away from the camera. Voice only for Fern; one PixVerse pass for Frieren.",
        ),
    )

    pdf.h2("Step 8 - Handoff and QC", min_follow_mm=42)
    pdf.body("Ask Agent to list every file it created. FREE - no credits.")
    pdf.code_block(
        "S006 handoff: list voice clips (Fern + Frieren), still, video, and final lip-sync clip.\n"
        "Tell me where each file is saved so I can find them in the sidebar."
    )
    pdf.body("Final QC checklist:")
    pdf.bullet("TWO voice clips (Fern + Frieren) before video")
    pdf.bullet("One S006 video - extended if needed; Fern audio layered")
    pdf.bullet("Frieren lip-sync OK")
    pdf.bullet("No Fern lip-sync (faces away from camera)")
    pdf.callout("Done", "Same workflow for other shots - change S### ID and drag the right files.")
    pdf.h2("Next booklet", min_follow_mm=20)
    pdf.body("Optional: Full Reference PDF (booklet 4) for extra skills detail and troubleshooting.")
    pdf.body("PDF: docs/cursor-student-workbook-en.pdf")


def _fill_setup_body(pdf: WorkbookPDF) -> None:
    pdf.h1("Overview")
    _page_guide(pdf)
    pdf.callout("Booklet 1 of 4", "You are reading Setup first. Next: Cursor Guide PDF, then S006 First Try.")
    _explain_what_project_does(pdf)

    pdf.new_page()
    pdf.h2("0. Before you start")
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

    pdf.h2("1. What you need")
    pdf.simple_table(
        ["Item", "Who", "Why"],
        [
            ["Cursor app", "You", "Main workspace"],
            ["Python on PC", "Mentor", "Agent uses it - you do not type commands"],
            ["Project ZIP", "You", "Download from GitHub"],
            ["Manga JPGs", "Mentor", "002.jpg etc. not in ZIP"],
            ["Voice Reference", "Mentor", "Frieren, Fern, Stark voice timbre"],
            ["Fal API key", "You", "Pays for image, video, voice"],
        ],
        [32, 28, CONTENT_W - 60],
    )

    pdf.h1("2. Get the project (no terminal)")
    pdf.h3("2.1 Download ZIP", min_follow_mm=32)
    pdf.bullet("GitHub page > green Code > Download ZIP")
    pdf.bullet("Open Downloads in File Explorer > right-click the ZIP > Extract All")
    pdf.bullet("Destination folder: C:\\  (type C:\\ only - the C: drive root, not a subfolder)")
    pdf.bullet("After extract you get C:\\AI_Animation-main — rename that folder to AI_Animation")
    pdf.bullet("Final project path: C:\\AI_Animation")
    pdf.bullet("Check inside: docs, scripts, .cursor, README.md (Chapter-81 is NOT in the ZIP - step 2.2)")
    pdf.h3("2.2 Copy from mentor", min_follow_mm=32)
    pdf.bullet("Copy mentor USB folder Chapter-81 into C:\\AI_Animation\\Chapter-81")
    pdf.bullet("Need 001.jpg - 018.jpg (002.jpg for the S006 lesson)")
    pdf.bullet("Copy Voice Reference/ — voice timbre for Frieren, Fern, Stark (required for dialogue)")
    pdf.bullet("Optional: pre-made panels/ crops")
    pdf.h3("2.3 Open in Cursor", min_follow_mm=18)
    pdf.bullet("File > Open Folder > C:\\AI_Animation")
    pdf.h3("2.4 API key", min_follow_mm=18)
    pdf.bullet("Copy .env.example to .env in file tree; paste FAL_KEY; Save")
    pdf.h3("2.5 Ask Agent once", min_follow_mm=28)
    pdf.body(f"Credits: {FAL_FREE} (local Python install — not Fal.ai)")
    pdf.code_block(
        "First-time setup. Create .venv, pip install -r requirements.txt.\n"
        "I will not use the terminal myself. Report success plainly."
    )

    pdf.ensure_space(80)
    _folder_guide_plain(pdf)

    pdf.ensure_space(90)
    pdf.h1("4. Production steps (in order)")
    pdf.pipeline_diagram()
    pdf.simple_table(
        ["Step", "You do (via Agent)", "Output"],
        [
            ["1 Study", "Read JP balloons + stage_02 / stage_03", "Shot plan in chat"],
            ["2 Voice", "Qwen TTS - one clip per speaker", "outputs/voice/final/S###/"],
            ["3 Timing", "Add speech + pauses; pick video seconds", "Duration notes"],
            ["4 Still", "Nano Banana from panel crop", "Tests/Final/S###.png"],
            ["5 Video", "Seedance first; Kling if needed", "outputs/video/S###.mp4"],
            ["6 Lip-sync", "PixVerse per speaker; mask other face", "outputs/video/ (lipsync)"],
            ["7 Assemble", "Join finished shots into one scene", "Scene .mp4"],
        ],
        [22, 58, CONTENT_W - 80],
    )
    pdf.callout("Golden rule", "Step 2 Voice BEFORE Step 5 Video length.")

    pdf.ensure_space(100)
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
        max_h=88,
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
    pdf.h2("Next booklet", min_follow_mm=20)
    pdf.body("When setup is done, open Cursor Guide PDF (booklet 2), then S006 First Try (booklet 3).")


def build_cursor_guide_pdf() -> Path:
    return build_with_contents(
        booklet_title="Cursor Guide",
        cover_subtitle="How to use Cursor for this course",
        cover_tagline="Drag files into chat, /skills, Agent mode, and when Fal credits are spent.",
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
        cover_tagline="8 steps with pictures: voice, Nano Banana still, video extend, Frieren lip-sync.",
        body=_fill_s006_body,
        out_path=OUT_S006,
    )


def _fill_reference_body(pdf: WorkbookPDF) -> None:
    pdf.h1("Overview")
    _page_guide(pdf)
    pdf.body(
        "Booklet 4 = skills workflow + prompt templates + troubleshooting. "
        "Read booklets 1-3 before this one."
    )

    pdf.ensure_space(60)
    pdf.h1("Skills workflow")
    _skills_workflow_full(pdf)

    pdf.new_page(section="Pipeline overview")
    pdf.h1("Pipeline overview")
    pdf.pipeline_diagram()
    pdf.callout("Voice first", "On dialogue shots, never pick video length before voice clips.")

    pdf.h2("7-8. Prompts: still and video")
    pdf.body("Drag files first; /skill then plain English (see Cursor Guide). Seedance first; Kling if policy fail, MS two-face, or lip-sync CU.")
    pdf.simple_table(
        ["#", "Drag", "Skill + action"],
        [
            ["7.1", "full manga page", "/manga-panel-crop-for-shots - S003 crop one panel"],
            ["7.2", "panel crop", "/nano-banana-2-prompting - S003 colored anime still"],
            ["7.3", "video + voices", "/anime-scene-i2v-prompting - S006 extend clip, same angle"],
            ["8.1", "approved still", "/anime-scene-i2v-prompting - S002 Seedance short motion"],
            ["8.2", "still + voices", "/anime-scene-i2v-prompting - S004 Kling MS two-face"],
        ],
        [14, 38, CONTENT_W - 52],
    )

    pdf.new_page(section="9. Work with Cursor Agent")
    pdf.h1("9. Work with Cursor Agent")
    pdf.body(
        "Use Agent mode. Drag files into chat; type /skill first. "
        "Agent runs scripts; you approve credits and QC."
    )
    pdf.callout(
        "Session order",
        "Study page -> voice clips -> still -> video (extend if short) -> lip-sync with masks.",
    )
    pdf.body("Example S004 session — drag files at each step:")
    _drag_files_list(
        pdf,
        [
            "Japanese panel crop (dialogue)",
            "Voice Reference folder",
            "English panel crop, approved still, video, voice clips (later steps)",
        ],
    )
    pdf.code_block(
        "Shot S004 only. /skill each step.\n"
        "STEP 1: who speaks and JP lines\n"
        "STEP 2: /qwen-frieren-dialogue — voice clips + how long each plays\n"
        "STEP 3: /nano-banana-2-prompting still\n"
        "STEP 4: /anime-scene-i2v-prompting video (extend if needed)\n"
        "STEP 5: /pixverse-lipsync — mask each face, one pass per speaker"
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
    pdf.callout("Good prompt", "/skill first. Drag files into chat. Voice before video. S### only.")
    pdf.callout("Bad prompt", "5 second video (no dialogue). Whole chapter anime. Paste API keys.")

    pdf.ensure_space(70)
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
            ["S006", "Both speakers", "Seedance first; extend or Kling if MS two-face"],
        ],
        [28, 58, CONTENT_W - 86],
    )

    pdf.h2("10.5 If speech is longer than the video")
    pdf.body(
        "Prefer extending the same video (hold camera) over making a separate extra picture. "
        "Ask Agent to extend the last frame until all voice clips fit."
    )
    pdf.code_block(
        "/anime-scene-i2v-prompting\n"
        "[I dragged the video and voice clips]\n"
        "S006 only. Extend this clip — same angle — until all dialogue fits."
    )

    pdf.h3("Assemble scene (prompt)")
    pdf.code_block(
        "Assemble page 002 camp S002->S006B in story order.\n"
        "Use lipsync/final clips. Concat with ffmpeg. Report total duration."
    )

    pdf.ensure_space(75)
    pdf.h1("11. Voice and lip-sync (REQUIRED)")
    pdf.callout(
        "Voice FIRST",
        "Generate Qwen WAV before video duration or model. Measure seconds, then Seedance/Kling, then PixVerse.",
    )
    pdf.h3("11.1 Prompt - voice / audio")
    _ref_prompt_block(
        pdf,
        ["Voice Reference folder", "Japanese S006 panel crop"],
        "/qwen-frieren-dialogue\n"
        "[I dragged Voice Reference and JP panel]\n"
        "S006 only. Voice for Fern AND Frieren. Tell me how long each clip plays.",
    )

    pdf.h3("11.2 Prompt - lip-sync (mask first)")
    pdf.body("PixVerse = one mouth per pass. Mask non-speaking face. Two speakers = two passes.")
    _ref_prompt_block(
        pdf,
        ["S004 video", "Each speaker voice clip"],
        "/pixverse-lipsync\n"
        "[I dragged video and voice clips]\n"
        "S004 only. Lip-sync each speaker. Mask the other face each pass.",
    )
    pdf.figure(
        FIGURES[5][0],
        FIGURES[5][1],
        "S006 camp debate - lip-sync both speakers on one video; mask non-speaking face.",
        max_h=40,
    )

    pdf.ensure_space(65)
    pdf.h1("12. Prompt cookbook")
    pdf.simple_table(
        ["You want", "Skill + starter"],
        [
            ["Study page", "/manga-chapter-ingest + drag manga page photo"],
            ["Panel crop", "/manga-panel-crop-for-shots + drag full page"],
            ["Anime still", "/nano-banana-2-prompting + drag panel crop"],
            ["Voice", "/qwen-frieren-dialogue + drag Voice Reference + JP panel"],
            ["Video", "/anime-scene-i2v-prompting + drag still + voice clips"],
            ["Lip-sync", "/pixverse-lipsync + drag video + speaker voice"],
            ["First panel", "S006 First Try PDF (booklet 3)"],
            ["Full shot", "Section 9 session prompt"],
        ],
        [42, CONTENT_W - 42],
    )
    pdf.body("Agent runs scripts in scripts/ - you do not type Python for production steps.")

    pdf.h2("13. Common problems")
    pdf.simple_table(
        ["Symptom", "Fix"],
        [
            ["Agent guesses dialogue", "/skill + drag JP panel crop"],
            ["Wrong layout / mirrored", "Re-crop panel from full manga page"],
            ["Seedance policy fail", "Expected on MS two-face - switch to Kling"],
            ["Wrong lip-sync mouth", "/pixverse-lipsync - mask; one pass per speaker"],
            ["Dialogue cut off", "Voice first - extend video or longer clip"],
            ["Missing FAL_KEY", "Copy .env.example to .env"],
        ],
        [65, CONTENT_W - 65],
    )

    pdf.h2("14. Four-week syllabus")
    pdf.simple_table(
        ["Week", "Deliverable"],
        [
            ["1", "Setup + S006 First Try booklet"],
            ["2", "S004: voice-first; Seedance try then Kling; dual lip-sync"],
            ["3", "S005-S006: voice-first + extend video if needed"],
            ["4", "Assemble page 002 - length from dialogue sum"],
        ],
        [22, CONTENT_W - 22],
    )

    pdf.ensure_space(55)
    pdf.h1("Cheat sheet - use in Cursor")
    pdf.body("Drag files into chat. Do not copy paths from this page.")
    pdf.set_fill_color(*CODE_BG)
    pdf.set_font("Courier", "", 8)
    cheat = (
        "AI_Animation - Shot S### only.\n"
        "Read booklets: 1 Setup, 2 Cursor, 3 S006 First Try.\n"
        "EVERY step: /skill-name first, then drag files into chat.\n"
        "Start: /manga-chapter-ingest + drag manga page photo\n"
        "Mentor pack: Chapter-81 JPGs + Voice Reference (3 characters)\n"
        "ORDER: study -> voice clips -> still -> video (extend if short) ->\n"
        "lip-sync with face masks (one speaker per pass)\n"
        "Do not commit .env. Ask for handoff when done."
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
        cover_tagline="Booklet 4 - use after Setup, Cursor Guide, and S006 First Try.",
        body=_fill_reference_body,
        out_path=OUT,
    )


def build_all() -> list[Path]:
    paths = [
        build_setup_pdf(),
        build_cursor_guide_pdf(),
        build_s006_pdf(),
        build_reference_pdf(),
    ]
    return paths


def combine_workbook_pdfs(
    parts: tuple[Path, ...] = BOOKLET_PDFS_IN_ORDER,
    out_path: Path = OUT_COMBINED,
) -> Path:
    """Merge booklets 1-4 into one print-ready PDF (Setup -> Cursor -> S006 -> Reference)."""
    from pypdf import PdfWriter

    missing = [p for p in parts if not p.is_file()]
    if missing:
        raise FileNotFoundError(
            "Missing booklet PDF(s): " + ", ".join(str(p) for p in missing)
        )

    writer = PdfWriter()
    for part in parts:
        writer.append(str(part))
    total_pages = len(writer.pages)
    try:
        writer.compress_identical_objects(remove_identical_objects=True, remove_orphaned_objects=True)
    except TypeError:
        writer.compress_identical_objects()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with out_path.open("wb") as f:
            writer.write(f)
    except PermissionError:
        out_path = out_path.with_name(
            f"{out_path.stem}_{date.today().strftime('%Y%m%d')}{out_path.suffix}"
        )
        with out_path.open("wb") as f:
            writer.write(f)
        print(f"WARNING: combined PDF locked. Wrote: {out_path}", flush=True)

    print(
        f"Combined {len(parts)} booklets -> {out_path.name} ({total_pages} pages)",
        flush=True,
    )
    return out_path


if __name__ == "__main__":
    for path in build_all():
        print(f"Wrote: {path}")
    combined = combine_workbook_pdfs()
    print(f"Wrote: {combined}")
