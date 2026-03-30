# Stage 4 — S076 visual QC: manga page vs Flux edit stills

**Shot:** **S076** (`fb_hero`, WS, beat B15) — full **hero party** in **flower field**; drifting petals; **Himmel** readable mid-field.  
**Default Fal ref:** [`panels/panel_s076.png`](../panels/panel_s076.png) — single-panel crop of the **wide clearing** beat (four figures, flower bed, forest ring, petals). **Page context:** [`016.jpg`](./016.jpg); **white-gutter top = [`S075`](stage_04_s075_visual_qc_log.md)**; **black-gutter wide tier = this shot** (young Frieren, **no** travel scarf).  
**Generated (Flux 2 edit, full page upload, `103820Z`):**  
- Pro: [`Tests/S076_flux-2-pro-edit_20260325T103820Z.png`](../Tests/S076_flux-2-pro-edit_20260325T103820Z.png)  
- Flex: [`Tests/S076_flux-2-flex-edit_20260325T103820Z.png`](../Tests/S076_flux-2-flex-edit_20260325T103820Z.png)  
**Fal logs:** [`outputs/fal/S076_ref_edit_summary_20260325T103820Z.json`](../outputs/fal/S076_ref_edit_summary_20260325T103820Z.json)  
**Nano Banana 2 (optional):** `python generate_s076_ref_edit.py --model nano-banana-2-edit` — same `S076_EDIT_PROMPT` as Flux; default ref **`panels/panel_s076.png`**.  
- Legacy sample (full `016.jpg`, 16:9, 1K): [`Tests/S076_nano-banana-2-edit_20260326T080910Z.png`](../Tests/S076_nano-banana-2-edit_20260326T080910Z.png) · [`S076_ref_edit_summary_20260326T080910Z.json`](../outputs/fal/S076_ref_edit_summary_20260326T080910Z.json)  
- **Panel ref** (`panel_s076.png`, 16:9, 1K): [`Tests/S076_nano-banana-2-edit_20260326T082824Z.png`](../Tests/S076_nano-banana-2-edit_20260326T082824Z.png) · [`S076_ref_edit_summary_20260326T082824Z.json`](../outputs/fal/S076_ref_edit_summary_20260326T082824Z.json)

---

## 1. Manga ground truth (S076 panel intent)

| Dimension | Manga (wide flower-field panel on `016.jpg`) |
|-----------|-----------------------------------------------|
| **Scale / lens** | **High, wide** read — clearing feels **large**; party reads **small** in the flower sea; not a tight lineup poster. |
| **Layout** | **Depth staging**, not a flat front row: **Frieren and Himmel** closer / paired; **Eisen and Heiter** further into the field (one tall figure in long dark coat mid-distance). |
| **Environment** | **Forest-enclosed clearing** — trees around the meadow; **dappled light** (komorebi) on flowers and figures; distant hills/sky beyond the treeline. |
| **Flora** | **Dense carpet** of spell-made flowers (color lore often leans **blue / “Blue Moon”**-style weeds in adaptation); **many petals / debris** swept through the **whole** frame, not a few accents. |
| **Who** | **Four only:** young **Frieren**, **Himmel**, **Heiter**, **Eisen** — younger/travel-era designs. |
| **Silhouette reads** | Frieren **petite** vs Himmel **taller**; **Eisen = dwarf** — **short, stocky**, not a tall human warrior. |
| **Himmel** | Hero **white** cloak / structured shoulders; **mid-field focal** — often **with** Frieren in this wide beat (backs or three-quarter), not necessarily facing camera. |

---

## 2. Observed gaps — vs **Pro edit** (`…pro-edit…103820Z.png`)

