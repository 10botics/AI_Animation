# Stage 4 — S003 visual QC log

**Shot:** **S003** — Fern + squirrel (`full`) / Fern plate (`fern-only`). Ref [`panels/panel_s003.png`](../panels/panel_s003.png).

## Regression notes

| Date | Issue | Mitigation |
|------|--------|------------|
| 2026-03-26 | **Fern-only** Nano output: hands **hidden** inside oversized coat sleeves | `S003_PROMPT_FLUX_FERN_ONLY` + `S003_EDIT_LEAD_IN_FERN_ONLY` now **require visible hands on lap**, cuffs at/above wrists; lead-in supports **refine pass** from an existing color frame (`--ref` to that PNG). |
| 2026-03-26 | Output **horizontally flipped** vs manga | Lead-ins + `S003_PROMPT_FLUX*` lock **Fern viewer-left / facing left**, bag+squirrel **viewer-right** in `full`; fern-only inpaints **viewer-right** ground only. Always use [`panels/panel_s003.png`](../panels/panel_s003.png). |
| 2026-03-26 | Model outputs **right-facing** or **standing** | Prompts spell **LEFT edge of frame** + **sits on ground**; lead-ins forbid mirror. **16:9** can still recompose vs a tall panel — if flip returns, retry with **`--aspect-ratio 9:16`** or Flux. **Delivery default:** Nano **`16:9`** for chapter pipeline. |
| 2026-03-26 | **Fern-only** plate missing **S002** camp (Frieren, Stark, fire, gear) | Second pass **`--variant extend-camp`**: locks foreground Fern from `--ref` fern-only PNG; `S003_PROMPT_FLUX_EXTEND_CAMP` + lead-in add mid/background continuity with S002. Default ref swaps to `Tests/S003_fernonly_nano-banana-2-edit_20260326T142928Z.png` when `--ref` is still the panel default. |
| 2026-03-26 | **Extend-camp** plate missing **squirrel** / Fern looks at **fire** not bag | Third pass **`--variant extend-camp-squirrel`**: ref = approved extend-camp PNG; `S003_PROMPT_FLUX_EXTEND_CAMP_SQUIRREL` locks camp, adds **tan satchel + squirrel** (`panel_s003.png` scale), directs **gaze to squirrel**. Default `--ref` → `Tests/S003_extendcamp_nano-banana-2-edit_20260326T143552Z.png` if present. |
| 2026-03-26 | Squirrel reads as **wrong species / toy** (huge tail on lip, chibi) vs **`panel_s003.png`** | Prompts lock **panel ink**: **upright in bag**, **head + upper chest above rim**, **small ears**, **slender**, **paws high on chest**, **tail mostly inside satchel**; `S003_PROMPT_FLUX` aligned. Re-run **`extend-camp-squirrel`**. Prefer **`--ref`** the **extend-camp** plate (`S003_extendcamp_*.png` **without** squirrel) so the edit is not anchored to a bad messenger; only use a prior `extendcampsquirrel` ref for **gaze-only** tweaks. |
| 2026-03-26 | Courier does not match **anime turnaround** (user ref: **shoulder micro-bag + letter**) | `S003_PROMPT_FLUX_EXTEND_CAMP_SQUIRREL` now describes **Frieren TV messenger squirrel** **on leaves** between Fern and fire: **lavender-grey / white bib**, **big black eyes**, **bushy tail**, **cream canvas + tan flap + buckle + envelope**; manga-only “inside traveler satchel” wording retired for this variant. Try **`--model flux-2-pro-edit`** if Nano drifts. |

**Regenerate fern-only:**  
`python scripts/generate_s003_ref_edit.py --variant fern-only`  
**Refine an existing render:**  
`python scripts/generate_s003_ref_edit.py --variant fern-only --ref Tests/your_fernonly.png`  
**Extend camp (fern-only → full scene depth):**  
`python scripts/generate_s003_ref_edit.py --variant extend-camp --ref Tests/S003_fernonly_nano-banana-2-edit_20260326T142928Z.png`  
**Extend camp + squirrel gaze:**  
`python scripts/generate_s003_ref_edit.py --variant extend-camp-squirrel --ref Tests/S003_extendcamp_nano-banana-2-edit_20260326T143552Z.png`  
**Same, but squirrel **look** from your PNG (dual `image_urls`):**  
`python scripts/generate_s003_ref_edit.py --variant extend-camp-squirrel --ref Tests/S003_extendcamp_nano-banana-2-edit_20260326T143552Z.png --squirrel-ref path/to/your_squirrel.png`
