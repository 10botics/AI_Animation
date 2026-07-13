# Pipeline dashboard — design log (future reference)

**Status:** Beginner demo implemented (`Start-Studio.bat`, `scripts/beginner_dashboard.py`)  
**Logged:** 2026-07-09  
**Context:** Discussion on running AI_Animation outside vs inside Cursor, and whether a progress UI should duplicate Agent chat.

---

## Summary

Build **two surfaces over one shared progress engine**, not a standalone app that replaces Cursor:

| Surface | Audience | Role |
|---------|----------|------|
| **Browser dashboard** (“AI Animation Studio”) | Beginner learners (10botics) | Guided, pretty, lesson-scoped; copy prompts into Cursor Agent |
| **Cursor Canvas board** (“Pipeline board”) | Mentors / professionals | Dense, IDE-native, full chapter (91 shots); click shot → pre-fill Agent |

**Cursor Agent stays the brain** (skills, ingest, prompts, script runs, Fal failure recovery).  
**Scripts stay the execution layer** (`generate_*_ref_edit.py`, I2V, dialogue, lip-sync).  
**Dashboard(s) are mission control** — read progress, spot gaps, launch the next step.

**Do not** embed a full chatbox in either surface. Avoid alt-tab awkwardness by putting the **pro board inside Cursor** (Canvas beside chat), not by cloning chat in the browser.

---

## Problem this solves

Chapter 81 has **91 shots** across **18 pages**, each with multiple artifacts:

- Panel crop (`panels/eng/panel_s###.png`)
- WIP still (`Tests/`)
- Approved Final (`Tests/Final/`)
- Voice (`outputs/voice/…`)
- Video (`outputs/video/…`)
- Lip-sync outputs
- Optional QC (`Chapter-81/stage_04_s###_visual_qc_log.md`)

Progress is scattered across folders and JSON logs under `outputs/fal/`. Chat and folder spelunking do not scale.

---

## Architecture

```text
┌─────────────────────────────────────────────────────────┐
│  LEARNER: Browser Studio    │  PRO: Cursor Canvas board │
│  (guided, one shot)         │  (grid, filters, density)  │
└──────────────┬──────────────┴──────────────┬───────────┘
               │                             │
               ▼                             ▼
        ┌──────────────────────────────────────────┐
        │  Shared progress scanner (Python module)  │
        │  Parse stage_02 + scan panels/Tests/      │
        │  outputs/ → status JSON per S###          │
        └──────────────────┬───────────────────────┘
                           │
     ┌─────────────────────┼─────────────────────┐
     ▼                     ▼                     ▼
Chapter-81/           scripts/              Cursor Agent
stage_01–03           → Fal.ai              + .cursor/skills/
```

**Single source of truth:** filesystem + markdown canon (not a separate database).  
**Optional later:** `outputs/progress.json` or `progress.local.json` for mentor approvals and notes; both UIs read the same file.

---

## Shared progress scanner (implement first)

One module (e.g. `scripts/pipeline_status.py`) should:

1. Parse shot IDs and metadata from `Chapter-81/stage_02_shot_list.md` (page, layer, beat, framing).
2. Check existence / latest file per artifact type per shot.
3. Read latest `outputs/fal/*S###*_meta_*.json` for timestamps, model, errors.
4. Flag blockers (e.g. video without voice; ingest notes from `stage_01`; MS two-face → Kling routing hint from skills).
5. Emit JSON for both UIs.

Scripts already write structured metadata (example: `generate_s006_ref_edit.py` → `outputs/fal/S006_ref_edit_meta_*.json`).

---

## Browser — learner mode (“AI Animation Studio”)

**Goals:** Low intimidation, workbook-aligned, projector-friendly.

**UX:**

- Simple pipeline labels: **Picture → Voice → Video → Lip-sync** (map to Stage 4–5 + dialogue + PixVerse).
- **One shot at a time** by default (e.g. S006 lesson); mentor can unlock full chapter later.
- Large status chips, thumbnails (panel vs Final vs latest video).
- **Copy prompt for Cursor** — pre-filled skill name + `@files`; no full chat clone.
- Friendly empty states with workbook PDF links (`docs/cursor-student-workbook-en*.pdf`).
- **Read-only by default** — no Fal calls from browser unless mentor enables “Run script.”