| # | Category | Panel vs generation | Severity |
|---|----------|---------------------|----------|
| P1 | **Composition** | Generation reads as **four abreast, flat**, hero center **back to camera** in a hood — manga beat is **layered depth** (pair near + two deeper in field). | **High** |
| P2 | **Setting** | More **open sunny hill-meadow** and generic multicolor wildflowers; manga emphasizes **wooded clearing rim** + **dappled** light, spell-field **density**. | **High** |
| P3 | **Flora identity** | **Rainbow mixed wildflowers** — if matching story/VFX, steer toward **dominant small blue** (or single species carpet) + heavy petal swirl. | Medium |
| P4 | **Heiter** | **Brown hair** — canon Heiter is **green / teal** hair in anime reference. | Medium |
| P5 | **Frieren** | Reads **very child / chibi**; should be **young but believably adolescent/young adult elf** petite, not toddler proportions. | **High** |
| P6 | **Eisen** | **Dwarf** cues present (beard, stocky) — closer than Flex; still verify **height vs Himmel** (waist/chest band). | Medium |

---

## 3. Observed gaps — vs **Flex edit** (`…flex-edit…103820Z.png`)

| # | Category | Panel vs generation | Severity |
|---|----------|---------------------|----------|
| X1 | **Composition** | Same issue: **flat lineup / group portrait**; loses manga **foreground pair + background pair** staging. | **High** |
| X2 | **Eisen** | Reads as **large human** warrior — **fails dwarf scale** relative to Himmel (should be **much shorter**, wide build). | **Critical** |
| X3 | **Heiter** | **Grey hair** — still wrong vs **green/teal** priest cues. | Medium |
| X4 | **Frieren wardrobe** | Missing **white + gold-trim mage** read; earrings/icon details weak vs flashback design. | Medium |
| X5 | **Himmel** | Face-forward hero read is OK for color pass, but **wide S076** in manga is not a **symmetric four-across hero pose**; mole / fine likeness optional for WS. | Low–medium |
| X6 | **Lighting** | Very **even bright** field; manga panel pushes **tree shadow / sun shaft** contrast. | Medium |

---

## 4. Shared fixes (prompt + reference)

1. **Crop reference:** Run edit on a **crop of only the wide S076 panel** (not full `016.jpg`) so the model is not averaging other panels / faces — use `scripts/generate_s076_ref_edit.py --ref …` or [`scripts/edit_image_flux.py`](../scripts/edit_image_flux.py) on an intermediate still.  
2. **Composition text:** Replace “space the four across” with **“layered depth: Frieren and Himmel closer together foreground; Eisen and Heiter smaller, further up the field; high wide angle, small figures in vast flower sea.”**  
3. **Forest + light:** Add **“forest clearing encircled by tall trees; komorebi dappled sunlight; petals everywhere in the air.”**  
4. **Flowers:** Optional lore lock: **“dense field of small blue flowers (single species), like a spell-made carpet”** if matching Blue Moon weeds.  
5. **Heiter:** **“Pale green hair, priestly robes”** — forbid brown/grey hair for priest slot.  
6. **Frieren:** **“Young elf, petite adult proportions not chibi; white and gold-trim traveling mage clothes; low twin tails; red teardrop earrings.”**  
7. **Eisen:** **“Dwarf — notably short next to humans, stocky, broad; height near their waists — never same eye level as Himmel.”**  
8. **Second pass:** Use `edit_image_flux.py` on the better still with a **short delta prompt** (depth staging + blue field + dwarf height) to avoid rewriting the whole scene.

---

## 5. Summary (Round 1 — `103820Z`, before prompt v2)

| Model | Layout vs manga | Cast / scale | Environment vs panel |
|-------|-----------------|-------------|---------------------|
| **Pro edit** | Flat four-across; wrong hero blocking | Frieren too young/chibi; Heiter hair wrong | Open meadow > wooded clearing; flower mix not spell carpet |
| **Flex edit** | Same | **Eisen not dwarf**; Heiter grey hair | Same; very even lighting |

*Round 2 (`105137Z`): same models; v2 prompt + lead-in — see §6 and Round 2 links below.*

