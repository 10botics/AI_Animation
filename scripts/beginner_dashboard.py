"""
AI Animation Studio — beginner progress dashboard (local Streamlit).

No Streamlit Cloud account required. Read-only view of pipeline progress;
copy prompts into Cursor Agent to run Fal scripts.

Usage (from project root):
  streamlit run scripts/beginner_dashboard.py

Or double-click Start-Studio.bat at project root.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import streamlit as st

import pandas as pd

from artifact_paths import ROOT, parse_media_timestamp, shot_root
from character_bibles import (
    extract_one_line_summary,
    get_character,
    list_characters_with_bibles,
    load_doc_body,
    reference_images_for,
)
from ingest_summary import load_ingest_summary, shot_details_for_display
from panel_crop import panel_eng_path, resolve_chapter_page, save_panel_crop
import importlib

import pipeline_status as _pipeline_status

importlib.reload(_pipeline_status)
cursor_prompt_for_step = _pipeline_status.cursor_prompt_for_step
find_chapter_dir = _pipeline_status.find_chapter_dir

STEP_DISPLAY = (
    ("panel", "1. Panel crop", "`panels/eng/panel_s###.png`"),
    ("still", "2. Still (WIP)", "`shots/S###/still/wip/{model}/{timestamp}.png`"),
    ("final", "3. Approved still", "`shots/S###/still/approved/{timestamp}.png`"),
    ("voice", "4. Voice", "`shots/S###/voice/approved/{speaker}.wav`"),
    ("video", "5. Video", "`shots/S###/video/approved/{timestamp}.mp4`"),
    ("lipsync", "6. Lip-sync", "`shots/S###/lipsync/approved/{timestamp}.mp4`"),
)

STEP_SHORT = {
    "panel": "Panel",
    "still": "Still WIP",
    "final": "Approved still",
    "voice": "Voice",
    "video": "Video",
    "lipsync": "Lip-sync",
}

NEXT_STEP_TO_PROMPT = {
    "panel": "panel",
    "picture": "picture",
    "final": "final",
    "voice": "voice",
    "video": "video",
    "lipsync": "lipsync",
    "done": "done",
}

NEXT_STEP_LABEL = {
    "panel": "panel crop",
    "picture": "still (generate)",
    "final": "approved still (promote)",
    "voice": "voice",
    "video": "video",
    "lipsync": "lip-sync",
    "done": "done",
}

MISSING_FILTER_OPTIONS = (
    ("any", "Any missing resource"),
    ("panel", "Missing panel crop"),
    ("still", "Missing still WIP"),
    ("final", "Missing approved still"),
    ("voice", "Missing voice"),
    ("video", "Missing video"),
    ("lipsync", "Missing lip-sync"),
    ("complete", "Complete (all resources present)"),
)

WIP_KINDS = ("still", "voice", "video", "lipsync", "sfx")

SIDEBAR_PAGES = ("Progress", "Ingest", "Shot detail", "Characters")

PAGE_TO_URL_SLUG = {
    "Progress": "progress",
    "Ingest": "ingest",
    "Shot detail": "shot",
    "Characters": "characters",
}
URL_SLUG_TO_PAGE = {slug: page for page, slug in PAGE_TO_URL_SLUG.items()}

INGEST_TAB_TO_URL_SLUG = {
    "Story": "story",
    "Every panel": "panels",
    "Files & stats": "files",
}
URL_SLUG_TO_INGEST_TAB = {slug: tab for tab, slug in INGEST_TAB_TO_URL_SLUG.items()}

PREVIEW_TAB_TO_URL_SLUG = {
    "Still": "still",
    "Video": "video",
    "Audio": "audio",
}
URL_SLUG_TO_PREVIEW_TAB = {slug: tab for tab, slug in PREVIEW_TAB_TO_URL_SLUG.items()}

# Palettes tuned for comfortable reading (WCAG-friendly contrast, no pure #000/#fff):
# Light — slate-50 canvas, slate-800 body text (~12:1 on white cards)
# Dark — slate-900 canvas (GitHub/VS Code style), slate-100 text (~15:1 on surfaces)
THEME_LIGHT = {
    "bg": "#f8fafc",
    "surface": "#ffffff",
    "sidebar_bg": "#f1f5f9",
    "text": "#1e293b",
    "text_muted": "#64748b",
    "heading": "#0f172a",
    "border": "#e2e8f0",
    "border_strong": "#cbd5e1",
    "accent": "#0284c7",
    "accent_dark": "#0369a1",
    "accent_soft": "#e0f2fe",
    "nav_inactive_bg": "#ffffff",
    "nav_inactive_text": "#334155",
    "nav_hover_bg": "#f0f9ff",
    "nav_active_bg": "#0284c7",
    "nav_active_border": "#0369a1",
    "nav_active_text": "#ffffff",
    "code_bg": "#f1f5f9",
    "input_bg": "#ffffff",
    "progress_track": "#cbd5e1",
    "progress_fill": "#0284c7",
    "btn_secondary_bg": "#ffffff",
    "btn_secondary_text": "#334155",
    "btn_secondary_border": "#cbd5e1",
    "alert_success_bg": "#ecfdf5",
    "alert_success_text": "#065f46",
    "alert_warning_bg": "#fffbeb",
    "alert_warning_text": "#92400e",
    "alert_info_bg": "#eff6ff",
    "alert_info_text": "#1e40af",
    "alert_error_bg": "#fef2f2",
    "alert_error_text": "#991b1b",
    "expander_bg": "#ffffff",
    "header_bg": "#ffffff",
    "header_border": "#e2e8f0",
    "icon": "#475569",
    "toggle_track_off": "#64748b",
    "toggle_track_on": "#0284c7",
    "toggle_thumb": "#ffffff",
    "toggle_card_bg": "#e2e8f0",
    "toggle_card_border": "#0369a1",
    "menu_bg": "#ffffff",
    "menu_hover": "#f0f9ff",
    "menu_text": "#1e293b",
}

THEME_DARK = {
    "bg": "#0f172a",
    "surface": "#1e293b",
    "sidebar_bg": "#020617",
    "text": "#e2e8f0",
    "text_muted": "#94a3b8",
    "heading": "#f1f5f9",
    "border": "#334155",
    "border_strong": "#475569",
    "accent": "#38bdf8",
    "accent_dark": "#0ea5e9",
    "accent_soft": "#164e63",
    "nav_inactive_bg": "#1e293b",
    "nav_inactive_text": "#e2e8f0",
    "nav_hover_bg": "#334155",
    "nav_active_bg": "#0284c7",
    "nav_active_border": "#38bdf8",
    "nav_active_text": "#f8fafc",
    "code_bg": "#0f172a",
    "input_bg": "#1e293b",
    "progress_track": "#475569",
    "progress_fill": "#38bdf8",
    "btn_secondary_bg": "#1e293b",
    "btn_secondary_text": "#e2e8f0",
    "btn_secondary_border": "#475569",
    "alert_success_bg": "#14532d",
    "alert_success_text": "#bbf7d0",
    "alert_warning_bg": "#78350f",
    "alert_warning_text": "#fde68a",
    "alert_info_bg": "#1e3a5f",
    "alert_info_text": "#bae6fd",
    "alert_error_bg": "#7f1d1d",
    "alert_error_text": "#fecaca",
    "expander_bg": "#1e293b",
    "header_bg": "#0f172a",
    "header_border": "#334155",
    "icon": "#e2e8f0",
    "toggle_track_off": "#475569",
    "toggle_track_on": "#0284c7",
    "toggle_thumb": "#f8fafc",
    "toggle_card_bg": "#1e293b",
    "toggle_card_border": "#475569",
    "menu_bg": "#1e293b",
    "menu_hover": "#334155",
    "menu_text": "#e2e8f0",
}


def _get_theme() -> dict[str, str]:
    name = st.session_state.get("studio_theme", "light")
    return THEME_DARK if name == "dark" else THEME_LIGHT


def _get_theme_id() -> str:
    return st.session_state.get("studio_theme", "light")


def _button_css_block(t: dict[str, str], selector: str, *, variant: str = "secondary") -> str:
    """Shared button chrome — same rules for nav, preview, crop, and global fallback."""
    hover_selectors = [f"{selector}:hover:not(:disabled)", f"{selector}:focus-visible:not(:disabled)"]
    if " > button" in selector:
        hover_selectors.append(f"{selector.replace(' > button', ':hover > button')}:not(:disabled)")
    hover_rule = ",\n        ".join(hover_selectors)

    if variant == "primary":
        return f"""
        {selector} {{
            min-height: 2.5rem;
            background-color: {t["accent"]} !important;
            background-image: none !important;
            color: {t["nav_active_text"]} !important;
            border: 1px solid {t["accent_dark"]} !important;
            box-shadow: none !important;
        }}
        {hover_rule} {{
            background-color: {t["accent_dark"]} !important;
            background-image: none !important;
            border-color: {t["accent"]} !important;
            color: {t["nav_active_text"]} !important;
            box-shadow: none !important;
        }}
        {selector}:disabled {{
            opacity: 0.45;
        }}
        """
    if variant == "active":
        return f"""
        {selector} {{
            min-height: 2.5rem;
            background-color: {t["nav_active_bg"]} !important;
            background-image: none !important;
            color: {t["nav_active_text"]} !important;
            border: 2px solid {t["nav_active_border"]} !important;
            box-shadow: none !important;
            font-weight: 600 !important;
        }}
        {hover_rule} {{
            background-color: {t["accent_dark"]} !important;
            background-image: none !important;
            border-color: {t["accent"]} !important;
            color: {t["nav_active_text"]} !important;
            box-shadow: none !important;
        }}
        {selector}:disabled {{
            opacity: 0.45;
        }}
        """
    return f"""
    {selector} {{
        min-height: 2.5rem;
        background-color: {t["btn_secondary_bg"]} !important;
        background-image: none !important;
        color: {t["btn_secondary_text"]} !important;
        border: 1px solid {t["btn_secondary_border"]} !important;
        box-shadow: none !important;
    }}
    {hover_rule} {{
        background-color: {t["nav_hover_bg"]} !important;
        background-image: none !important;
        border-color: {t["accent"]} !important;
        color: {t["accent"]} !important;
        box-shadow: none !important;
    }}
    {selector}:disabled {{
        opacity: 0.45;
    }}
    """


def _main_buttons_css(t: dict[str, str]) -> str:
    """Global main-area button fallback (overridden by row/standalone injects below)."""
    secondary = _button_css_block(t, "section.main div.stButton > button")
    primary = _button_css_block(
        t,
        'section.main div.stButton > button[kind="primary"], '
        '[data-testid="stCopyToClipboardButton"] button',
        variant="primary",
    )
    return secondary + primary


def _button_row_layout_css(anchor_key: str) -> str:
    """Column alignment for nav-style rows (Previous / selectbox / Next)."""
    row = f'[data-testid="stHorizontalBlock"]:has(.st-key-{anchor_key})'
    return f"""
        {row} {{
            align-items: flex-end;
        }}
        {row} [data-testid="column"] {{
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
        }}
        {row} [data-testid="column"] > div {{
            width: 100%;
        }}
    """


def _button_row_styles_html(
    t: dict[str, str],
    anchor_key: str,
    *,
    active_column: int | None = None,
    primary_columns: tuple[int, ...] = (),
    layout: bool = False,
) -> str:
    """CSS for buttons in a st.columns row — anchor via :has(.st-key-{anchor_key})."""
    row = f'[data-testid="stHorizontalBlock"]:has(.st-key-{anchor_key})'
    btn = f"{row} div.stButton > button"
    parts: list[str] = []
    if layout:
        parts.append(_button_row_layout_css(anchor_key))
    parts.append(_button_css_block(t, btn))
    if active_column is not None:
        active_sel = f'{row} [data-testid="column"]:nth-child({active_column}) div.stButton > button'
        parts.append(_button_css_block(t, active_sel, variant="active"))
    for col in primary_columns:
        primary_sel = f'{row} [data-testid="column"]:nth-child({col}) div.stButton > button'
        parts.append(_button_css_block(t, primary_sel, variant="primary"))
    return f"<style>{''.join(parts)}</style>"


def _nav_button_row_styles_html(
    t: dict[str, str],
    anchor_key: str,
    *,
    active_column: int | None = None,
    primary_columns: tuple[int, ...] = (),
) -> str:
    """Nav row — same layout + button chrome as Previous / selectbox / Next."""
    return _button_row_styles_html(
        t,
        anchor_key,
        active_column=active_column,
        primary_columns=primary_columns,
        layout=True,
    )


def _widget_button_selector(key: str) -> str:
    """Match Streamlit 1.48–1.59+ button DOM (key on wrapper or on stButton)."""
    k = f".st-key-{key}"
    return (
        f"{k} div.stButton > button, "
        f"{k}.stButton > button, "
        f"{k} > button, "
        f"section.main {k} button"
    )


def _widget_button_styles_html(
    t: dict[str, str],
    keys: list[tuple[str, str]],
) -> str:
    """CSS for one or more standalone st.button widgets (widget_key, variant)."""
    parts = [
        _button_css_block(t, _widget_button_selector(key), variant=variant)
        for key, variant in keys
    ]
    return f"<style>{''.join(parts)}</style>"


def _selectbox_css(t: dict[str, str]) -> str:
    """Streamlit 1.48+ uses react-aria ComboBox, not baseweb select."""
    return f"""
        .stSelectbox .react-aria-ComboBox [role="group"],
        .st-key-shot_detail_select .react-aria-ComboBox [role="group"],
        .st-key-missing_filter .react-aria-ComboBox [role="group"] {{
            background-color: {t["input_bg"]} !important;
            border-color: {t["border"]} !important;
        }}
        .stSelectbox input[role="combobox"],
        .st-key-shot_detail_select input[role="combobox"],
        .st-key-missing_filter input[role="combobox"] {{
            background-color: {t["input_bg"]} !important;
            color: {t["text"]} !important;
            -webkit-text-fill-color: {t["text"]} !important;
            border-color: {t["border"]} !important;
        }}
        .stSelectbox .react-aria-ComboBox button,
        .st-key-shot_detail_select .react-aria-ComboBox button,
        .st-key-missing_filter .react-aria-ComboBox button {{
            background-color: {t["input_bg"]} !important;
            color: {t["icon"]} !important;
            border-color: {t["border"]} !important;
        }}
        .stSelectbox .react-aria-ComboBox svg,
        .st-key-shot_detail_select .react-aria-ComboBox svg {{
            fill: {t["icon"]} !important;
            color: {t["icon"]} !important;
        }}
        [data-testid="stSelectboxVirtualDropdown"],
        [data-testid="stSelectboxVirtualDropdown"] [role="listbox"] {{
            background-color: {t["menu_bg"]} !important;
            border-color: {t["border"]} !important;
        }}
        [data-testid="stSelectboxVirtualDropdown"] [role="option"],
        [data-testid="stSelectboxVirtualDropdown"] [data-item-hl] {{
            color: {t["menu_text"]} !important;
            background-color: transparent !important;
        }}
        [data-testid="stSelectboxVirtualDropdown"] [role="option"][aria-selected="true"],
        [data-testid="stSelectboxVirtualDropdown"] [role="option"]:hover,
        [data-testid="stSelectboxVirtualDropdown"] [role="option"][data-focused="true"] {{
            background-color: {t["menu_hover"]} !important;
            color: {t["menu_text"]} !important;
        }}
        [data-testid="stSelectboxVirtualDropdown"] [role="option"][aria-selected="true"] [data-item-hl],
        [data-testid="stSelectboxVirtualDropdown"] [role="option"]:hover [data-item-hl] {{
            color: {t["menu_text"]} !important;
        }}
        """


def _glide_dataframe_css(t: dict[str, str]) -> str:
    """Glide Data Grid fallback — canvas grid ignores most parent CSS."""
    return f"""
        div.stDataFrameGlideDataEditor,
        [data-testid="stDataFrame"] div.stDataFrameGlideDataEditor {{
            --gdg-accent-color: {t["accent"]} !important;
            --gdg-accent-fg: {t["nav_active_text"]} !important;
            --gdg-accent-light: {t["accent_soft"]} !important;
            --gdg-text-dark: {t["text"]} !important;
            --gdg-text-medium: {t["text_muted"]} !important;
            --gdg-text-light: {t["text_muted"]} !important;
            --gdg-text-bubble: {t["text"]} !important;
            --gdg-text-header: {t["heading"]} !important;
            --gdg-text-header-selected: {t["heading"]} !important;
            --gdg-bg-cell: {t["surface"]} !important;
            --gdg-bg-cell-medium: {t["code_bg"]} !important;
            --gdg-bg-header: {t["code_bg"]} !important;
            --gdg-bg-header-hovered: {t["nav_hover_bg"]} !important;
            --gdg-bg-header-has-focus: {t["accent_soft"]} !important;
            --gdg-bg-icon-header: {t["code_bg"]} !important;
            --gdg-fg-icon-header: {t["icon"]} !important;
            --gdg-bg-bubble: {t["code_bg"]} !important;
            --gdg-border-color: {t["border"]} !important;
            --gdg-horizontal-border-color: {t["border"]} !important;
            --gdg-link-color: {t["accent"]} !important;
        }}
        [data-testid="stDataFrameResizable"] {{
            background-color: {t["surface"]} !important;
            border-color: {t["border"]} !important;
        }}
        [data-testid="stTable"],
        [data-testid="stTable"] > div {{
            background-color: {t["surface"]} !important;
            border-color: {t["border"]} !important;
        }}
        [data-testid="stTable"] table {{
            color: {t["text"]} !important;
            background-color: {t["surface"]} !important;
        }}
        [data-testid="stTable"] thead th {{
            background-color: {t["code_bg"]} !important;
            color: {t["heading"]} !important;
            border-color: {t["border"]} !important;
        }}
        [data-testid="stTable"] tbody td {{
            background-color: {t["surface"]} !important;
            color: {t["text"]} !important;
            border-color: {t["border"]} !important;
        }}
        """


def _theme_dataframe(rows: list[dict], t: dict[str, str]) -> None:
    """Read-only table with cell colors that follow studio light/dark toggle."""
    if not rows:
        st.caption("No rows to display.")
        return
    df = pd.DataFrame(rows)
    cell_props = {
        "background-color": t["surface"],
        "color": t["text"],
        "border-color": t["border"],
    }
    header_props = [
        ("background-color", t["code_bg"]),
        ("color", t["heading"]),
        ("border-color", t["border"]),
    ]
    styler = (
        df.style.set_properties(**cell_props)
        .set_table_styles(
            [
                {"selector": "th", "props": header_props},
                {"selector": "thead th", "props": header_props},
            ],
            overwrite=False,
        )
        .hide(axis="index")
    )
    # st.table uses HTML DOM (not Glide canvas) so theme CSS + Styler both apply.
    st.table(styler, width="stretch", hide_index=True)


def _theme_css(t: dict[str, str]) -> str:
    """Full app chrome + widgets — embedded palette colors, re-injected per theme."""
    return f"""
        /* ── App shell ── */
        .stApp {{
            background-color: {t["bg"]} !important;
            color: {t["text"]} !important;
        }}
        [data-testid="stAppViewContainer"] > section.main {{
            background-color: {t["bg"]};
        }}
        [data-testid="stDecoration"] {{
            display: none !important;
        }}
        header[data-testid="stHeader"] {{
            background-color: {t["header_bg"]} !important;
            border-bottom: 1px solid {t["header_border"]} !important;
        }}
        [data-testid="stToolbar"],
        [data-testid="stHeader"] [data-testid="stToolbar"] {{
            background-color: {t["header_bg"]} !important;
        }}
        [data-testid="stHeader"] button,
        [data-testid="stSidebarCollapseButton"] button,
        [data-testid="stExpandSidebarButton"] button,
        button[kind="header"],
        button[kind="headerNoPadding"] {{
            color: {t["icon"]} !important;
            background-color: transparent !important;
        }}
        [data-testid="stHeader"] [data-testid="stIconMaterial"],
        [data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"],
        [data-testid="stExpandSidebarButton"] [data-testid="stIconMaterial"],
        [data-testid="stHeader"] svg,
        [data-testid="stSidebarCollapseButton"] svg,
        [data-testid="stExpandSidebarButton"] svg {{
            color: {t["icon"]} !important;
            fill: {t["icon"]} !important;
        }}
        [data-testid="stMainMenu"] {{
            color: {t["icon"]} !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarHeader"],
        section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] > div {{
            background-color: {t["sidebar_bg"]} !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] button,
        section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] [data-testid="stIconMaterial"] {{
            color: {t["icon"]} !important;
            fill: {t["icon"]} !important;
        }}

        /* ── Sidebar ── */
        section[data-testid="stSidebar"] {{
            background-color: {t["sidebar_bg"]} !important;
            border-right: 1px solid {t["border"]} !important;
        }}
        section[data-testid="stSidebar"] > div:first-child {{
            background-color: {t["sidebar_bg"]} !important;
        }}
        section[data-testid="stSidebar"] .stMarkdown,
        section[data-testid="stSidebar"] .stMarkdown p,
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] .stCaption {{
            color: {t["text"]} !important;
        }}

        /* ── Main content ── */
        section.main .block-container {{
            color: {t["text"]};
        }}
        section.main h1, section.main h2, section.main h3,
        section.main .stMarkdown h1, section.main .stMarkdown h2,
        section.main .stMarkdown h3, section.main .stMarkdown strong {{
            color: {t["heading"]} !important;
        }}
        section.main .stMarkdown p, section.main .stMarkdown li,
        section.main label, section.main .stCaption {{
            color: {t["text"]};
        }}
        section.main .stMarkdown p em, section.main .stCaption {{
            color: {t["text_muted"]} !important;
        }}

        /* ── Toggle (dark mode switch) ── */
        section[data-testid="stSidebar"] .st-key-studio_theme_dark {{
            background-color: {t["toggle_card_bg"]} !important;
            border: 2px solid {t["toggle_card_border"]} !important;
            border-radius: 8px !important;
            padding: 0.65rem 0.75rem !important;
            margin-bottom: 0.75rem !important;
        }}
        section[data-testid="stSidebar"] .st-key-studio_theme_dark label {{
            width: 100% !important;
            justify-content: space-between !important;
        }}
        .stToggle label span {{
            color: {t["heading"]} !important;
            font-weight: 600 !important;
        }}
        .stToggle [data-baseweb="switch"],
        .stToggle [data-baseweb="switch"] > div {{
            background-color: {t["toggle_track_off"]} !important;
            border: 2px solid {t["toggle_card_border"]} !important;
            box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.12) !important;
        }}
        .stToggle [data-baseweb="switch"][aria-checked="true"],
        .stToggle [data-baseweb="switch"][aria-checked="true"] > div {{
            background-color: {t["toggle_track_on"]} !important;
            border-color: {t["toggle_track_on"]} !important;
        }}
        .stToggle [data-baseweb="switch"] [data-baseweb="slider"],
        .stToggle [data-baseweb="switch"] > div > div {{
            background-color: {t["toggle_thumb"]} !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25) !important;
        }}
        .stToggle label[data-baseweb="checkbox"] > div:first-of-type {{
            background-color: {t["toggle_track_off"]} !important;
            border: 2px solid {t["toggle_card_border"]} !important;
        }}
        .stToggle label[data-baseweb="checkbox"]:has(input:checked) > div:first-of-type {{
            background-color: {t["toggle_track_on"]} !important;
            border-color: {t["toggle_track_on"]} !important;
        }}

        /* ── Text inputs & prompt box (copy/paste) ── */
        .stTextArea textarea,
        [data-testid="stTextArea"] textarea,
        [data-testid="stTextArea"] [data-baseweb="textarea"],
        .stTextInput input,
        [data-testid="stTextInput"] input {{
            background-color: {t["input_bg"]} !important;
            color: {t["text"]} !important;
            -webkit-text-fill-color: {t["text"]} !important;
            border-color: {t["border"]} !important;
            caret-color: {t["accent"]} !important;
        }}
        .stSelectbox label, .stTextArea label, [data-testid="stTextArea"] label {{
            color: {t["text_muted"]} !important;
        }}

        {_main_buttons_css(t)}

        /* ── Metrics, tables, code ── */
        div[data-testid="stMetric"] {{
            background-color: {t["surface"]};
            border: 1px solid {t["border"]};
            border-radius: 8px;
            padding: 0.65rem 0.85rem;
        }}
        div[data-testid="stMetric"] label {{
            color: {t["text_muted"]} !important;
        }}
        div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
            color: {t["heading"]} !important;
        }}
        div[data-testid="stDataFrame"], div[data-testid="stTable"] {{
            border: 1px solid {t["border"]};
            border-radius: 8px;
            background-color: {t["surface"]};
        }}
        code, .stCode, pre,
        [data-testid="stCode"] pre,
        [data-testid="stCodeBlock"] pre,
        [data-testid="stCodeBlock"] code {{
            background-color: {t["code_bg"]} !important;
            color: {t["text"]} !important;
            border: 1px solid {t["border"]};
        }}

        /* ── Progress & dividers ── */
        div[data-testid="stProgressBar"] > div > div {{
            background-color: {t["progress_track"]};
        }}
        div[data-testid="stProgressBar"] > div > div > div {{
            background-color: {t["progress_fill"]};
        }}
        hr {{
            border-color: {t["border"]} !important;
        }}

        /* ── Help tooltips (button help= text) ── */
        [data-baseweb="popover"],
        [data-baseweb="tooltip"],
        div[role="tooltip"],
        [data-testid="stTooltipContent"] {{
            background-color: {t["surface"]} !important;
            color: {t["text"]} !important;
            border: 1px solid {t["border"]} !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35) !important;
        }}
        [data-baseweb="popover"] div,
        [data-baseweb="tooltip"] div,
        div[role="tooltip"] div,
        [data-testid="stTooltipContent"] div {{
            color: {t["text"]} !important;
        }}

        /* ── Alerts ── */
        div[data-testid="stAlert"] {{
            border-radius: 8px;
            border: 1px solid {t["border"]};
        }}
        div[data-testid="stAlert"]:has(svg[data-testid="stAlertSuccessIcon"]) {{
            background-color: {t["alert_success_bg"]} !important;
            color: {t["alert_success_text"]} !important;
        }}
        div[data-testid="stAlert"]:has(svg[data-testid="stAlertSuccessIcon"]) * {{
            color: {t["alert_success_text"]} !important;
        }}
        div[data-testid="stAlert"]:has(svg[data-testid="stAlertWarningIcon"]) {{
            background-color: {t["alert_warning_bg"]} !important;
            color: {t["alert_warning_text"]} !important;
        }}
        div[data-testid="stAlert"]:has(svg[data-testid="stAlertWarningIcon"]) * {{
            color: {t["alert_warning_text"]} !important;
        }}
        div[data-testid="stAlert"]:has(svg[data-testid="stAlertInfoIcon"]) {{
            background-color: {t["alert_info_bg"]} !important;
            color: {t["alert_info_text"]} !important;
        }}
        div[data-testid="stAlert"]:has(svg[data-testid="stAlertInfoIcon"]) * {{
            color: {t["alert_info_text"]} !important;
        }}
        div[data-testid="stAlert"]:has(svg[data-testid="stAlertErrorIcon"]) {{
            background-color: {t["alert_error_bg"]} !important;
            color: {t["alert_error_text"]} !important;
        }}
        div[data-testid="stAlert"]:has(svg[data-testid="stAlertErrorIcon"]) * {{
            color: {t["alert_error_text"]} !important;
        }}

        /* ── Radio / segmented tabs (ingest section, etc.) ── */
        div[data-testid="stRadio"] > div,
        div[data-testid="stRadio"] [role="radiogroup"] {{
            background-color: {t["surface"]} !important;
            border-color: {t["border"]} !important;
        }}
        div[data-testid="stRadio"] label,
        div[data-testid="stRadio"] label span {{
            color: {t["text"]} !important;
        }}
        div[data-testid="stRadio"] label[data-baseweb="radio"] > div:first-of-type {{
            background-color: {t["input_bg"]} !important;
            border-color: {t["border"]} !important;
        }}
        div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) > div:first-of-type {{
            background-color: {t["accent"]} !important;
            border-color: {t["accent"]} !important;
        }}

        /* ── Expanders ── */
        details[data-testid="stExpander"] {{
            background-color: {t["expander_bg"]};
            border: 1px solid {t["border"]};
            border-radius: 8px;
        }}
        details[data-testid="stExpander"] summary {{
            color: {t["heading"]} !important;
        }}

        /* ── Shot detail layout (theme-neutral) ── */
        section.main [data-testid="stHorizontalBlock"]:has([class*="preview_btn_"]) {{
            align-items: flex-start !important;
        }}
        section.main [data-testid="stHorizontalBlock"]:has([class*="preview_btn_"]) [data-testid="column"] {{
            justify-content: flex-start !important;
        }}

        {_glide_dataframe_css(t)}
        """


def _inject_theme_css(t: dict[str, str]) -> None:
    """Inject theme CSS every run — Streamlit rebuilds the DOM on each rerun/fragment."""
    theme_id = _get_theme_id()
    st.html(
        f'<script>document.documentElement.setAttribute("data-studio-theme","{theme_id}");</script>',
        unsafe_allow_javascript=True,
    )
    st.html(f"<style>{_theme_css(t)}{_selectbox_css(t)}</style>")


def _init_session_state() -> None:
    if "studio_theme" not in st.session_state:
        st.session_state.studio_theme = "light"
    if "studio_theme_dark" in st.session_state:
        st.session_state.studio_theme = (
            "dark" if st.session_state.studio_theme_dark else "light"
        )
    if "scan_cache_version" not in st.session_state:
        st.session_state.scan_cache_version = 0
    if "ingest_panel_view" not in st.session_state:
        st.session_state.ingest_panel_view = "Panel story (browse)"
    if "studio_page_radio" not in st.session_state:
        legacy = st.session_state.get("studio_page", SIDEBAR_PAGES[0])
        if legacy == "Missing resources":
            legacy = "Progress"
        st.session_state.studio_page_radio = legacy if legacy in SIDEBAR_PAGES else SIDEBAR_PAGES[0]
    if "ingest_main_tab" not in st.session_state:
        st.session_state.ingest_main_tab = "Story"
    if "skip_silent_shots_nav" not in st.session_state:
        st.session_state.skip_silent_shots_nav = True
    if "character_detail_id" not in st.session_state:
        st.session_state.character_detail_id = ""


def _qp_get(key: str) -> str:
    if not hasattr(st, "query_params"):
        return ""
    val = st.query_params.get(key, "")
    if isinstance(val, list):
        return val[0] if val else ""
    return str(val).strip() if val else ""


def _url_snapshot() -> str:
    return "|".join(
        _qp_get(key) for key in ("page", "shot", "ingest", "preview", "character")
    )


def _apply_url_to_session() -> None:
    """Restore page / shot / tabs from the browser URL (F5 or edited address bar only)."""
    if not hasattr(st, "query_params"):
        return

    snap = _url_snapshot()
    if st.session_state.get("_applied_url_snapshot") == snap:
        return

    page_slug = _qp_get("page")
    if page_slug in URL_SLUG_TO_PAGE:
        st.session_state.studio_page_radio = URL_SLUG_TO_PAGE[page_slug]

    shot = _qp_get("shot").upper()
    if shot:
        st.session_state.shot_detail_id = shot
        st.session_state.shot_detail_select = shot

    ingest_slug = _qp_get("ingest")
    if ingest_slug in URL_SLUG_TO_INGEST_TAB:
        st.session_state.ingest_main_tab = URL_SLUG_TO_INGEST_TAB[ingest_slug]

    preview_slug = _qp_get("preview")
    if preview_slug in URL_SLUG_TO_PREVIEW_TAB and shot:
        st.session_state[f"shot_preview_tab_{shot}"] = URL_SLUG_TO_PREVIEW_TAB[preview_slug]

    character = _qp_get("character").lower()
    if character and get_character(character):
        st.session_state.character_detail_id = character
        st.session_state.character_select = character

    st.session_state._applied_url_snapshot = snap


def _sync_session_to_url() -> None:
    """Keep ?page=…&shot=… in the address bar so browser refresh stays put."""
    if not hasattr(st, "query_params"):
        return

    page = _current_page()
    desired: dict[str, str] = {"page": PAGE_TO_URL_SLUG.get(page, "progress")}

    if page == "Shot detail":
        shot = str(st.session_state.get("shot_detail_id", "")).upper()
        if shot:
            desired["shot"] = shot
        preview = st.session_state.get(f"shot_preview_tab_{shot}", "Still")
        desired["preview"] = PREVIEW_TAB_TO_URL_SLUG.get(preview, "still")
    elif page == "Ingest":
        ingest = st.session_state.get("ingest_main_tab", "Story")
        desired["ingest"] = INGEST_TAB_TO_URL_SLUG.get(ingest, "story")
    elif page == "Characters":
        char_id = str(st.session_state.get("character_detail_id", "")).lower()
        if char_id:
            desired["character"] = char_id

    tracked = ("page", "shot", "ingest", "preview", "character")
    if all(desired.get(key, "") == _qp_get(key) for key in tracked):
        return

    for key in tracked:
        if key in desired:
            st.query_params[key] = desired[key]
        elif _qp_get(key):
            del st.query_params[key]

    st.session_state._applied_url_snapshot = "|".join(desired.get(key, "") for key in tracked)


def _render_theme_toggle() -> None:
    if "studio_theme_dark" not in st.session_state:
        st.session_state.studio_theme_dark = st.session_state.studio_theme == "dark"

    def _apply_theme_from_toggle() -> None:
        st.session_state.studio_theme = "dark" if st.session_state.studio_theme_dark else "light"

    st.toggle("Dark mode", key="studio_theme_dark", on_change=_apply_theme_from_toggle)


def _sync_shot_prompt(selected: str, prompt: str, shot) -> str:
    """Keep one editable prompt buffer per shot; refresh when any pipeline step changes."""
    prompt_key = f"shot_agent_prompt_{selected}"
    progress_key = f"shot_detail_progress_{selected}"
    fingerprint = _shot_progress_fingerprint(shot)
    if (
        st.session_state.get("shot_detail_prompt_for") != selected
        or st.session_state.get(progress_key) != fingerprint
    ):
        st.session_state[prompt_key] = prompt
        st.session_state.shot_detail_prompt_for = selected
        st.session_state[progress_key] = fingerprint
    return prompt_key


def _shot_progress_fingerprint(shot) -> str:
    """Changes when any tracked pipeline file appears, disappears, or next step shifts."""
    return (
        f"{shot.next_step}|d{int(getattr(shot, 'has_dialogue', True))}|"
        f"p{int(shot.panel)}s{int(shot.still)}f{int(shot.final)}"
        f"v{int(shot.voice)}vi{int(shot.video)}l{int(shot.lipsync)}|"
        f"{shot.still_path}|{shot.final_path}|{shot.voice_path}|"
        f"{shot.video_path}|{shot.lipsync_path}"
    )


def _invalidate_shot_prompt(shot_id: str) -> None:
    """Force the Cursor prompt to rebuild on the next run (e.g. after saving a panel)."""
    st.session_state.pop(f"shot_agent_prompt_{shot_id}", None)
    st.session_state.pop(f"shot_detail_progress_{shot_id}", None)
    st.session_state.pop(f"shot_detail_prompt_step_{shot_id}", None)
    if st.session_state.get("shot_detail_prompt_for") == shot_id:
        st.session_state.pop("shot_detail_prompt_for", None)


def _scan_chapter_live(chapter_dir: Path):
    """Uncached filesystem scan — always reflects files written outside the dashboard."""
    from pipeline_status import scan_chapter

    return scan_chapter(chapter_dir)


def _reload_shots(chapter_dir: Path):
    """Fresh pipeline scan on every fragment rerun."""
    return _scan_chapter_live(chapter_dir).shots


def _rel_path(path: str | Path) -> str:
    if not path:
        return ""
    p = Path(path)
    try:
        return p.relative_to(ROOT).as_posix()
    except ValueError:
        return p.as_posix()


def _path_kind(path: str) -> str:
    if not path:
        return ""
    norm = path.replace("\\", "/").lower()
    if "/approved/" in norm:
        return "approved"
    if norm.endswith("/approved.png") or norm.endswith("/approved.mp4") or norm.endswith("/approved.mp3"):
        return "approved"
    if "/wip/" in norm:
        return "wip"
    if "/tests/" in norm or "/outputs/" in norm:
        return "legacy"
    if "/panels/" in norm:
        return "panel"
    return ""


def _human_timestamp(path: str) -> str:
    ts = parse_media_timestamp(Path(path).name) if path else None
    if not ts:
        return ""
    try:
        dt = datetime.strptime(ts, "%Y%m%d_%H%M%S")
        return f"{dt.day} {dt.strftime('%b %Y %H:%M UTC')}"
    except ValueError:
        return ts


def _wip_files(shot_id: str, kind: str) -> list[Path]:
    wip = shot_root(shot_id) / kind / "wip"
    if not wip.is_dir():
        return []
    return sorted(
        (p for p in wip.rglob("*") if p.is_file()),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def _approved_files(shot_id: str, kind: str) -> list[Path]:
    approved = shot_root(shot_id) / kind / "approved"
    if not approved.is_dir():
        return []
    return sorted(
        (p for p in approved.iterdir() if p.is_file()),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def _dedupe_media_options(items: list[tuple[str, Path]]) -> list[tuple[str, Path]]:
    seen: set[str] = set()
    out: list[tuple[str, Path]] = []
    for label, path in items:
        key = str(path.resolve())
        if key in seen or not path.is_file():
            continue
        seen.add(key)
        out.append((label, path))
    return out


def _collect_video_options(shot_id: str) -> list[tuple[str, Path]]:
    items: list[tuple[str, Path]] = []
    for path in _approved_files(shot_id, "lipsync"):
        items.append((f"Lip-sync · approved · {path.name}", path))
    for path in _approved_files(shot_id, "video"):
        items.append((f"Video · approved · {path.name}", path))
    for path in _wip_files(shot_id, "lipsync"):
        items.append((f"Lip-sync · wip · {path.name}", path))
    for path in _wip_files(shot_id, "video"):
        items.append((f"Video · wip · {path.name}", path))
    return _dedupe_media_options(items)


def _collect_audio_options(shot_id: str) -> list[tuple[str, Path]]:
    items: list[tuple[str, Path]] = []
    for path in _approved_files(shot_id, "voice"):
        items.append((f"Voice · approved · {path.name}", path))
    for path in _wip_files(shot_id, "voice"):
        items.append((f"Voice · wip · {path.name}", path))
    for path in _wip_files(shot_id, "sfx"):
        items.append((f"SFX · wip · {path.name}", path))
    return _dedupe_media_options(items)


def _play_video_file(path: Path) -> None:
    resolved = path.resolve()
    if not resolved.is_file():
        st.warning("Video file not found on disk.")
        return
    st.caption(f"`{_rel_path(resolved)}` · {_path_kind(str(resolved)) or 'file'}")
    try:
        st.video(str(resolved))
    except Exception:
        st.video(resolved.read_bytes())


def _play_audio_file(path: Path) -> None:
    resolved = path.resolve()
    if not resolved.is_file():
        st.warning("Audio file not found on disk.")
        return
    st.caption(f"`{_rel_path(resolved)}` · {_path_kind(str(resolved)) or 'file'}")
    try:
        st.audio(str(resolved))
    except Exception:
        st.audio(resolved.read_bytes())


def _default_preview_tab(shot) -> str:
    """Preview tab that matches pipeline focus — next step or latest artifact."""
    focus = {
        "panel": "Still",
        "picture": "Still",
        "final": "Still",
        "voice": "Audio",
        "video": "Video",
        "lipsync": "Video",
    }.get(shot.next_step, "Still")
    if shot.next_step == "done":
        if _collect_video_options(shot.shot_id):
            return "Video"
        if _collect_audio_options(shot.shot_id):
            return "Audio"
        return "Still"
    if focus == "Video" and not _collect_video_options(shot.shot_id):
        if _collect_audio_options(shot.shot_id):
            return "Audio"
        return "Still"
    if focus == "Audio" and not _collect_audio_options(shot.shot_id):
        return "Still"
    return focus


def _set_preview_tab(shot_id: str, tab: str) -> None:
    st.session_state[f"shot_preview_tab_{shot_id}"] = tab


def _ensure_preview_tab(shot_id: str, shot) -> str:
    tab_key = f"shot_preview_tab_{shot_id}"
    progress_key = f"shot_preview_progress_{shot_id}"
    fingerprint = _shot_progress_fingerprint(shot)
    if st.session_state.get("_preview_shot_id") != shot_id:
        st.session_state._preview_shot_id = shot_id
        st.session_state[progress_key] = fingerprint
        st.session_state[tab_key] = _default_preview_tab(shot)
    elif st.session_state.get(progress_key) != fingerprint:
        st.session_state[progress_key] = fingerprint
        st.session_state[tab_key] = _default_preview_tab(shot)
    elif tab_key not in st.session_state:
        st.session_state[tab_key] = _default_preview_tab(shot)
    return st.session_state[tab_key]


def _resolve_initial_shot(shot_ids: list[str]) -> str:
    """S001 on first visit; then last shot or URL."""
    if not shot_ids:
        return "S001"
    url_shot = _qp_get("shot").upper()
    if url_shot in shot_ids:
        return url_shot
    current = st.session_state.get("shot_detail_id", "")
    if current in shot_ids:
        return current
    last = st.session_state.get("last_shot_detail_id", "")
    if last in shot_ids:
        return last
    if "S001" in shot_ids:
        return "S001"
    return shot_ids[0]


def _remember_shot(shot_id: str) -> None:
    st.session_state.shot_detail_id = shot_id
    st.session_state.shot_detail_select = shot_id
    st.session_state.last_shot_detail_id = shot_id


def _preview_tab_styles_html(t: dict[str, str], shot_id: str, active_tab: str) -> str:
    """CSS for Still/Video/Audio row — mirrors Previous/Next row."""
    tab_index = {"Still": 1, "Video": 2, "Audio": 3}[active_tab]
    return _button_row_styles_html(t, f"preview_btn_still_{shot_id}", active_column=tab_index)


def _shot_detail_button_styles_html(t: dict[str, str], shot_id: str) -> str:
    """All shot-detail main buttons — re-injected last so theme wins on fragment reruns."""
    preview_tab = st.session_state.get(f"shot_preview_tab_{shot_id}", "Still")
    crop_anchor = f"panel_crop_anchor_{shot_id}"
    return (
        _preview_tab_styles_html(t, shot_id, preview_tab)
        + _nav_button_row_styles_html(t, "shot_detail_select")
        + _nav_button_row_styles_html(t, crop_anchor)
        + _nav_button_row_styles_html(t, f"save_panel_crop_{shot_id}", primary_columns=(1,))
        + _widget_button_styles_html(
            t,
            [
                (f"btn_close_panel_crop_{shot_id}", "secondary"),
                (f"btn_close_panel_crop_{shot_id}_2", "secondary"),
                (f"copy_prompt_{shot_id}", "primary"),
            ],
        )
    )


def _render_shot_media_preview(shot_id: str, shot, t: dict[str, str]) -> None:
    st.subheader("Preview")

    preview_tab = _ensure_preview_tab(shot_id, shot)
    focus_hint = shot.next_step if shot.next_step != "done" else "latest"
    st.caption(f"Pipeline focus: **{focus_hint}**")

    preview_tab = st.session_state.get(f"shot_preview_tab_{shot_id}", preview_tab)
    st.markdown(_preview_tab_styles_html(t, shot_id, preview_tab), unsafe_allow_html=True)

    btn_cols = st.columns(3)
    for col, tab in zip(btn_cols, ("Still", "Video", "Audio")):
        with col:
            st.button(
                tab,
                key=f"preview_btn_{tab.lower()}_{shot_id}",
                use_container_width=True,
                type="secondary",
                on_click=_set_preview_tab,
                kwargs={"shot_id": shot_id, "tab": tab},
            )

    preview_tab = st.session_state.get(f"shot_preview_tab_{shot_id}", preview_tab)

    if preview_tab == "Still":
        preview_path = None
        for candidate in (shot.final_path, shot.still_path, shot.panel_path):
            if candidate and Path(candidate).is_file():
                preview_path = candidate
                break
        if preview_path and Path(preview_path).suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
            kind = _path_kind(preview_path)
            st.image(
                preview_path,
                caption=f"{Path(preview_path).name} ({kind or 'file'})",
                use_container_width=True,
            )
            st.caption(f"`{_rel_path(preview_path)}`")
        else:
            st.info("No still yet — start with **Panel crop** in Cursor.")

    elif preview_tab == "Video":
        videos = _collect_video_options(shot_id)
        if not videos:
            st.caption("No video clips for this shot yet.")
        else:
            labels = [label for label, _ in videos]
            st.selectbox(
                "Choose clip",
                labels,
                key=f"shot_video_pick_{shot_id}",
            )
            choice = st.session_state[f"shot_video_pick_{shot_id}"]
            video_path = next(path for label, path in videos if label == choice)
            _play_video_file(video_path)

    elif preview_tab == "Audio":
        audios = _collect_audio_options(shot_id)
        if not audios:
            st.caption("No audio for this shot yet.")
        else:
            labels = [label for label, _ in audios]
            st.selectbox(
                "Choose track",
                labels,
                key=f"shot_audio_pick_{shot_id}",
            )
            choice = st.session_state[f"shot_audio_pick_{shot_id}"]
            audio_path = next(path for label, path in audios if label == choice)
            _play_audio_file(audio_path)


def _wip_counts(shot_id: str) -> dict[str, int]:
    return {kind: len(_wip_files(shot_id, kind)) for kind in WIP_KINDS}


def _cursor_prompt_for_shot(shot) -> str:
    """Build Agent prompt from live shot status (paths + promote vs generate)."""
    step = shot.next_step
    if step == "done":
        return cursor_prompt_for_step(shot.shot_id, "done")
    prompt_step = NEXT_STEP_TO_PROMPT.get(step, step)
    still_path = ""
    artifact_path = ""
    if prompt_step == "final" and shot.still_path:
        still_path = _rel_path(shot.still_path)
    elif prompt_step in ("voice", "video", "lipsync"):
        path = getattr(shot, f"{prompt_step}_path", "")
        if path and _path_kind(path) == "wip":
            artifact_path = _rel_path(path)
    return cursor_prompt_for_step(
        shot.shot_id,
        prompt_step,
        still_path=still_path,
        artifact_path=artifact_path,
        has_dialogue=getattr(shot, "has_dialogue", True),
    )


def _step_path(shot, key: str) -> str:
    if key == "still":
        return shot.still_path
    return getattr(shot, f"{key}_path", "")


def _step_applies(shot, key: str) -> bool:
    if key in ("voice", "lipsync") and not getattr(shot, "has_dialogue", True):
        return False
    return True


def _step_ok(shot, key: str) -> bool:
    if not _step_applies(shot, key):
        return True
    return bool(getattr(shot, key))


def _icon(ok: bool) -> str:
    return "✓" if ok else "·"


def _missing_labels(shot) -> list[str]:
    return [
        STEP_SHORT[key]
        for key, _, _ in STEP_DISPLAY
        if _step_applies(shot, key) and not _step_ok(shot, key)
    ]


def _missing_keys(shot) -> list[str]:
    return [key for key, _, _ in STEP_DISPLAY if _step_applies(shot, key) and not _step_ok(shot, key)]


def _count_missing(shots, key: str) -> int:
    return sum(1 for s in shots if _step_applies(s, key) and not _step_ok(s, key))


def _filter_shots(shots, filter_key: str):
    if filter_key == "any":
        return [s for s in shots if _missing_keys(s)]
    if filter_key == "complete":
        return [s for s in shots if not _missing_keys(s)]
    return [s for s in shots if not _step_ok(s, filter_key)]


INGEST_SUMMARY_SCHEMA = 5  # bump when IngestSummary fields change (invalidates Streamlit cache)


@st.cache_data(show_spinner=False)
def _load_chapter_progress(chapter_dir: str, _cache_version: int):
    """Cached filesystem scan — bump _cache_version via Refresh progress to rescan."""
    from pipeline_status import ChapterProgress, scan_chapter

    return scan_chapter(Path(chapter_dir))


@st.cache_data(show_spinner=False)
def _load_ingest_summary(chapter_dir: str, _cache_version: int, _schema: int = INGEST_SUMMARY_SCHEMA):
    """Cached ingest parse — bump _cache_version via Refresh progress to rescan."""
    return load_ingest_summary(Path(chapter_dir))


def _refresh_progress() -> None:
    """Rescan disk without changing the current page, shot, or tab."""
    st.session_state.scan_cache_version = int(st.session_state.get("scan_cache_version", 0)) + 1
    _load_chapter_progress.clear()
    _load_ingest_summary.clear()
    if hasattr(st, "toast"):
        st.toast("Progress refreshed")


NAV_ITEMS = (
    ("Progress", "nav_progress"),
    ("Ingest", "nav_ingest"),
    ("Shot detail", "nav_shot_detail"),
    ("Characters", "nav_characters"),
)


def _nav_to_page(page_name: str) -> None:
    st.session_state.studio_page_radio = page_name


def _render_sidebar_menu(t: dict[str, str]) -> None:
    """Sidebar nav — rectangular buttons; only active page highlighted."""
    for label, key in NAV_ITEMS:
        st.button(
            label,
            key=key,
            use_container_width=True,
            type="secondary",
            on_click=_nav_to_page,
            kwargs={"page_name": label},
        )

    active = st.session_state.studio_page_radio
    rules = [
        "section[data-testid='stSidebar'] .st-key-nav_progress, "
        "section[data-testid='stSidebar'] .st-key-nav_ingest, "
        "section[data-testid='stSidebar'] .st-key-nav_shot_detail, "
        "section[data-testid='stSidebar'] .st-key-nav_characters { margin-bottom: 0.35rem; }",
    ]
    for label, key in NAV_ITEMS:
        is_active = active == label
        if is_active:
            bg = t["nav_active_bg"]
            border = t["nav_active_border"]
            text = t["nav_active_text"]
            hover_bg, hover_border, hover_text = t["accent_dark"], t["accent"], t["nav_active_text"]
        else:
            bg = t["nav_inactive_bg"]
            border = t["border"]
            text = t["nav_inactive_text"]
            hover_bg = t["nav_hover_bg"]
            hover_border = t["accent"]
            hover_text = t["text"]
        weight = "600" if is_active else "500"
        rules.append(
            f"""
            section[data-testid="stSidebar"] .st-key-{key} button {{
                background-color: {bg} !important;
                border: 3px solid {border} !important;
                color: {text} !important;
                font-weight: {weight} !important;
                border-radius: 6px !important;
                min-height: 2.75rem !important;
            }}
            section[data-testid="stSidebar"] .st-key-{key} button:hover {{
                background-color: {hover_bg} !important;
                border-color: {hover_border} !important;
                color: {hover_text} !important;
            }}
            """
        )
    rules.append(
        f"""
        section[data-testid="stSidebar"] .st-key-refresh_progress button {{
            background-color: {t["nav_inactive_bg"]} !important;
            color: {t["nav_inactive_text"]} !important;
            border: 3px solid {t["border"]} !important;
            border-radius: 6px !important;
            min-height: 2.75rem !important;
            font-weight: 500 !important;
        }}
        section[data-testid="stSidebar"] .st-key-refresh_progress button:hover {{
            background-color: {t["nav_hover_bg"]} !important;
            border-color: {t["accent"]} !important;
        }}
        """
    )
    st.markdown(f"<style>{''.join(rules)}</style>", unsafe_allow_html=True)


def _current_page() -> str:
    page = st.session_state.get("studio_page_radio", SIDEBAR_PAGES[0])
    return page if page in SIDEBAR_PAGES else SIDEBAR_PAGES[0]


def _chapter_progress_ratio(shots) -> tuple[float, int, int]:
    """Fraction of all tracked step slots that have files (0–1)."""
    total = sum(s.steps_total for s in shots)
    done = sum(s.steps_done for s in shots)
    if total == 0:
        return 0.0, 0, 0
    return done / total, done, total


def _render_progress_page(shots) -> None:
    st.subheader("Progress")
    st.caption(
        "Chapter pipeline status — files under `shots/S###/` (WIP history + approved heroes). "
        "Legacy `Tests/` and `outputs/` paths still count if not migrated."
    )

    ratio, done_steps, total_steps = _chapter_progress_ratio(shots)
    complete_shots = sum(1 for s in shots if not _missing_keys(s))
    st.caption(
        f"Overall: **{done_steps} / {total_steps}** steps complete (**{ratio:.0%}**) · "
        f"**{complete_shots} / {len(shots)}** shots fully done"
    )
    st.progress(ratio)

    st.divider()
    mcols = st.columns(6)
    for col, (key, label, _) in zip(mcols, STEP_DISPLAY):
        n = _count_missing(shots, key)
        col.metric(label.split(". ", 1)[-1], n, help=f"Shots without {STEP_SHORT[key]}")

    complete = sum(1 for s in shots if not _missing_keys(s))
    st.caption(f"**{complete}** of **{len(shots)}** shots have every tracked resource.")

    st.divider()

    filter_key = st.selectbox(
        "Filter",
        options=[k for k, _ in MISSING_FILTER_OPTIONS],
        format_func=lambda k: next(l for kk, l in MISSING_FILTER_OPTIONS if kk == k),
        key="missing_filter",
    )

    filtered = _filter_shots(shots, filter_key)
    st.write(f"**{len(filtered)}** shot(s) match this filter.")

    if not filtered:
        st.success("Nothing missing for this filter.")
        return

    rows = []
    for s in filtered:
        missing = _missing_labels(s)
        rows.append(
            {
                "Shot": s.shot_id,
                "Page": s.page or "—",
                "Layer": s.layer or "—",
                "Missing": ", ".join(missing) if missing else "—",
                "Next step": s.next_step,
                "Done": f"{s.steps_done}/{s.steps_total}",
            }
        )
    _theme_dataframe(rows, _get_theme())

    st.divider()
    st.markdown("**By resource** — quick shot lists")

    rcols = st.columns(2)
    groups = (
        ("panel", "final", "voice"),
        ("still", "video", "lipsync"),
    )
    for col, keys in zip(rcols, groups):
        with col:
            for key in keys:
                missing_shots = [s.shot_id for s in shots if not _step_ok(s, key)]
                label = STEP_SHORT[key]
                if missing_shots:
                    st.markdown(f"**{label}** ({len(missing_shots)})")
                    st.code(", ".join(missing_shots), language=None)
                else:
                    st.markdown(f"**{label}** — all present")


def _stage_badge(ok: bool) -> str:
    return "✓ Ready" if ok else "· Missing"


def _panel_field(d, name: str, fallback: str = "—") -> str:
    value = getattr(d, name, None)
    if value is None or value == "":
        return fallback
    return value


def _render_panel_story_card(d, beat_summary: str = "") -> None:
    """Structured panel view — characters, dialogue, movement, scene."""
    st.markdown(f"**{d.shot_id}** · `{d.page or '—'}` · layer `{d.layer}` · {d.framing}")
    if beat_summary:
        st.caption(f"**{d.beat}** — {beat_summary}")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Characters on-screen**")
        st.write(_panel_field(d, "characters_on_screen"))
    with c2:
        vic = _panel_field(d, "characters_vicinity", "")
        st.markdown("**Nearby / off-panel**")
        st.write(vic if vic else "—")

    st.markdown("**Scene & blocking**")
    st.write(_panel_field(d, "scene_blocking", d.what_we_see))

    st.markdown("**Action & movement**")
    st.write(_panel_field(d, "action_movement"))

    lines = getattr(d, "dialogue_lines", None) or []
    jp = _panel_field(d, "dialogue_jp", "")
    en = _panel_field(d, "dialogue_en", "")
    st.markdown("**Dialogue**")
    if not getattr(d, "has_dialogue", True):
        st.caption("**Silent shot** — no speech balloon; voice / lip-sync skipped in pipeline.")
    elif lines:
        for line in lines:
            st.markdown(f"- {line}")
    elif jp or en:
        if jp:
            st.markdown(f"- **JP** · {jp}")
        if en:
            st.markdown(f"- **EN** · {en}")
    else:
        st.caption("No dialogue listed for this panel in Stage 2.")

    cont = _panel_field(d, "continuity", "")
    if cont and cont != "—":
        st.markdown("**Continuity & notes**")
        st.write(cont)


def _ingest_beat_summary(ingest, beat_id: str) -> str:
    for b in ingest.beats:
        if b.beat_id == beat_id:
            return getattr(b, "summary", "")
    return ""


@getattr(st, "fragment", lambda f: f)
def _render_ingest_page(ingest, shots) -> None:
    st.subheader("Ingest")
    st.caption(
        "Stages 1–3 — chapter story, page inventory, and every panel (shot) from your ingest Markdown."
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Manga pages", len(ingest.page_files))
    shot_details = shot_details_for_display(ingest, shots)
    c2.metric("Shots (Stage 2)", len(shot_details))
    c3.metric("Story beats", len(ingest.beats))
    c4.metric("Timeline layers", len(ingest.layers))
    c5.metric("Bible shot refs", ingest.stage3_shot_refs)

    st.caption(f"**{ingest.title or ingest.chapter_name}** · `{ingest.chapter_dir}`")

    if not ingest.stage1_ok or not ingest.stage2_ok:
        st.warning(
            "Complete **stage_01_ingest.md** and **stage_02_shot_list.md** in your chapter folder. "
            "Use the **manga-chapter-ingest-stages-1-3** skill in Cursor Agent."
        )

    st.divider()

    ingest_section = st.radio(
        "Ingest section",
        ["Story", "Every panel", "Files & stats"],
        horizontal=True,
        key="ingest_main_tab",
        label_visibility="collapsed",
    )

    if ingest_section == "Story":
        st.markdown("**Chapter story**")
        st.caption("Narrative arc from Stage 1 — what changes at each beat and what each manga page covers.")

        if ingest.beats:
            _theme_dataframe(
                [
                    {
                        "Beat": b.beat_id,
                        "After page": getattr(b, "after_page", "—"),
                        "What happens": b.summary,
                    }
                    for b in ingest.beats
                ],
                _get_theme(),
            )
        else:
            st.info("No story beats found in stage_01_ingest.md.")

        st.divider()

        page_inventory = getattr(ingest, "page_inventory", None) or []
        if page_inventory:
            st.markdown("**Page-by-page story**")
            _theme_dataframe(
                [
                    {
                        "Page": p.file,
                        "Order": p.order,
                        "What this page does": p.role,
                    }
                    for p in page_inventory
                ],
                _get_theme(),
            )
        elif ingest.pages:
            st.markdown("**Pages → shots** (from Stage 2)")
            _theme_dataframe(
                [
                    {"Page": p.page, "Shots": p.shot_count, "Beats": p.beats}
                    for p in ingest.pages
                ],
                _get_theme(),
            )

    elif ingest_section == "Every panel":
        st.markdown("**Every panel (shot)**")
        st.caption(
            "Stage 2 ingest — pick **Panel story** to browse who is in frame, what they say, "
            "and how they move. Data comes from `stage_02_shot_list.md`."
        )

        details = shot_details
        if not details:
            st.info(
                "No shots found. Add rows to **stage_02_shot_list.md** in your chapter folder, "
                "then click **Refresh progress**."
            )
        else:
            page_options = ["All pages"] + sorted(
                {d.page for d in details if d.page},
                key=lambda p: p,
            )
            page_filter = st.selectbox("Filter by manga page", page_options, key="ingest_page_filter")
            beat_filter = st.selectbox(
                "Filter by beat",
                ["All beats"] + sorted({d.beat for d in details if d.beat and d.beat != "—"}),
                key="ingest_beat_filter",
            )

            filtered = details
            if page_filter != "All pages":
                filtered = [d for d in filtered if d.page == page_filter]
            if beat_filter != "All beats":
                filtered = [d for d in filtered if d.beat == beat_filter]

            st.caption(f"**{len(filtered)}** shot(s) shown.")

            view_mode = st.radio(
                "View",
                ["Panel story (browse)", "Compact table", "All detail cards"],
                horizontal=True,
                key="ingest_panel_view",
            )

            if view_mode == "Panel story (browse)":
                shot_ids = [d.shot_id for d in filtered]
                st.markdown(
                    _nav_button_row_styles_html(_get_theme(), "ingest_panel_pick"),
                    unsafe_allow_html=True,
                )
                pick_cols = st.columns([1, 4, 1])
                cur_pick = st.session_state.get("ingest_panel_pick", shot_ids[0])
                if cur_pick not in shot_ids:
                    st.session_state.ingest_panel_pick = shot_ids[0]
                cur_idx = shot_ids.index(st.session_state.get("ingest_panel_pick", shot_ids[0]))

                def _ingest_panel_nav(delta: int, ids: list[str]) -> None:
                    i = ids.index(st.session_state.ingest_panel_pick) + delta
                    if 0 <= i < len(ids):
                        st.session_state.ingest_panel_pick = ids[i]

                with pick_cols[0]:
                    st.button(
                        "Previous",
                        key="ingest_panel_prev",
                        type="secondary",
                        use_container_width=True,
                        disabled=cur_idx == 0,
                        on_click=_ingest_panel_nav,
                        kwargs={"delta": -1, "ids": shot_ids},
                    )
                with pick_cols[1]:
                    st.selectbox(
                        "Panel",
                        shot_ids,
                        key="ingest_panel_pick",
                        format_func=lambda sid: next(
                            f"{sid} · {d.page or '—'} · {d.beat}" for d in filtered if d.shot_id == sid
                        ),
                        label_visibility="collapsed",
                    )
                with pick_cols[2]:
                    st.button(
                        "Next",
                        key="ingest_panel_next",
                        type="secondary",
                        use_container_width=True,
                        disabled=cur_idx >= len(shot_ids) - 1,
                        on_click=_ingest_panel_nav,
                        kwargs={"delta": 1, "ids": shot_ids},
                    )

                picked = next(d for d in filtered if d.shot_id == st.session_state.ingest_panel_pick)
                st.divider()
                _render_panel_story_card(picked, _ingest_beat_summary(ingest, picked.beat))

            elif view_mode == "Compact table":
                _theme_dataframe(
                    [
                        {
                            "Shot": d.shot_id,
                            "Page": d.page or "—",
                            "Layer": d.layer,
                            "Characters": _panel_field(d, "characters_on_screen")[:80],
                            "Dialogue": (
                                (d.dialogue_jp or d.dialogue_en or "—")[:80]
                                + ("…" if len(d.dialogue_jp or d.dialogue_en or "") > 80 else "")
                            ),
                            "Action": _panel_field(d, "action_movement")[:80],
                            "Beat": d.beat,
                        }
                        for d in filtered
                    ],
                    _get_theme(),
                )
            else:
                for d in filtered:
                    with st.expander(f"{d.shot_id} · {d.page or '—'} · {d.layer} · {d.beat}"):
                        _render_panel_story_card(d, _ingest_beat_summary(ingest, d.beat))

    else:
        st.markdown("**Stage files**")
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("Stage 1 — Ingest", _stage_badge(ingest.stage1_ok))
        sc2.metric("Stage 2 — Shot list", _stage_badge(ingest.stage2_ok))
        sc3.metric("Stage 3 — Series bible", _stage_badge(ingest.stage3_ok))

        for label, path in (
            ("Stage 1", ingest.stage1_path or f"{ingest.chapter_dir}/stage_01_ingest.md"),
            ("Stage 2", ingest.stage2_path or f"{ingest.chapter_dir}/stage_02_shot_list.md"),
            ("Stage 3", ingest.stage3_path or f"{ingest.chapter_dir}/stage_03_series_bible.md"),
        ):
            st.markdown(f"**{label}:** `{path}`")

        st.divider()

        if ingest.layers:
            st.markdown("**Timeline layers**")
            _theme_dataframe(
                [
                    {
                        "Layer": layer,
                        "Shots": count,
                        "Share": f"{count / max(len(shots), 1):.0%}",
                    }
                    for layer, count in ingest.layers.items()
                ],
                _get_theme(),
            )

        if ingest.stage1_sections:
            st.markdown("**Stage 1 sections**")
            for section in ingest.stage1_sections:
                st.markdown(f"- {section}")

        st.markdown("**What ingest covers**")
        st.markdown(
            "| Stage | File | Purpose |\n"
            "|-------|------|--------|\n"
            "| 1 | `stage_01_ingest.md` | Page order, RTL read path, story beats, continuity |\n"
            "| 2 | `stage_02_shot_list.md` | Per-panel shots (ID, layer, framing, characters) |\n"
            "| 3 | `stage_03_series_bible.md` | Fal prompts, layer prefixes, global negatives |"
        )

    _inject_theme_css(_get_theme())
    st.markdown(
        _nav_button_row_styles_html(_get_theme(), "ingest_panel_pick"),
        unsafe_allow_html=True,
    )


def _shot_label(shot_id: str, shots_by_id: dict) -> str:
    shot = shots_by_id.get(shot_id)
    if shot is not None and not getattr(shot, "has_dialogue", True):
        return f"{shot_id} · silent"
    return shot_id


def _shot_nav(delta: int, shot_ids: list[str], shots_by_id: dict) -> None:
    cur = st.session_state.get("shot_detail_id", shot_ids[0])
    if cur not in shot_ids:
        cur = shot_ids[0]
    skip_silent = st.session_state.get("skip_silent_shots_nav", True)
    idx = shot_ids.index(cur) + delta
    if not skip_silent:
        if 0 <= idx < len(shot_ids):
            _remember_shot(shot_ids[idx])
        return
    step = 1 if delta > 0 else -1
    while 0 <= idx < len(shot_ids):
        candidate = shot_ids[idx]
        if getattr(shots_by_id.get(candidate), "has_dialogue", True):
            _remember_shot(candidate)
            return
        idx += step


def _open_panel_crop(shot_id: str) -> None:
    st.session_state[f"panel_crop_ui_{shot_id}"] = True


def _close_panel_crop(shot_id: str) -> None:
    st.session_state.pop(f"panel_crop_ui_{shot_id}", None)


def _render_panel_crop_tool(shot_id: str, shot, chapter_dir: Path, t: dict[str, str]) -> None:
    """Interactive manga page crop — only for shots missing panels/eng/panel_s###.png."""
    if shot.panel or panel_eng_path(shot_id).is_file():
        return

    ui_key = f"panel_crop_ui_{shot_id}"
    open_key = f"btn_open_panel_crop_{shot_id}"
    anchor_key = f"panel_crop_anchor_{shot_id}"
    close_key = f"btn_close_panel_crop_{shot_id}"
    close_key_2 = f"btn_close_panel_crop_{shot_id}_2"
    save_key = f"save_panel_crop_{shot_id}"
    page_hint = shot.page or "—"

    if not st.session_state.get(ui_key):
        st.caption("Draw a box on the chapter page; saves to `panels/eng/`.")
        st.markdown(_nav_button_row_styles_html(t, anchor_key), unsafe_allow_html=True)
        c_btn, c_anchor, c_spacer = st.columns([1, 4, 1])
        with c_btn:
            st.button(
                "Crop panel from manga page",
                key=open_key,
                use_container_width=True,
                type="secondary",
                on_click=_open_panel_crop,
                kwargs={"shot_id": shot_id},
            )
        with c_anchor:
            st.selectbox(
                "Manga page",
                [page_hint],
                key=anchor_key,
                label_visibility="collapsed",
                disabled=True,
            )
        with c_spacer:
            st.empty()
        return

    try:
        from streamlit_cropper import st_cropper
    except ImportError:
        st.warning("Install **streamlit-cropper** to use in-browser panel crop: `pip install streamlit-cropper`")
        st.markdown(_nav_button_row_styles_html(t, anchor_key), unsafe_allow_html=True)
        c_close, c_mid, c_sp = st.columns([1, 4, 1])
        with c_close:
            st.button(
                "Close",
                key=close_key,
                type="secondary",
                use_container_width=True,
                on_click=_close_panel_crop,
                kwargs={"shot_id": shot_id},
            )
        with c_mid:
            st.selectbox("Manga page", [page_hint], key=anchor_key, label_visibility="collapsed", disabled=True)
        with c_sp:
            st.empty()
        return

    from PIL import Image

    target = panel_eng_path(shot_id)
    st.subheader("Crop panel reference")
    st.caption(
        f"Drag the box to the panel for **{shot_id}**, then save. "
        f"Output: `{_rel_path(target)}`"
    )
    if shot.page:
        st.caption(f"Stage 2 page: `{shot.page}` · Layer: `{shot.layer}` · {shot.beat}")

    page_path = resolve_chapter_page(chapter_dir, shot.page) if shot.page else None
    source: Image.Image | None = None

    if page_path is not None:
        st.caption(f"Source page: `{_rel_path(page_path)}`")
        source = Image.open(page_path)
    else:
        st.caption("Chapter page not found on disk — upload the JPG from your mentor pack.")
        uploaded = st.file_uploader(
            "Manga page",
            type=["jpg", "jpeg", "png"],
            key=f"panel_page_upload_{shot_id}",
            label_visibility="collapsed",
        )
        if uploaded is not None:
            source = Image.open(uploaded)

    if source is None:
        st.markdown(_nav_button_row_styles_html(t, anchor_key), unsafe_allow_html=True)
        c_close, c_mid, c_sp = st.columns([1, 4, 1])
        with c_close:
            st.button(
                "Close",
                key=close_key,
                type="secondary",
                use_container_width=True,
                on_click=_close_panel_crop,
                kwargs={"shot_id": shot_id},
            )
        with c_mid:
            st.selectbox("Manga page", [page_hint], key=anchor_key, label_visibility="collapsed", disabled=True)
        with c_sp:
            st.empty()
        return

    cropped = st_cropper(
        img_file=source,
        realtime_update=True,
        return_type="image",
        key=f"panel_cropper_{shot_id}",
        box_color="#6366f1",
    )

    c_preview, c_actions = st.columns([1, 2])
    with c_preview:
        if cropped is not None:
            st.image(cropped, caption="Preview", width=220)
    with c_actions:
        st.markdown(
            _nav_button_row_styles_html(t, save_key, primary_columns=(1,)),
            unsafe_allow_html=True,
        )
        c_save, c_close = st.columns(2)
        with c_save:
            save = st.button(
                f"Save to `{target.name}`",
                key=save_key,
                type="secondary",
                use_container_width=True,
            )
        with c_close:
            st.button(
                "Close",
                key=close_key_2,
                type="secondary",
                use_container_width=True,
                on_click=_close_panel_crop,
                kwargs={"shot_id": shot_id},
            )

    if save and cropped is not None:
        out = save_panel_crop(shot_id, cropped)
        st.session_state.pop(ui_key, None)
        _refresh_progress()
        _invalidate_shot_prompt(shot_id)
        st.success(f"Saved panel crop: `{_rel_path(out)}`")
        st.rerun()


