---
name: manga-panel-crop-for-shots
description: Cuts a single manga page into per-shot panel crops (PNG refs) for Fal image-edit pipelines—maps each S### shot to panels/panel_s###.png from chapter JPGs using stage_02. Use when creating or replacing panel references, cropping Frierien-chapter pages, preparing --ref uploads, mentions of panel_s*.png, single-panel crop, or extracting a panel for a specific scene.
---

# Manga panel crop for shots (AI_Animation)

## Role

Produce **one reference crop per shot** (when Stage 2 is **one panel ≈ one shot**) so Stage 4 scripts default to **`panels/panel_s0XX.png`** instead of a full **`NNN.jpg`**.

**Upstream:** Shot list + page file — [`.cursor/skills/manga-chapter-ingest-stages-1-3/SKILL.md`](../manga-chapter-ingest-stages-1-3/SKILL.md), **`Frierien-chapterNNN/stage_02_shot_list.md`**.  
**Downstream:** Fal uploads — [`.cursor/skills/nano-banana-2-prompting/SKILL.md`](../nano-banana-2-prompting/SKILL.md).

---

## Rules

1. **Source of truth for “which rectangle”** — the **`NNN.jpg`** named in Stage 2 for that shot, plus the **What we see / Continuity** row for **S###**. If RTL/panel order was audited on the page, use the **same panel** that row describes (not a neighboring tier).
2. **Filename** — repo root **`panels/panel_s0XX.png`** with **three-digit** `XX` matching the shot ID (`S002` → `panel_s002.png`). Use lowercase **`panel_s`** prefix consistently.
3. **One panel only** — crop **inside** the panel border; do not include an adjacent panel’s art or the full page unless Stage 2 explicitly treats the shot as a full-page comp (rare).
4. **Tiered pages** (e.g. **`016.jpg`** present vs flashback) — crop **only the tier** belonging to that shot (see Stage 1 gutter notes + Stage 2 layer). **S075** and **S076** must not share one crop.
5. **Gutters / credits** — exclude scan margin, chapter stamps, TL credit blocks, and **neighboring gutters** from the crop.
6. **Format** — **PNG** (lossless; preserves line art for edit models). No mandatory resolution in-repo; prefer **native scan DPI** for that panel — scripts can downscale at Fal.
7. **Iterating a ref** — keep `panel_s00X.png` as current default; optional side files like `panel_s003old.png` for history only — **scripts default to `panel_s###.png`**.

---

## Workflow

1. Open **`stage_02_shot_list.md`** → locate **S###** (page **`NNN.jpg`**, row text).
2. Open **`Frierien-chapterNNN/NNN.jpg`** and identify the **single panel** for that shot (balloon order / ingest note if the page is dense).
3. Flatten crop to rectangle; export **`panels/panel_s###.png`** (overwrite deliberate).
4. In Stage 2 **Continuity** for that shot, ensure the line **`Ref [`panels/panel_s###.png`](../../panels/panel_s###.png)`** exists (path depth may vary; match sibling shots in the same chapter).
5. If **`generate_*_ref_edit.py`** exists for the shot, confirm default **`--ref`** points at the new file (or document override in **stage_03** / script header).

---

## Do not

- Use a **full page** as `--ref` when Stage 2 lists **multiple shots** on that page — Fal gets wrong composition and wrong gutter/balloon context.
- **Mirror** the crop horizontally unless the pipeline explicitly corrects chirality; QC logs (e.g. **S003**, **S075**) track flip bugs.
- Rename **`S###`** when fixing crops — **IDs are stable**; replace the PNG under the same name or add `_old` variants.

---

## Verification (copy)

```markdown
## Panel crop check — S###
- [ ] Source `NNN.jpg` + Stage 2 row match the same panel
- [ ] `panels/panel_s###.png` exists; no extra panels in frame
- [ ] Tier/layer (present vs fb_*) matches stage Layer
- [ ] Stage 2 Continuity links ref; stage_03 / script default ref updated if needed
```

## Related paths

| Path | Role |
|------|------|
| `Frierien-chapter081/stage_02_shot_list.md` | Shot → page → panel description |
| `panels/panel_s*.png` | Output crops |
| `docs/flux-2-pro-prompting-guide.md` | Crop vs full-page QC notes |
| `scripts/generate_*_ref_edit.py` | Default `--ref` |
