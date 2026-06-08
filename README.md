# AI Animation — Manga to anime (Fal.ai pipeline)

Personal workflow for turning ordered **manga chapter** material into **anime-style stills** and **short motion clips** using **[Fal.ai](https://fal.ai)** — with story, shot identity, and prompts kept in versioned markdown instead of ad-hoc copy-paste.

The repo ships **pipeline code and docs** only. **Chapter folders** (page scans, `stage_01`–`stage_03`, QC logs) stay **local and gitignored** — create a new `Frierien-chapterNNN/` or `Chapter-NN/` per manga chapter you work on.

## What this repo is

| Piece | Role |
|--------|------|
| **Stages 1–3** (local `Frierien-chapterNNN/stage_01_ingest.md`, `stage_02_shot_list.md`, `stage_03_series_bible.md`) | Canon for page order, beats, shots (**S00x**), and style notes — **not in git** |
| **`panels/eng/panel_s###.png`** | Single-panel crops used as **edit references** for Nano Banana |
| **`scripts/fal_common.py`** | Shared **`S###_PROMPT_FLUX`** bodies (one string per shot for all backends) |
| **`scripts/generate_s###_ref_edit.py`** | Stage **4**: image edit (**Nano Banana 2** by default) → PNG under `Tests/` |
| **`scripts/generate_s###_kling_i2v.py`** | Stage **5** (optional): **Kling 2.6 Pro** image-to-video → MP4 under `outputs/video/` |
| **`Tests/Final/`** | “Hero” stills you approve for defaults and I2V drivers |
| **`docs/`** | Prompting guides, greyscale→color notes, Stage 5 handbook |

End-to-end stage intent is also summarized in [`manga-to-anime-fal-stages.plan.md`](manga-to-anime-fal-stages.plan.md).

## Requirements

- **Python 3.10+** (tested with typical 3.x installs)
- A **[Fal.ai API key](https://fal.ai/dashboard/keys)** (`FAL_KEY`)

## Setup

```powershell
cd <path-to-this-repo>
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit **`.env`** and set `FAL_KEY=` to your key. **Never commit `.env`** (it is gitignored).

## Quick start — one still (Stage 4)

From the repo root, run a shot’s edit script (example **S009**):

```powershell
cd scripts
python generate_s009_ref_edit.py
```

- Default **`--ref`** is `panels/eng/panel_s009.png` unless the script docstring says otherwise.
- Default model is **`nano-banana-2-edit`**; some scripts support **`--model flux-2-pro-edit`** for legacy runs.

Outputs land under `Tests/` and `outputs/fal/` (see script stdout).

## Quick start — one clip (Stage 5)

Use an approved PNG (often under `Tests/Final/`) as **`--start-image`** when the script’s default differs:

```powershell
cd scripts
python generate_s009_kling_i2v.py --experiment 3 --start-image "..\Tests\Final\S009_nano-banana-2-edit_20260330T055707Z.png"
```

See [`docs/stage5-image-to-video-fal.md`](docs/stage5-image-to-video-fal.md) for model id, **`duration`**, **`negative_prompt`**, and cost notes.

## Repository layout (short)

```
Frierien-chapterNNN/   # Local only — pages + stage_01–03 + stage_04 QC (gitignored)
panels/                # Per-shot manga crops (gitignored)
scripts/               # fal_common.py + generate_*_ref_edit.py + generate_*_kling_i2v.py
docs/                  # Prompting / pipeline docs
Tests/Final/           # Approved hero stills (gitignored)
outputs/               # Generated logs, JSON, video (gitignored)
.cursor/skills/        # Cursor Agent Skills for prompts + ingest
```

## Cursor / contributors

**Students / interns:** [`docs/cursor-student-workbook.md`](docs/cursor-student-workbook.md) — [Cursor guide PDF](docs/cursor-student-workbook-en-cursor-guide.pdf) → [Setup PDF](docs/cursor-student-workbook-en-setup.pdf) → [S006 PDF](docs/cursor-student-workbook-en-s006-first-try.pdf) → [Skills reference](docs/cursor-student-workbook-en.pdf) · [粵語](docs/cursor-student-workbook-yue.md).

Agent-oriented workflows live in **`.cursor/skills/`** (e.g. nano-banana prompting, panel crops, I2V motion wording). They assume you keep **Stages 1–3** truthful before trusting `fal_common.py` for a given **S###**.

## Legal / IP

This project is tooling and documentation for **personal or research** use. **Manga scans**, character designs, and trademarks belong to their **rights holders**. Do not share copyrighted raws or API keys in public repos.

## License

Specify your license here (e.g. MIT) if you intend others to reuse the **scripts and docs**; manga-derived assets are **not** implied to be redistributable.
