---
name: manga-chapter-ingest-stages-1-3
description: Builds or audits Stages 1–3 manga ingestion for AI_Animation — page inventory, Japanese RTL panel order, story beats, per-panel shot list with explicit character/on-screen and vicinity fields, continuity, and series bible handoff for Fal stills. Use when ingesting a new chapter folder, fixing shot order, gutter/timeline tags, expanding stage_01_ingest.md, stage_02_shot_list.md, stage_03_series_bible.md, or when the user mentions ingest, story beats, panel order, RTL, shot IDs, or who is in frame / near the action.
---

# Manga chapter ingest — Stages 1–3 (AI_Animation)

## Role

Turn raw chapter **`NNN.jpg`** pages under a `Frierien-chapter*` (or equivalent) folder into **maintained Markdown**:

| Stage | File | Purpose |
|-------|------|---------|
| **1** | `Frierien-chapterNNN/stage_01_ingest.md` | Page order, **manga read path** (RTL), gutter/timeline notes, **beats B1…**, chapter casting/location continuity |
| **2** | `.../stage_02_shot_list.md` | **Shot table** per page: ID, Layer, Framing, Beat, **Characters**, “What we see”, Continuity |
| **3** | `.../stage_03_series_bible.md` | Layer prefixes, global negatives, **per-shot Fal kit** (feeds [`nano-banana-2-prompting`](../nano-banana-2-prompting/SKILL.md)) |

Downstream **Stage 4** still prompts consume this ingest as **story truth** — [`.cursor/skills/nano-banana-2-prompting/SKILL.md`](../nano-banana-2-prompting/SKILL.md) + [`docs/flux-2-pro-prompting-guide.md`](../../../docs/flux-2-pro-prompting-guide.md) (edit-flow lessons; Nano default on Fal).

---

## Workflow (do in order)

### A. Chapter scope

1. Set **chapter root** (e.g. `Frierien-chapter081/`).
2. List **`001.jpg` … `NNN.jpg`** in **reading order** (zero-padded sort); note title splash vs story start/end.
3. Record **source / RTL audit date** in Stage 1 header.

### B. Panel read path (mandatory)

- **Japanese manga:** within each page, order panels **right → left** within a row/strip, **top → bottom** down the page — **not** Western LTR by x-position.
- **Verify** ambiguous grids with **speech-bubble sequence** or JP original if available.
- If Stage 2 rows were ever built LTR, **re-walk** the page and fix shot order + any page-level note (see ch.81 `002.jpg`–`004.jpg` examples in [stage_02_shot_list.md](../../../Frierien-chapter081/stage_02_shot_list.md)).

### C. Story progression

1. Define **beats** B1… (narrative hinges): what **shifts** after each page or tier — [stage_01_ingest.md](../../../Frierien-chapter081/stage_01_ingest.md) §3 pattern.
2. Map each beat to pages in Stage 1; map each **panel** to one **shot ID** (`Sxxx`) in Stage 2.
3. Tag **`Layer`** per shot: `present`, `cold_open`, `fb_denken`, `fb_couple`, `fb_macht`, `fb_hero`, etc. — from **dialogue + wardrobe + story**, not from gutter color alone (gutters are cues; see Stage 1 gutter subsection for ch.81).

### D. Characters per panel (required field)

For every shot row in Stage 2, include **explicit character coverage** so Stage 4 / anime refs do not invent or drop cast.

Use one of these patterns (pick one and stay consistent in the table):

**Option 1 — dedicated column**

| … | **Characters (on-screen)** | **Characters (vicinity)** | What we see | … |
|---|------------------------------|---------------------------|-------------|---|
| … | Frieren, Fern, Stark | — | … | … |

**Option 2 — sub-bullets inside “What we see” or Continuity**

- **On-screen:** …
- **Vicinity / implied:** party camp off-panel L; speaker from adjacent panel; crowd in town square, etc.

**Rules**

- **On-screen:** every **visible** named figure or clear silhouette.
- **Vicinity:** anyone **not drawn in the panel** but **story-logical** nearby (rest of party, warden down the path, combatants heard off-panel). Needed for **wide establishing** edits and **reverse angles** later.
- **Creatures / messengers / summons** count as characters.
- If a beat **requires** a character for continuity, note them in **Continuity** even when off-screen.

### E. Stage 1 body sections (template)

Mirror [stage_01_ingest.md](../../../Frierien-chapter081/stage_01_ingest.md):

1. Page inventory table  
2. **Manga panel read path** warning (RTL)  
3. Gutter / tier cues if the scan uses them  
4. Chapter boundaries  
5. Story beats table  
6. Continuity / casting (chapter-wide)  
7. Debugging log + Stage 2 handoff checklist  

### F. Stage 2 row fields (minimum)

| Field | Content |
|-------|---------|
| **ID** | `Sxxx` |
| **Layer** | timeline / mood bucket |
| **Framing** | WS, MS, CU, OTS, … |
| **Beat** | Bn |
| **Characters** | on-screen + vicinity (see §D) |
| **What we see** | blocking, props, dialogue beat |
| **Continuity** | wardrobe, ref `panels/panel_sxxx.png`, VFX notes |

Per-page **summary table** (page → shot count → beats) helps audits.

### G. Stage 3

- **Inputs:** locked Stage 2.  
- **Outputs:** global negatives, **layer prefixes**, per-shot Fal bullets pointing to `fal_common.py` / `generate_*_ref_edit.py` where scripted.

### H. Verification (copy)

```markdown
## Ingest verification — Stages 1–3
- [ ] Every page file accounted for; boundaries clear
- [ ] Panel order on each multi-panel page follows **RTL** + balloons; suspicious LTR legacy re-checked
- [ ] Each shot has **Beat** + **Layer** + **Characters (on-screen | vicinity)**
- [ ] Gutter/tier pages: **Layer** matches story, not gutter color alone
- [ ] Stage 2 → Stage 3 chain consistent; refs `panels/panel_s*.png` noted where crops exist
- [ ] Handoff: downstream agents read [`nano-banana-2-prompting`](../nano-banana-2-prompting/SKILL.md) only **after** this ingest is trusted
```

---

## Handoff template

```text
Task: Ingest chapter <N> or audit <page>.jpg
Use skill: manga-chapter-ingest-stages-1-3
Steps: (1) Stage 1 page list + RTL + beats (2) Stage 2 full shot table with Characters on-screen/vicinity (3) Stage 3 bible sync (4) Run verification block (5) Log surprises in Stage 1 §debug
```

## Related paths

| Path | Role |
|------|------|
| `Frierien-chapter081/stage_01_ingest.md` | Reference Stage 1 |
| `Frierien-chapter081/stage_02_shot_list.md` | Reference Stage 2 + legend |
| `Frierien-chapter081/stage_03_series_bible.md` | Reference Stage 3 |
| `docs/flux-2-pro-prompting-guide.md` | Stage 4 edit lessons (name historical) |
| `.cursor/skills/nano-banana-2-prompting/SKILL.md` | Stage 4 still workflow |
| `manga-to-anime-fal-stages.plan.md` | Full pipeline diagram |
| `.cursor/skills/manga-panel-crop-for-shots/SKILL.md` | **Extract** `panels/panel_s###.png` from `NNN.jpg` per shot |