**Prompt v2 (2026-03-25):** `S076_PROMPT_FLUX` + `S076_EDIT_LEAD_IN` rewritten using [FLUX.2 prompting](https://docs.bfl.ai/guides/prompting_guide_flux2) and [image-edit](https://docs.bfl.ai/flux_2/flux2_image_editing) guidance — reference-first imperative for edits, subject/style/lighting order, positive constraints, hex anchors for blue flowers (#6B8DC2) and Heiter hair (#8FD4B8), explicit layered depth instead of “space four across.”

**Round 2 generation (full-page `016.jpg` ref, v2 prompt only — no model or resolution change):**  
- Pro: [`Tests/S076_flux-2-pro-edit_20260325T105137Z.png`](../Tests/S076_flux-2-pro-edit_20260325T105137Z.png)  
- Flex: [`Tests/S076_flux-2-flex-edit_20260325T105137Z.png`](../Tests/S076_flux-2-flex-edit_20260325T105137Z.png)  
- Summary: [`outputs/fal/S076_ref_edit_summary_20260325T105137Z.json`](../outputs/fal/S076_ref_edit_summary_20260325T105137Z.json)  

*Outcome:* Outputs tracked the panel brief **markedly better** than Round 1 (`103820Z`) on layout depth, blue spell-field read, forest/dappled lighting language, Heiter hair, Frieren proportions, and Eisen dwarf scale.

**Further optional pass:** single-panel crop of the wide meadow (`--ref`) and/or [`edit_image_flux.py`](../scripts/edit_image_flux.py) for small deltas.

---

## 6. Process playbook — what improved S076 (reuse on other shots)

Repeatable pipeline when a **reference-guided Flux 2 Pro/Flex edit** misses the manga.

### A. Baseline

1. Fix the shot ID, page, and beat in the shot list.  
2. Run **one** pair of jobs with **frozen** endpoints and dimensions (here: `fal-ai/flux-2-pro/edit`, `fal-ai/flux-2-flex/edit`, upload ref, 1280×720 via [`generate_s076_ref_edit.py`](../scripts/generate_s076_ref_edit.py)).  
3. Archive **JSON + PNG** with timestamps under `outputs/fal/` and `Tests/` so before/after stays auditable.

### B. Structured QC vs panel

1. Ground truth table: **scale, depth layout, environment, flora, cast count, height rules**, not vague “match style.”  
2. Separate **Pro** vs **Flex** gap lists with severity — fixes composition and cast before nitpicking lore.  
3. Name the **failure mode** (e.g. prompt line that implies a **flat lineup**, or **multi-panel** ref diluting layout).

### C. Prompt revision (FLUX.2 docs)

| Principle | Applied to S076 |
|-----------|-----------------|
| **Image edit: open with task + preserve/change** | [`S076_EDIT_LEAD_IN`](../scripts/generate_s076_ref_edit.py): bind to upload, preserve depth order, strip manga UI. |
| **Word order: critical first** | Anime framing + **four roles** → **lighting + forest clearing** → **camera** → **depth staging** → character locks. |
| **Lighting explicit** | Dappled canopy light; petals through full frame. |
| **Positive constraints** | “Only these four”; Eisen **head height vs waists**; avoid negation-only paragraphs. |
| **Hex for drift** | Flowers **#6B8DC2**, Heiter **#8FD4B8**. |
| **One prompt body** | [`S076_PROMPT_FLUX`](../scripts/fal_common.py). **Pro** is default in [`generate_s076_ref_edit.py`](../scripts/generate_s076_ref_edit.py); `--with-flex` for optional Flex A/B. |

Sources: [Prompting guide — FLUX.2](https://docs.bfl.ai/guides/prompting_guide_flux2), [FLUX.2 image editing](https://docs.bfl.ai/flux_2/flux2_image_editing).

### D. Repo layout (single source of truth)

| Piece | Location |
|--------|-----------|
| Scene text (T2I-safe) | `scripts/fal_common.py` → `S076_PROMPT_FLUX` |
| Edit-only lead-in | `scripts/generate_s076_ref_edit.py` → `S076_EDIT_LEAD_IN` |
| Bible pointer | [`stage_03_series_bible.md`](./stage_03_series_bible.md) §S076 |
| Post-gen scratch edits | [`scripts/edit_image_flux.py`](../scripts/edit_image_flux.py) |

### E. Regenerate + log

1. `python scripts/generate_s076_ref_edit.py` (optionally `--ref` crop; add `--with-flex` only if comparing Flex).  
2. Append this file: timestamps, prompt version, subjective delta vs last round.

### F. Checklist for the next shot (S010, S070, …)

- [ ] Baseline gen + logs saved  
- [ ] QC: panel truth vs Pro vs Flex  
- [ ] Root cause: ref vs prompt contradiction vs missing light/staging  
- [ ] Rewrite: **edit lead-in** + **ordered scene body**; hex only where palette keeps slipping  
- [ ] `SHOT_PROMPT_FLUX` in `fal_common.py`; `SHOT_EDIT_LEAD_IN` in shot script  
- [ ] Bible note + QC log round  

---

**Round 3 (prompt v3 + pipeline):** `S076_PROMPT_FLUX` — wiki-aligned **Himmel** (mole under left eye, blue tunic, cream/tan cloak), **Heiter** (slicked green hair **#6EB89A**, brown eyes, **rectangular glasses**, black-and-gold clergy, scripture book), **Eisen** (wiki-heavy: long beard, red cape, pauldrons — **reverted in v4**). Pro sample: [`Tests/S076_flux-2-pro-edit_20260326T021140Z.png`](../Tests/S076_flux-2-pro-edit_20260326T021140Z.png), summary [`S076_ref_edit_summary_20260326T021140Z.json`](../outputs/fal/S076_ref_edit_summary_20260326T021140Z.json).

**Round 4 (prompt v4 — Eisen fix):** Restore **v2-style dwarf silhouette** (practical dark travel coat, stocky, short vs humans). **Heiter / Himmel unchanged.** For Eisen only: **readable face** (trimmed jaw beard, visible eyes), **muted palette hex locks** coat **#2A2624**, tunic **#5C4A3D**, leather **#6B4E3D** — drop dominant red cape / chest-length beard / heavy armor language that broke the good prior body read. **Pro (full `016.jpg`):** [`Tests/S076_flux-2-pro-edit_20260326T022033Z.png`](../Tests/S076_flux-2-pro-edit_20260326T022033Z.png), [`S076_ref_edit_summary_20260326T022033Z.json`](../outputs/fal/S076_ref_edit_summary_20260326T022033Z.json).

---

## 7. Round 4 visual QC — generated [`022033Z`](../Tests/S076_flux-2-pro-edit_20260326T022033Z.png) vs manga **wide party panel** on [`016.jpg`](./016.jpg)

Comparison uses the **middle wide shot** on p.16 (four figures in the flower spell, forest ring, airborne petals). Lower tiers on the same page are dialogue close-ups and must not be treated as layout truth for S076.

| Area | Manga panel intent | `022033Z` generation | Verdict |
|------|-------------------|----------------------|---------|
| **Himmel — species** | Human hero, no elf ears. | **Pointed elf ears** on Himmel. | **Critical** anatomy / identity error. |
| **Himmel — prop** | Wide shot: with Frieren, backs / field, **no scripture focus**. | Holds a **thick brown book** like Heiter. | **High** — likely bleed from lower panels + “Heiter book” prompt language. |
| **Eisen — palette** | **Dark** cloak / rugged mass, dwarf scale. | **Bright mustard / orange** shirt, **white** bushy beard; not the locked **#2A2624 / #5C4A3D** muted stack. | **Critical** — hex in prompt did not bind; reads opposite of panel + prompt. |
| **Eisen — role read** | Warrior / traveler in dark layers, often **axe** silhouette in hero-party memory. | **Book** held like cleric; softened generic face. | **High** — conflated with priest beat. |
| **Heiter** | Tall, **dark long robe**, light hair (green in color); background motion in wide panel. | Green hair, dark robe with gold, glasses — directionally OK; **very saturated** green; **book** matches prompt but may over-weight vs wide panel. | Medium — closer than others; still “AI smooth” face. |
| **Staging** | Four scattered in depth in clearing (Eisen **left** from behind, Heiter deeper, Frieren + Himmel paired). | Reads as **two backs foreground + two fronts midground**, flatter poster layout. | Medium — reference still full page + model lineup drift. |
| **Reference pollution** | S076 = one wide composition. | Full **`016.jpg`** upload merges **top vista** + **bottom Himmel/Frieren CU** cues → books, wrong interactions. | **High** — root cause for props / ears / layout mixing. |

**Summary:** The run fails mainly on **(Himmel elf ears + book)**, **(Eisen wrong colors + white beard + book instead of warrior read)**, and **multi-panel reference noise**. Prompt v4 did not overcome **full-page** conditioning. **Next corrective actions:** (1) **Crop only the wide S076 panel** as `--ref`. (2) Prompt deltas: **“Himmel is human with rounded human ears, never elf ears”**; **“no books for Himmel or Eisen”** / **empty hands** for wide beat; **Eisen: no holy book, warrior or hands at sides**; reinforce **axe on back** if visible. (3) Optional second pass: [`edit_image_flux.py`](../scripts/edit_image_flux.py) on `022033Z` with a **narrow** fix list (ears, Eisen shirt recolor) to avoid full regen.

---

**Prompt rollback (2026-03-26):** `S076_PROMPT_FLUX` restored to **Round 2 v2** (identical to [`105137Z`](../Tests/S076_flux-2-pro-edit_20260325T105137Z.png) / user-saved asset). Later v3/v4 wiki and Eisen hex experiments **removed** from codebase.

**Wardrobe palette pass (v5):** Added heavy per-hero **hex** text — caused generations to **ignore panel blocking** vs reference. **Reverted (v6):** v2 character wording restored + one short “gentle color nudge” sentence + **reference wins composition** in `S076_EDIT_LEAD_IN`. v5 sample for contrast: [`022743Z`](../Tests/S076_flux-2-pro-edit_20260326T022743Z.png). **v6 Pro:** [`023257Z`](../Tests/S076_flux-2-pro-edit_20260326T023257Z.png).

**v7 (hair micro-tune):** Himmel = **light-blue bowl-cut**, hue tied to tunic, human ears, not white/silver/long shaggy; Heiter = **short slicked seafoam/mint #8FD4B8**, optional two forelock strands, **not brown/grey/white** — **only** these clauses touched to limit re-layout drift. **Pro:** [`023701Z`](../Tests/S076_flux-2-pro-edit_20260326T023701Z.png).

### Why v7 skewed cape / robe colors (FLUX.2 Pro edit)

Per [Black Forest Labs — Prompting Guide (FLUX.2)](https://docs.bfl.ai/guides/prompting_guide_flux2):

1. **“No negative prompts”** — models are tuned to **describe what you want**. Phrases like *“never brown, grey, or **white** clerical hair”* still surface the token **white** next to **Heiter**, which can bleed into **robes** (not just hair).
2. **Word order / attention** — *“…pays more attention to* **what comes first**.” Heavy early **blue** (#6B8DC2 field + **sky-blue** Himmel + “same **cool blue family** as his tunic”) can **over-associate** blue with the whole **Himmel** figure unless **cloak is named as separate off-white** explicitly.
3. **Image edit + long prompts** — the edit endpoint still **re-synthesizes** regions; vague garment splits let the **dominant scene color** (blue flowers) tint **secondary** materials unless each piece is **positively** locked ([image editing](https://docs.bfl.ai/flux_2/flux2_image_editing) combines reference + text; conflicting or negation-style text fights the panel).
4. **Eisen** — red cape lived only in the short “color-grade” sentence; the **per-character** line said “dark travel coat” **without** red, so the model could **drop red** and let **ambient blue** win.

**v8 fix (prompt):** Remove Heiter **“never … white”** negation; use **positive** locks: *black/charcoal vestments*, *green hair on scalp only*; Himmel *blue = hair + tunic only*, *cloak cream/white explicitly*; Eisen *brick-red cape* in the Eisen paragraph. **Pro:** [`024856Z`](../Tests/S076_flux-2-pro-edit_20260326T024856Z.png).

*QC log: Round 1 (`103820Z`), Round 2 v2 (`105137Z` — **current prompt**), Rounds 3–4 archival; §7 still documents `022033Z` failure modes for reference.*