**Visual target:** Modern app feel — **React + Tailwind/shadcn** if polish matters; Streamlit only for fast prototype (utilitarian).

**Stack note:** Runs locally (`localhost`); reads project root; does not need `FAL_KEY` to browse.

---

## Cursor Canvas — pro mode (“Pipeline board”)

**Goals:** Same window as Agent; maximum information density.

**UX:**

- Full **91-shot grid** with filters: page (`017.jpg`), beat (B16), layer (`present` / `fb_hero`).
- Compact cards: panel / Final / voice / video / lip-sync / QC chips.
- **Click shot → pre-fill Agent prompt** (skill + `@stage_02`, `@panel_s###`, etc.).
- Blockers panel (Seedance `generated_video`, WAV longer than clip, missing `panels/jap/` for dialogue).
- Thumbnail strip + link to latest Fal JSON log.
- Flat, minimal — **Cursor theme tokens**; no gradients/shadows per Canvas design policy.

**Location:** `.canvas.tsx` in Cursor-managed `canvases/` directory (IDE compiles beside chat).

---

## Cursor connection (no duplicate chat)

| Do | Don't |
|----|--------|
| Pre-fill prompts and `@file` lists | Full multi-turn chat in dashboard |
| “Continue in Cursor Agent” as primary action | Second LLM + API key in browser |
| Optional: clipboard + focus Cursor | Re-implement `.cursor/skills/` in UI |
| Later: MCP server exposing shot status to Agent | Standalone exe replacing Cursor |

---

## QOL features (backlog)

**Navigation:** Search S###; “Next incomplete shot” in story order; page → shots jump.

**Media:** Inline PNG/MP4/WAV; side-by-side panel vs Final vs video frame; mark hero Final for I2V.

**Production:** Fal log viewer; rough credit estimate from duration/model; assembly order preview (Stage 6).

**Ingest:** Page wizard with RTL reminder; highlight rows missing Layer or on-screen characters; diff stage_02 vs `fal_common.py` shots.

**Collaboration:** Mentor `approved` flag per artifact; per-shot notes (“retry Kling near-static”).

---

## Naming (recommended)

| Context | Term |
|---------|------|
| Student-facing | **AI Animation Studio** (browser) |
| Pro / in-IDE | **Pipeline board** (Canvas) |
| Technical docs | **progress dashboard** / **pipeline UI** |
| Avoid alone | “Interface,” “Portal” |

Use **dashboard** or **board** in conversation; **UI** in README/dev notes.

---

## Build order (when implementing)

1. **`pipeline_status.py`** — scanner + CLI `python pipeline_status.py --json` (dogfood in terminal).
2. **Cursor Canvas v1** — grid + filters + copy Agent prompt (pros validate data).
3. **Browser v1** — learner skin on same JSON; S006-only mode + workbook links.
4. Optional: `progress.local.json` for approvals; MCP for Agent queries; React polish pass on browser.

---

## Related repo paths

| Path | Role |
|------|------|
| [`manga-to-anime-fal-stages.plan.md`](../manga-to-anime-fal-stages.plan.md) | End-to-end stages |
| [`docs/cursor-student-workbook-en.md`](cursor-student-workbook-en.md) | Learner workflow (Agent + skills) |
| [`.cursor/skills/`](../.cursor/skills/) | Agent playbooks (ingest, Nano, I2V, dialogue) |
| [`scripts/build_mentor_pack_zip.py`](../scripts/build_mentor_pack_zip.py) | Offline handout pack |
| [`README.md`](../README.md) | Script-first quick start (works without dashboard) |

---

## Decisions recorded (2026-07-09)

1. **Keep Cursor in the pipeline** — dashboard supplements, does not replace Agent.
2. **Dual UI is intentional** — browser for learners, Canvas for professionals; one scanner backend.
3. **No chat mimic in browser** — prompt composer + copy to Cursor; pro board lives beside real chat.
4. **Standalone .exe / full external app** — deprioritized vs shared scanner + two skins.
5. **Prettiest learner UX** → browser React; **integrated pro UX** → Cursor Canvas (minimal, IDE-native).

---

## Revision log

| Date | Change |
|------|--------|
| 2026-07-09 | Beginner Streamlit demo + `pipeline_status.py` + `Start-Studio.bat` |
