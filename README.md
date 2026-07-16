# AI Animation — Manga to anime (Fal.ai pipeline)

Personal workflow for turning ordered **manga chapter** material into **anime-style stills** and **short motion clips** using **[Fal.ai](https://fal.ai)** — with story, shot identity, and prompts kept in versioned markdown instead of ad-hoc copy-paste.

The repo ships **pipeline code and docs** only. **Chapter folders** live under **`Comic Source/`** (page scans, `stage_01`–`stage_03`, QC logs) — **gitignored**; add a new `Chapter-NN/` per comic chapter you work on.

## What this repo is

| Piece | Role |
|--------|------|
| **Stages 1–3** (local `Comic Source/Chapter-NNN/stage_01_ingest.md`, …) | Canon for page order, beats, shots (**S00x**), and style notes — **not in git** |
| **`panels/eng/panel_s###.png`** | Single-panel crops used as **edit references** for Nano Banana |
| **`scripts/fal_common.py`** | Shared **`S###_PROMPT_FLUX`** bodies (one string per shot for all backends) |
| **`scripts/generate_s006_*.py`** | **Examples** in git — copy/adapt per shot with Cursor Agent |
| **`scripts/generate_s###_*.py`** | Other shots — **local only** (gitignored); add as you work each scene |
| **`Tests/Final/`** | “Hero” stills you approve for defaults and I2V drivers |
| **`docs/`** | Prompting guides, greyscale→color notes, Stage 5 handbook |

**Mentor pack (not on GitHub):** run `python scripts/build_mentor_pack_zip.py` → extract into project root. Creates **`Comic Source/Chapter-81/`**, `Voice Reference/`, and `.env` with blank `FAL_KEY=`. Add more chapters as sibling folders under **`Comic Source/`**. Students create `panels/`, `shots/`, and `outputs/` during the lesson.

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

From the repo root, run the **S006** example (copy this pattern for other shots):

```powershell
cd scripts
python generate_s006_ref_edit.py
```

- Default **`--ref`** is `panels/eng/panel_s006.png` (create the crop locally or via the dashboard).
- Default model is **`nano-banana-2-edit`**; some scripts support **`--model flux-2-pro-edit`** for legacy runs.

Outputs land under `shots/S006/still/wip/` (see script stdout).

## Quick start — one clip (Stage 5)

Use an approved PNG (often under `Tests/Final/`) as **`--start-image`** when the script’s default differs:

```powershell
cd scripts
python generate_s006_kling_i2v.py --start-image "..\shots\S006\still\approved\<timestamp>.png"
```

See [`docs/stage5-image-to-video-fal.md`](docs/stage5-image-to-video-fal.md) for model id, **`duration`**, **`negative_prompt`**, and cost notes.

## Beginner dashboard (AI Animation Studio)

Local progress board for learners — **no Streamlit account**. Read-only; copy prompts into Cursor Agent to generate.

```powershell
# One-click (creates .venv + installs deps on first run):
.\Start-Studio.bat

# Second instance on another port (and optional chapter):
.\Start-Studio.bat 8502
.\Start-Studio.bat 8502 Chapter-82
# or double-click Start-Studio-8502.bat

# Or set in .env: STUDIO_PORT=8502  and  STUDIO_CHAPTER=Chapter-82

# Or manually:
python scripts/start_studio.py --port 8502 --chapter Chapter-82
```

Pick the active chapter in the **sidebar** when several folders exist under `Comic Source/`.

CLI progress scan: `python scripts/pipeline_status.py --shot S006`

## Repository layout (short)

```
Comic Source/          # Local only — one folder per chapter (Chapter-81/, Chapter-82/, …)
panels/                # Per-shot manga crops (gitignored)
shots/                 # Per-shot production files (gitignored) — see below
scripts/               # fal_common.py + generate_* + artifact_paths.py
docs/                  # Prompting / pipeline docs
Tests/                 # Legacy still WIP/Final (optional after migration)
outputs/               # Fal logs, SFX, analysis (gitignored)
.cursor/skills/        # Cursor Agent Skills for prompts + ingest
```

### Shot folders (`shots/S###/`)

Each shot keeps **WIP history** under `wip/{model}/` (UTC timestamp filenames: **`YYYYMMDD_HHMMSS`**) and **fixed approved paths** for the next pipeline step:

| Step | WIP example | Approved |
|------|-------------|----------|
| Still | `still/wip/nano-banana-2/20260330_035743.png` | `still/approved/20260330_035743.png` |
| Voice | `voice/wip/qwen/frieren_20260710_091920.wav` | `voice/approved/frieren.wav` |
| Video | `video/wip/seedance-2/20260527_054046.mp4` | `video/approved/20260527_054046.mp4` |
| Lip-sync | `lipsync/wip/pixverse/20260604_045309.mp4` | `lipsync/approved/20260604_045309.mp4` |
| SFX (per shot) | `sfx/wip/cassetteai/01_ambient_20260402_043520.wav` | — |
| BGM (chapter) | `audio/bgm/wip/minimax/prototype_20260529_075424.mp3` | `audio/bgm/approved/prototype_20260529_075424.mp3` |

Normalize existing media into this layout:

```powershell
python scripts/normalize_artifacts.py
```

## Cursor / contributors

**Students / interns:** [`docs/cursor-student-workbook.md`](docs/cursor-student-workbook.md) — [Cursor guide PDF](docs/cursor-student-workbook-en-cursor-guide.pdf) → [Setup PDF](docs/cursor-student-workbook-en-setup.pdf) → [S006 PDF](docs/cursor-student-workbook-en-s006-first-try.pdf) → [Skills reference](docs/cursor-student-workbook-en.pdf) · [粵語](docs/cursor-student-workbook-yue.md).

Agent-oriented workflows live in **`.cursor/skills/`** (e.g. nano-banana prompting, panel crops, I2V motion wording). They assume you keep **Stages 1–3** truthful before trusting `fal_common.py` for a given **S###**.

**Future (demo):** beginner **AI Animation Studio** — double-click `Start-Studio.bat` or run `streamlit run scripts/beginner_dashboard.py`; design log [`docs/pipeline-dashboard-design-log.md`](docs/pipeline-dashboard-design-log.md).

## Legal / IP

This project is tooling and documentation for **personal or research** use. **Manga scans**, character designs, and trademarks belong to their **rights holders**. Do not share copyrighted raws or API keys in public repos.

## License

Specify your license here (e.g. MIT) if you intend others to reuse the **scripts and docs**; manga-derived assets are **not** implied to be redistributable.
