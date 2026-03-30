# Stage 4 — S002 visual QC log

**Shot:** **S002** (`present`, WS EST, B2) — **Stark**, **Frieren**, **Fern** at **forest camp**; small **campfire**, **axe** & packs; Weise establishing.  
**Panel ref:** [`panels/panel_s002.png`](../panels/panel_s002.png) — default for [`generate_s002_ref_edit.py`](../scripts/generate_s002_ref_edit.py).  
**Pipeline:** **`S002_PROMPT_FLUX`** + **`S002_EDIT_LEAD_IN`** — **`fal-ai/flux-2-pro/edit`** and/or **`fal-ai/nano-banana-2/edit`** (`--model` / `--model both`). Default ref **`panels/panel_s002.png`**; Flux **16:9** `landscape_16_9`; Nano Banana **`--aspect-ratio`** / **`--resolution`**.

---

## Runs

| Timestamp | Ref | Pro | Notes |
|-----------|-----|-----|-------|
| `040025Z` | [`panels/panel_s002.png`](../panels/panel_s002.png) | [`Tests/S002_flux-2-pro-edit_20260326T040025Z.png`](../Tests/S002_flux-2-pro-edit_20260326T040025Z.png) | First **`S002_PROMPT_FLUX`** + lead-in; [`S002_ref_edit_summary_20260326T040025Z.json`](../outputs/fal/S002_ref_edit_summary_20260326T040025Z.json). |
| `094001Z` | [`panels/panel_s002.png`](../panels/panel_s002.png) | [`Tests/S002_flux-2-pro-edit_20260326T094001Z.png`](../Tests/S002_flux-2-pro-edit_20260326T094001Z.png) | Re-run Flux Pro `landscape_16_9`; [`S002_ref_edit_summary_20260326T094001Z.json`](../outputs/fal/S002_ref_edit_summary_20260326T094001Z.json). |
| `094158Z` | [`panels/panel_s002.png`](../panels/panel_s002.png) | Flux: [`Tests/S002_flux-2-pro-edit_20260326T094158Z.png`](../Tests/S002_flux-2-pro-edit_20260326T094158Z.png) · Nano: [`Tests/S002_nano-banana-2-edit_20260326T094158Z.png`](../Tests/S002_nano-banana-2-edit_20260326T094158Z.png) | **`--model both`** same upload; [`S002_ref_edit_summary_20260326T094158Z.json`](../outputs/fal/S002_ref_edit_summary_20260326T094158Z.json). |

---

## QC checklist (`panel_s002.png` + 16:9)

- [ ] **Chirality:** **Stark** fire side **viewer-left**; **no** accidental horizontal flip vs crop.
- [ ] **Cast:** Three travelers only; **Fern** back to camera foreground; **Frieren** tree + **book**; **Stark** + **axe** near fire.
- [ ] **Read:** Cold-travel wardrobe locks (purple / silver-white / red) without cross-bleed onto wrong coat.
- [ ] **Clean frame:** No manga boxes, balloons, or halftone.

---

*Update after each QC round.*