def _on_character_selected() -> None:
    char_id = st.session_state.get("character_select", "")
    st.session_state.character_detail_id = char_id


def _open_shot_from_character(shot_id: str) -> None:
    st.session_state.studio_page_radio = "Shot detail"
    st.session_state.shot_detail_id = shot_id.upper()
    st.session_state.shot_detail_select = shot_id.upper()


_REFERENCE_SOURCE_ORDER = (
    "Character reference",
    "Bible doc",
    "Panel crop",
    "Approved still",
)


def _render_reference_gallery(refs) -> None:
    if not refs:
        st.info(
            "No reference images found yet. Add portraits under `docs/reference/{character}/`, "
            "create panel crops for related shots, or promote approved stills."
        )
        return

    by_source: dict[str, list] = {}
    for ref in refs:
        by_source.setdefault(ref.source, []).append(ref)

    for source in _REFERENCE_SOURCE_ORDER:
        group = by_source.get(source, [])
        if not group:
            continue
        st.markdown(f"**{source}**")
        cols = st.columns(min(len(group), 4))
        for i, ref in enumerate(group):
            with cols[i % len(cols)]:
                st.image(str(ref.path), caption=ref.caption, use_container_width=True)
                st.caption(_rel_path(ref.path))
        st.markdown("")


def _render_characters_page() -> None:
    st.subheader("Characters")
    st.caption(
        "Character bibles from `docs/` — appearance locks, Qwen personality guides, "
        "and reference images for Fal prompts and voice work."
    )

    characters = list_characters_with_bibles()
    if not characters:
        st.info(
            "No character bibles found. Add `docs/*-appearance-reference.md` or "
            "`docs/*-qwen-personality-guide.md` files, then refresh."
        )
        return

    id_to_char = {c.id: c for c in characters}
    char_ids = [c.id for c in characters]

    default_id = str(st.session_state.get("character_detail_id", "")).lower()
    if default_id not in id_to_char:
        default_id = characters[0].id
    if st.session_state.get("character_select") not in id_to_char:
        st.session_state.character_select = default_id

    st.selectbox(
        "Character",
        char_ids,
        format_func=lambda cid: id_to_char[cid].display_name,
        key="character_select",
        on_change=_on_character_selected,
    )
    selected_id = st.session_state.character_select
    st.session_state.character_detail_id = selected_id
    char = id_to_char[selected_id]
    refs = reference_images_for(char)

    summary_src = char.appearance_doc or char.personality_doc
    summary = extract_one_line_summary(summary_src) if summary_src else ""

    sections = char.available_sections()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Bible sections", len(sections))
    c2.metric(
        "Appearance doc",
        "Yes" if char.appearance_doc and char.appearance_doc.is_file() else "—",
    )
    c3.metric(
        "Personality doc",
        "Yes" if char.personality_doc and char.personality_doc.is_file() else "—",
    )
    c4.metric("Reference images", len(refs))

    if summary:
        st.markdown(f"**Summary:** {summary}")
    if char.voice_note:
        st.caption(f"Voice: {char.voice_note}")

    if char.related_shots:
        st.markdown("**Chapter 81 shots**")
        shot_cols = st.columns(min(len(char.related_shots), 6))
        for i, shot_id in enumerate(char.related_shots):
            with shot_cols[i % len(shot_cols)]:
                st.button(
                    shot_id,
                    key=f"char_shot_{char.id}_{shot_id}",
                    use_container_width=True,
                    on_click=_open_shot_from_character,
                    kwargs={"shot_id": shot_id},
                )

    if refs:
        st.markdown("**Reference images**")
        st.caption(
            "Character portraits, panel crops, and approved stills used in Fal prompts for this cast member."
        )
        _render_reference_gallery(refs)

    st.divider()

    doc_tabs: list[str] = ["Overview"]
    if char.appearance_doc and char.appearance_doc.is_file():
        doc_tabs.append("Appearance")
    if char.personality_doc and char.personality_doc.is_file():
        doc_tabs.append("Personality")
    doc_tabs.append("Reference images")

    tab_widgets = st.tabs(doc_tabs)
    for tab_name, tab in zip(doc_tabs, tab_widgets):
        with tab:
            if tab_name == "Overview":
                st.markdown("**Source files**")
                rows = []
                if char.appearance_doc and char.appearance_doc.is_file():
                    rows.append(
                        {
                            "Type": "Appearance",
                            "Path": _rel_path(char.appearance_doc),
                        }
                    )
                if char.personality_doc and char.personality_doc.is_file():
                    rows.append(
                        {
                            "Type": "Personality",
                            "Path": _rel_path(char.personality_doc),
                        }
                    )
                if char.skill_relpath:
                    skill_path = ROOT / char.skill_relpath
                    if skill_path.is_file():
                        rows.append(
                            {
                                "Type": "Cursor skill",
                                "Path": char.skill_relpath,
                            }
                        )
                if rows:
                    _theme_dataframe(rows, _get_theme())
                else:
                    st.caption("No linked docs.")

                st.markdown("**Sections in this bible**")
                for section in sections:
                    st.markdown(f"- {section}")

            elif tab_name == "Appearance" and char.appearance_doc:
                st.caption(_rel_path(char.appearance_doc))
                body = load_doc_body(char.appearance_doc)
                if body:
                    st.markdown(body)
                else:
                    st.info("Appearance doc is empty.")

            elif tab_name == "Personality" and char.personality_doc:
                st.caption(_rel_path(char.personality_doc))
                body = load_doc_body(char.personality_doc)
                if body:
                    st.markdown(body)
                else:
                    st.info("Personality doc is empty.")

            elif tab_name == "Reference images":
                _render_reference_gallery(refs)


