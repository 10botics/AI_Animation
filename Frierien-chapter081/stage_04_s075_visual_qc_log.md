# Stage 4 — S075 visual QC log

**Shot:** **S075** (`present`, MS OTS, beat B15) — **Denken** + adult **Frieren**, **snowy Northern vista**; **thick travel scarf** (**S074** continuity). **Not** **S076** flower flashback.  
**Panel ref (ground truth):** [`panels/panel_s075.png`](../panels/panel_s075.png) — snowy **OTS** Denken / scarf Frieren; default for [`generate_s075_ref_edit.py`](../scripts/generate_s075_ref_edit.py).  
**Pipeline:** `fal-ai/flux-2-pro/edit` only; **`S075_PROMPT_FLUX` v11** (Denken back-of-head hair = **brown**; not Frieren’s silver-white). Output **16:9** (`landscape_16_9` default). **Crop ref** = best accuracy.

---

## Runs

| Timestamp | Ref | Pro | Flex | Notes |
|-----------|-----|-----|------|-------|
| `105743Z` | full [`016.jpg`](./016.jpg) | [`Tests/S075_flux-2-pro-edit_20260325T105743Z.png`](../Tests/S075_flux-2-pro-edit_20260325T105743Z.png) | [`Tests/S075_flux-2-flex-edit_20260325T105743Z.png`](../Tests/S075_flux-2-flex-edit_20260325T105743Z.png) | Legacy prompt; wrong layer/cast vs **v4**. |
| `025812Z` | full [`016.jpg`](./016.jpg) | [`Tests/S075_flux-2-pro-edit_20260326T025812Z.png`](../Tests/S075_flux-2-pro-edit_20260326T025812Z.png) | [`Tests/S075_flux-2-flex-edit_20260326T025812Z.png`](../Tests/S075_flux-2-flex-edit_20260326T025812Z.png) | Pre–**v4**; treat as invalid for QC vs Denken+scarf present. |
| `031824Z` | full [`016.jpg`](./016.jpg) | [`Tests/S075_flux-2-pro-edit_20260326T031824Z.png`](../Tests/S075_flux-2-pro-edit_20260326T031824Z.png) | — | **v5** (pre–snow correction); full page ref. |
| `032607Z` | [`panels/panel_s075.png`](../panels/panel_s075.png) | [`Tests/S075_flux-2-pro-edit_20260326T032607Z.png`](../Tests/S075_flux-2-pro-edit_20260326T032607Z.png) | — | **v6**; superseded by **v7** BG + Denken OTS locks. |
| `033307Z` | [`panels/panel_s075.png`](../panels/panel_s075.png) | [`Tests/S075_flux-2-pro-edit_20260326T033307Z.png`](../Tests/S075_flux-2-pro-edit_20260326T033307Z.png) | — | **v7** (could mirror: prompt had “Frieren left **or opposite**”). |
| `033652Z` | [`panels/panel_s075.png`](../panels/panel_s075.png) | [`Tests/S075_flux-2-pro-edit_20260326T033652Z.png`](../Tests/S075_flux-2-pro-edit_20260326T033652Z.png) | — | **v8** chirality lock + lead-in **do not mirror**; [`S075_ref_edit_summary_20260326T033652Z.json`](../outputs/fal/S075_ref_edit_summary_20260326T033652Z.json). |
| `034208Z` | [`panels/panel_s075.png`](../panels/panel_s075.png) | [`Tests/S075_flux-2-pro-edit_20260326T034208Z.png`](../Tests/S075_flux-2-pro-edit_20260326T034208Z.png) | — | **v9** Denken **full silver-white hair**; [`S075_ref_edit_summary_20260326T034208Z.json`](../outputs/fal/S075_ref_edit_summary_20260326T034208Z.json). |
| `035041Z` | [`panels/panel_s075.png`](../panels/panel_s075.png) | [`Tests/S075_flux-2-pro-edit_20260326T035041Z.png`](../Tests/S075_flux-2-pro-edit_20260326T035041Z.png) | — | **v11** Denken **brown** scalp hair; positive-only wording (no “not silver” on Denken); [`S075_ref_edit_summary_20260326T035041Z.json`](../outputs/fal/S075_ref_edit_summary_20260326T035041Z.json). |
| `073223Z` | [`panels/panel_s075.png`](../panels/panel_s075.png) | [`Tests/S075_nano-banana-2-edit_20260326T073223Z.png`](../Tests/S075_nano-banana-2-edit_20260326T073223Z.png) | — | **Nano Banana 2** `fal-ai/nano-banana-2/edit` — **same** `S075_EDIT_PROMPT` as Flux; 16:9, 1K; [`S075_ref_edit_summary_20260326T073223Z.json`](../outputs/fal/S075_ref_edit_summary_20260326T073223Z.json). |

*New runs: **Pro-only**; Flex column empty.*

---

## v11 QC checklist (`panels/panel_s075.png` + 16:9)

*(**v10** expected **bright white** Denken head hair; **v11** matches **broadcast anime** brown head hair — older Pro rows in the table above are still valid for composition/snow checks, not for hair color.)*

- [ ] **Chirality:** **Frieren left**, **Denken back right** — **not** mirrored vs crop.
- [ ] **Setting:** Snow + **rock-streaked** ridges; grey overcast.
- [ ] **OTS Denken:** Back only; **brown** head hair (not silver-white), high dark coat; **Frieren** scarf read.
- [ ] **Cast:** Present pair only; no hero-party flashback wardrobe.

---

## Process

Same playbook as [S076 §6](stage_04_s076_visual_qc_log.md#6-process-playbook--what-improved-s076-reuse-on-other-shots): baseline → structured QC vs panel → prompt deltas → re-run.

---

*Update this file after each QC round.*
