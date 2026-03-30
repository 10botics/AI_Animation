---
name: nano-banana-2-prompting
description: Authors and edits Fal.ai Nano Banana 2 image-edit prompts for the AI_Animation manga-to-anime pipeline (Frieren ch.81). Covers manga panel reference crops (panels/panel_s###.png), reference-first lead-ins, shared PROMPT_FLUX bodies, multi-image image_urls compositing, aspect_ratio and resolution, and QC handoff. Use when editing fal_common.py or generate_*_ref_edit.py, changing S002/S003/S010/S075/S076 stills, creating or fixing panel crops for --ref, camp/squirrel variants, or when the user mentions Nano Banana, nano-banana-2/edit, Fal image edit, panel reference, or stage 4 still generation.
---

# Nano Banana 2 prompting (AI_Animation)

## Role

Default **still** backend: **`fal-ai/nano-banana-2/edit`** on Fal ([API](https://fal.ai/models/fal-ai/nano-banana-2/edit/api)). The model consumes **`prompt`** + **`image_urls`** (one or more uploads). **Do not** default new chapter work to Flux; legacy `--model flux-2-pro-edit` exists only on request.

**Upstream (Stages 1–3):** Author or audit **`stage_01_ingest.md` → `stage_02_shot_list.md` → `stage_03_series_bible.md`** with [`.cursor/skills/manga-chapter-ingest-stages-1-3/SKILL.md`](../manga-chapter-ingest-stages-1-3/SKILL.md) before trusting **`fal_common.py`** for a shot — especially **RTL panel order**, **beats**, and **characters on-screen vs vicinity**.

**Manga reference crop (before Fal):** If **`panels/panel_s###.png`** is missing, stale, or **`--ref`** would point at a full **`NNN.jpg`** while Stage 2 has **multiple panels** on that page, follow [`.cursor/skills/manga-panel-crop-for-shots/SKILL.md`](../manga-panel-crop-for-shots/SKILL.md) — **wrong or missing crops dominate edit failures** (composition, chirality, tier bleed).

## Before changing any prompt text

1. **Reference:** For the target **S###**, confirm a correct **single-panel** PNG exists at **`panels/panel_s0xx.png`** and matches **`stage_02`** (see [`.cursor/skills/manga-panel-crop-for-shots/SKILL.md`](../manga-panel-crop-for-shots/SKILL.md)). Fix the crop before tuning prompt copy when the upload is wrong.
2. Skim BFL [**FLUX.2 prompting guide**](https://docs.bfl.ai/guides/prompting_guide_flux2) for **ordering and tone** (subject → action → style → context; **positive** descriptions; short negations; scope color words like white/blue to the correct role). Same habits apply to Nano copy even though the stack differs.
3. Read **`docs/flux-2-pro-prompting-guide.md`** — shared **edit** lessons, shot pitfalls, file roles (name is historical; guide is backend-agnostic for text).
4. Read **`docs/manga-greyscale-to-color.md`** when tuning **color, materials, or light** from a **greyscale manga** ref — how screentones/lines encode **matte vs specular**, mapping values to **per-surface hue locks**, and **reference anchoring** pitfalls (especially useful before rewriting `*_PROMPT_FLUX` or lead-ins for mood washes).
5. Confirm call shape: concatenated string = **`*_EDIT_LEAD_IN`** (in `scripts/generate_*_ref_edit.py`) + **`*_PROMPT_FLUX`** (in `scripts/fal_common.py`). The `PROMPT_FLUX` filename is historical; **one** body string for all backends.

## API mapping (implementation)

| Fal field | Typical use |
|-----------|-------------|
| `prompt` | Full edit string (lead-in + body). |
| `image_urls` | List of HTTPS URLs; order matters for multi-ref (e.g. camp plate, then squirrel design). |
| `aspect_ratio` | Chapter keys often **`16:9`**; **`9:16`** only if QC says it stabilizes layout. |
| `resolution` | **`1K`** default tests; **`2K`**/`4K` when delivery needs it. |
| `output_format` | **`png`** in scripts. |
| `limit_generations` | **`true`** in project scripts. |

Upload locals with `fal_client.upload_file(path)` then pass returned URLs.

## Edit pipeline (chapter shots)

1. **Panel ref:** Ensure **`panels/panel_s0xx.png`** for this shot matches **`stage_02`** / source **`NNN.jpg`** ([`manga-panel-crop-for-shots`](../manga-panel-crop-for-shots/SKILL.md)). Scripts’ **`--ref`** should default to that path unless Stage 2 documents a deliberate full-page exception.
2. **Lead-in:** Uploaded reference wins **pose, depth, headcount**; strip manga **balloons/halftone/gutters**; narration text must not replace blocking.
3. **Body (`fal_common.py`):** Layer **subject → lighting → staging → cast**; per-garment color locks when the scene has a strong wash (e.g. global blue flowers). Ground **material/light color** choices in **`docs/manga-greyscale-to-color.md`** when the upload is **B&W manga**.
4. **Manga:** Prefer **single-panel** `--ref` (e.g. `panels/panel_s0xx.png`); never treat a full `NNN.jpg` page as one composition unless ingest proves it.
5. **Multi-reference:** State in lead-in **which image is which** (master first, auxiliary second); keep **one** prompt body in `fal_common.py` (e.g. `S003_PROMPT_FLUX_COMPOSITE_SQUIRREL`).

## Verification (copy and complete)

```markdown
## Prompt change verification
- [ ] `panels/panel_s###.png` correct per stage_02 + manga-panel-crop-for-shots; `--ref` not a full page when multi-panel `NNN.jpg`
- [ ] BFL-style positives; risky tokens (white, blue) tied to the right character
- [ ] Read docs/flux-2-pro-prompting-guide.md
- [ ] If changing **color/material/light** from a greyscale ref: read docs/manga-greyscale-to-color.md
- [ ] Edit lead-in: reference still wins composition
- [ ] No hex wall unless fixing a logged drift
- [ ] Eisen / Heiter / Himmel wardrobe clauses only where that shot appears
- [ ] stage_03 updated if the shot note changes for writers
- [ ] New repeatable failure: one line in stage_04 QC + guide §6–§7 if it generalizes
- [ ] Scripts default / docs say Nano Banana, not Flux
```

## Handoff template

```text
Task: <shot id / files>
Use skill: nano-banana-2-prompting
Steps: (0) manga-panel-crop-for-shots — `panels/panel_s###.png` + stage_02 ref line if missing/wrong (1) BFL prompting_guide_flux2 skim (2) docs/flux-2-pro-prompting-guide.md (3) docs/manga-greyscale-to-color.md if tuning color/material from B&W panel (4) Edit only fal_common.py + target generate_*_ref_edit.py (5) Checklist above (6) No unrelated shots
```

## Anti-patterns

- Iterating **prompt text** when the Fal upload is still a **wrong panel**, **full page**, or **wrong tier** — **crop first** ([`manga-panel-crop-for-shots`](../manga-panel-crop-for-shots/SKILL.md)).
- Fixing **color bleed** by rewriting only the **lead-in** — add **positive garment locks** in the **body**.
- **Duplicating** `*_PROMPT_FLUX` per backend — API args vary in the script, **not** the string.
- **Forking** Pro vs Flex prompt text — project keeps a **single** scene string.

## Related paths

| Path | Role |
|------|------|
| `.cursor/skills/manga-chapter-ingest-stages-1-3/SKILL.md` | **Ingest** Stages 1–3 (story, RTL, cast) |
| `.cursor/skills/manga-panel-crop-for-shots/SKILL.md` | **`panels/panel_s###.png`** from **`NNN.jpg`** per shot (before `--ref`) |
| `docs/flux-2-pro-prompting-guide.md` | Long-form edit guide + revision log |
| `docs/manga-greyscale-to-color.md` | Greyscale cues → color/material matching; edit anchoring |
| `docs/stage5-image-to-video-fal.md` | Stage 5 video (not Nano; motion prompts only) |
| `scripts/fal_common.py` | `*_PROMPT_FLUX` |
| `scripts/generate_*_ref_edit.py` | `*_EDIT_LEAD_IN`, `--model` (default `nano-banana-2-edit`) |
| `Frierien-chapter081/stage_03_series_bible.md` | Per-shot Fal notes |
| `Frierien-chapter081/stage_04_*_visual_qc_log.md` | Regressions |
| `.cursor/skills/flux-2-pro-prompting/SKILL.md` | Deprecated; redirect here |