@getattr(st, "fragment", lambda f: f)
def _render_shot_page(shots, t: dict[str, str], chapter_dir: Path) -> None:
    # Re-scan on every run (fragment reruns do not reload main()'s shots argument).
    shots = _reload_shots(chapter_dir)
    if not shots:
        st.warning("No shots listed in stage_02_shot_list.md")
        return

    shot_ids = [s.shot_id for s in shots]
    shots_by_id = {s.shot_id: s for s in shots}
    initial = _resolve_initial_shot(shot_ids)
    if st.session_state.get("shot_detail_id") not in shot_ids:
        _remember_shot(initial)

    if (
        "shot_detail_select" not in st.session_state
        or st.session_state.shot_detail_select not in shot_ids
        or st.session_state.shot_detail_select != st.session_state.shot_detail_id
    ):
        st.session_state.shot_detail_select = st.session_state.shot_detail_id

    def _sync_shot_from_select() -> None:
        _remember_shot(st.session_state.shot_detail_select)

    cur_idx = shot_ids.index(st.session_state.shot_detail_id)

    st.markdown("**Select shot**")
    st.checkbox(
        "Skip silent shots (no dialogue) when using Previous / Next",
        key="skip_silent_shots_nav",
        help="Silent shots stay in the dropdown — e.g. flashback inserts like S034. Mark them in Stage 2 with **Dialogue: none**.",
    )
    st.markdown(_nav_button_row_styles_html(t, "shot_detail_select"), unsafe_allow_html=True)

    c_prev, c_sel, c_next = st.columns([1, 4, 1])
    with c_prev:
        st.button(
            "Previous",
            key="shot_prev",
            use_container_width=True,
            type="secondary",
            disabled=cur_idx == 0,
            on_click=_shot_nav,
            kwargs={"delta": -1, "shot_ids": shot_ids, "shots_by_id": shots_by_id},
        )
    with c_sel:
        st.selectbox(
            "Select shot",
            shot_ids,
            format_func=lambda sid: _shot_label(sid, shots_by_id),
            key="shot_detail_select",
            label_visibility="collapsed",
            on_change=_sync_shot_from_select,
        )
    with c_next:
        st.button(
            "Next",
            key="shot_next",
            use_container_width=True,
            type="secondary",
            disabled=cur_idx == len(shot_ids) - 1,
            on_click=_shot_nav,
            kwargs={"delta": 1, "shot_ids": shot_ids, "shots_by_id": shots_by_id},
        )

    selected = st.session_state.shot_detail_id

    shot = next(s for s in shots if s.shot_id == selected)

    col_left, col_right = st.columns([1, 1])
    wip_counts = _wip_counts(selected)
    total_wip = sum(wip_counts.values())

    with col_left:
        st.subheader(selected)
        if not getattr(shot, "has_dialogue", True):
            st.caption("**Silent shot** — no speech balloon; voice and lip-sync steps are skipped.")
        st.caption(f"Shot folder: `shots/{selected}/` · **{total_wip}** WIP file(s) on disk")
        if shot.page:
            st.write(f"**Page:** `{shot.page}` · **Layer:** `{shot.layer}` · **Beat:** {shot.beat}")
        if shot.summary:
            st.write(shot.summary[:300] + ("…" if len(shot.summary) > 300 else ""))

        missing = _missing_labels(shot)
        if missing:
            st.warning("Missing: " + ", ".join(missing))
        else:
            st.success("All tracked resources present on disk.")

        st.markdown("**Pipeline steps**")
        for key, label, hint in STEP_DISPLAY:
            if not _step_applies(shot, key):
                st.markdown(f"— **{label}** · skipped (no dialogue)")
                continue
            ok = _step_ok(shot, key)
            path = _step_path(shot, key)
            line = f"{_icon(ok)} **{label}**"
            if ok and path:
                rel = _rel_path(path)
                kind = _path_kind(path)
                if kind:
                    line += f" · `{kind}`"
                line += f"\n\n`{rel}`"
                ts = _human_timestamp(path)
                if ts:
                    line += f" · {ts}"
            st.markdown(line)
            if not ok:
                st.caption(hint)
                if key == "final" and _step_ok(shot, "still"):
                    st.caption("WIP still on disk — copy the best WIP into `still/approved/` after QC.")
            elif key in WIP_KINDS and wip_counts.get(key, 0) > 1:
                st.caption(f"{wip_counts[key]} WIP version(s) in folder — latest shown above.")

        st.progress(shot.steps_done / max(shot.steps_total, 1))
        st.caption(f"{shot.steps_done} of {shot.steps_total} steps have a file on disk")

    with col_right:
        _render_shot_media_preview(selected, shot, t)

    if not shot.panel:
        _render_panel_crop_tool(selected, shot, chapter_dir, t)

    if total_wip:
        with st.expander(f"WIP history ({total_wip} files)"):
            for kind in WIP_KINDS:
                files = _wip_files(selected, kind)
                if not files:
                    continue
                st.markdown(f"**{kind}/wip** ({len(files)})")
                for p in files[:8]:
                    ts = _human_timestamp(str(p))
                    st.markdown(f"- `{_rel_path(p)}`" + (f" · {ts}" if ts else ""))
                if len(files) > 8:
                    st.caption(f"… and {len(files) - 8} more under `shots/{selected}/{kind}/wip/`")

    approved_kinds = [k for k in ("still", "voice", "video", "lipsync") if _approved_files(selected, k)]
    if approved_kinds:
        with st.expander("Approved folder"):
            st.caption("QC-passed files live under each `approved/` folder (not a magic filename).")
            for kind in approved_kinds:
                files = _approved_files(selected, kind)
                st.markdown(f"**{kind}/approved** ({len(files)})")
                for p in files:
                    ts = _human_timestamp(str(p))
                    st.markdown(f"- `{_rel_path(p)}`" + (f" · {ts}" if ts else ""))

    st.divider()

    next_key = NEXT_STEP_TO_PROMPT.get(shot.next_step, shot.next_step)
    step_label = NEXT_STEP_LABEL.get(shot.next_step, shot.next_step)
    if shot.next_step == "done":
        st.success("All tracked steps have files. Review quality in Cursor, or pick another shot.")
        prompt = cursor_prompt_for_step(selected, "done")
    else:
        st.subheader(f"Next step: {step_label}")
        prompt = _cursor_prompt_for_shot(shot)

    st.markdown("**Copy into Cursor Agent**")
    st.caption("Edit the prompt if needed, **copy** it, then **paste** into the Cursor Agent chat and press Enter.")

    st.text_area(
        "Cursor Agent prompt",
        height=220,
        label_visibility="collapsed",
        key=_sync_shot_prompt(selected, prompt, shot),
    )
    prompt_key = f"shot_agent_prompt_{selected}"
    prompt_text = st.session_state.get(prompt_key, prompt)

    if hasattr(st, "copy_button"):
        st.markdown(
            _widget_button_styles_html(t, [(f"copy_prompt_{selected}", "primary")]),
            unsafe_allow_html=True,
        )
        st.copy_button(
            "Copy prompt to clipboard",
            prompt_text,
            key=f"copy_prompt_{selected}",
            use_container_width=True,
            type="secondary",
        )
        st.caption("Then switch to Cursor → Agent chat → **Ctrl+V** to paste.")
    else:
        st.info("Select all text in the box above (**Ctrl+A**, **Ctrl+C**), then paste into Cursor Agent (**Ctrl+V**).")

    st.caption(f"Workbook: `{ROOT / 'docs' / 'cursor-student-workbook-en.md'}`")

    with st.expander("All chapter shots"):
        rows = []
        for s in shots:
            rows.append(
                {
                    "Shot": s.shot_id,
                    "Page": s.page,
                    "Panel": _icon(s.panel),
                    "Still": _icon(s.still),
                    "Approved": _icon(s.final),
                    "Voice": "—" if not s.has_dialogue else _icon(s.voice),
                    "Video": _icon(s.video),
                    "Missing": ", ".join(_missing_labels(s)) or "—",
                    "Next": s.next_step,
                    "Dialogue": "yes" if s.has_dialogue else "silent",
                }
            )
        _theme_dataframe(rows, _get_theme())

    _inject_theme_css(_get_theme())
    st.markdown(_shot_detail_button_styles_html(t, selected), unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(
        page_title="AI Animation Studio",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _init_session_state()
    _apply_url_to_session()
    _inject_theme_css(_get_theme())

    chapter = find_chapter_dir()
    try:
        if chapter is None:
            with st.sidebar:
                st.header("AI Animation Studio")
                _render_theme_toggle()
            st.error(
                "Chapter folder not found. Copy **Chapter-81/** from your mentor pack into the project root."
            )
            _inject_theme_css(_get_theme())
            return

        with st.sidebar:
            st.header("AI Animation Studio")
            _render_theme_toggle()
            _render_sidebar_menu(_get_theme())
            st.divider()
            st.markdown("**How to use**")
            st.markdown(
                "1. **Progress** — `shots/S###/` pipeline files\n"
                "2. **Ingest** — Stages 1–3 chapter summary\n"
                "3. **Shot detail** — paths, previews, Cursor prompt\n"
                "4. **Characters** — appearance & personality bibles\n"
                "5. **Copy** the prompt → **paste** into Cursor Agent chat\n"
                "6. Files on disk update automatically — use **Refresh progress** if a view looks stale\n"
                "7. Promote WIP → approved: `python scripts/promote_artifact.py`"
            )
            st.button(
                "Refresh progress",
                key="refresh_progress",
                on_click=_refresh_progress,
                use_container_width=True,
            )

        page = _current_page()

        progress = _scan_chapter_live(chapter)
        shots = progress.shots

        if not shots and page in ("Progress", "Shot detail"):
            st.warning("No shots listed in stage_02_shot_list.md")
            return

        if page == "Progress":
            st.caption(
                "Read-only progress view — copy prompts into Cursor Agent to generate. "
                "No Fal calls from this page."
            )
            finals = sum(1 for s in shots if s.final)
            videos = sum(1 for s in shots if s.video)
            incomplete = sum(1 for s in shots if _missing_keys(s))
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Chapter shots", len(shots))
            c2.metric("Approved stills", finals)
            c3.metric("Videos", videos)
            c4.metric("Shots incomplete", incomplete)
            st.divider()
            _render_progress_page(shots)
        elif page == "Ingest":
            ingest = _load_ingest_summary(str(chapter), st.session_state.scan_cache_version)
            _render_ingest_page(ingest, shots)
        elif page == "Characters":
            _render_characters_page()
        else:
            _render_shot_page(shots, _get_theme(), chapter)

        _sync_session_to_url()
    finally:
        # Last in DOM — overrides Streamlit header, icons, menus, and toggle.
        t = _get_theme()
        _inject_theme_css(t)
        page = _current_page()
        if page == "Shot detail" and chapter is not None:
            shot_id = str(st.session_state.get("shot_detail_id", "")).upper()
            if shot_id:
                st.markdown(
                    _shot_detail_button_styles_html(t, shot_id),
                    unsafe_allow_html=True,
                )
        elif page == "Ingest":
            st.markdown(
                _nav_button_row_styles_html(t, "ingest_panel_pick"),
                unsafe_allow_html=True,
            )


if __name__ == "__main__":
    main()
