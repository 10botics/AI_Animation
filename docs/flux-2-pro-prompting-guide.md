# Still-image prompting guide (Fal.ai + BFL) — **Nano Banana 2 primary**

> **Project default (2026-03-26 onward):** chapter stills use **`fal-ai/nano-banana-2/edit`**, not Flux. Same prompt strings (`*_EDIT_LEAD_IN` + `*_PROMPT_FLUX` in code); API fields differ (`aspect_ratio`, `resolution`, etc.). **Cursor skill:** [`.cursor/skills/nano-banana-2-prompting/SKILL.md`](../.cursor/skills/nano-banana-2-prompting/SKILL.md). *flux-2-pro-prompting* is **deprecated** (redirect only).
>
> The sections below on **BFL / FLUX.2** remain the **authoring reference** for positive prompt structure; `[Flux 2 Pro](https://fal.ai/models/fal-ai/flux-2-pro/edit)` is **legacy optional** in scripts via `--model flux-2-pro-edit` only when explicitly needed.

**Legacy skill stub:** [`.cursor/skills/flux-2-pro-prompting/SKILL.md`](../.cursor/skills/flux-2-pro-prompting/SKILL.md) — points to Nano Banana skill.

**Stage 5 (image → video on Fal):** [`docs/stage5-image-to-video-fal.md`](./stage5-image-to-video-fal.md) — Kling 2.6 Pro I2V handbook (complements this image guide).

**Before authoring or changing prompts:** skim Black Forest Labs [**Prompting Guide — FLUX.2**](https://docs.bfl.ai/guides/prompting_guide_flux2) (subject → action → style → context; **no negative prompts**; priority order and length guidance). This project guide then adds Fal `/edit` and pipeline lessons below.

**Use this document** whenever you **create or edit** prompts for:

- `fal-ai/flux-2-pro` (text-to-image)
- `fal-ai/flux-2-pro/edit` (image + text; reference URLs in `image_urls`)

Project wiring: shot strings in `scripts/fal_common.py` (`*_PROMPT_FLUX`); reference-specific lead-ins in `scripts/generate_*_ref_edit.py` (`*_EDIT_LEAD_IN`).

---

## 1. Official references (read for depth)

| Resource | URL |
|----------|-----|
| FLUX.2 prompting (Pro / Max) | [docs.bfl.ai — Prompting Guide](https://docs.bfl.ai/guides/prompting_guide_flux2) |
| FLUX.2 image editing (reference + text) | [docs.bfl.ai — Image editing](https://docs.bfl.ai/flux_2/flux2_image_editing) |
| Fal model API (Pro T2I) | [fal-ai/flux-2-pro](https://fal.ai/models/fal-ai/flux-2-pro/api) |
| Fal model API (Pro **edit**) | [fal-ai/flux-2-pro/edit](https://fal.ai/models/fal-ai/flux-2-pro/edit/api) |

---

## 2. Core rules (BFL)

### 2.1 No negative prompts

FLUX.2 is trained to follow **positive** descriptions. **Avoid** long “never / don’t / no X” lists.

- Bad: `never brown, grey, or white hair` (tokens like **white** still fire and can attach to the **wrong garment**—e.g. white robes instead of green hair only).
- Better: `scalp hair seafoam-green; robes solid black with gold trim`.

### 2.2 Word order = priority

Earlier tokens weigh more: **main subject → action → style → context → details**.

Put **composition locks** and **the edit task** (for `/edit`) **before** long atmospheric prose if the model keeps drifting.

### 2.3 Lighting and scene color vs costume color

Big **environment color** (e.g. a **blue flower field** + hex) can **tint** figures if outfit colors are not **named per garment**.

- Tie colors to **specific parts**: “**tunic** blue; **cloak** cream; **cassock** black.”
- Say when needed: each garment **keeps its own hue** (optional: not one global blue wash on capes).

### 2.4 Hex codes

Use **hex for precision** on Parts that drift ([HEX section](https://docs.bfl.ai/guides/prompting_guide_flux2)). Prefer **one part = one color phrase**, not a wall of hex that overpowers **image reference** layout.

---

## 3. Image editing (`flux-2-pro/edit`) — this repo’s default for shots

### 3.1 Reference + text

The uploaded image is the **layout anchor**. Prompt should:

1. **First** say what to **keep** (poses, depth, headcount, blocking).
2. **Then** say what to **change** (halftone removal, anime paint, gentle palette).

If text **contradicts** the reference or is **over-specific** on wardrobe, the model may **rewrite the whole scene**—see S076 wardrobe-hex experiments in `stage_04_s076_visual_qc_log.md`.

### 3.2 Multi-panel manga pages

Full-page `NNN.jpg` = **several compositions** in one file. The model may **blend** gutters, dialogue CUs, and props (e.g. books on everyone).

**Prefer a single-panel crop** for the target shot; pass `--ref path\to\crop.png`.

### 3.3 One body for Pro (optional Flex elsewhere)

This project defaults to **Pro edit only**; **don’t fork** prompt strings for Pro vs Flex. **`generate_s075_ref_edit.py`** is **Pro-only** (`fal-ai/flux-2-pro/edit`). Other shot scripts may still offer `--with-flex` for comparison unless noted.

### 3.4 Reference fidelity — what the API can (and cannot) do

The public **`fal-ai/flux-2-pro/edit`** schema has **`prompt`**, **`image_urls`**, **`image_size`** (`auto`, presets, or `{width,height}`), **`seed`**, **`output_format`**, **`safety_tolerance`**, **`enable_safety_checker`**. There is **no** img2img-style **strength / denoise / CFG** knob exposed — layout drift is controlled by **input**, not a slider.

Practical levers (strongest first):

1. **Single-panel crop** as `image_urls` — full manga pages mix layouts; the model averages them.
2. **`image_size`** — forcing the wrong aspect **re-frames** the panel. **`generate_s075_ref_edit.py`** defaults to Fal **`landscape_16_9`** for a native **16:9** output, with **`1280x720`** / **`1920x1080`** as fixed alternates. (Ref-size **`match`** lives in `flux_pro_edit_image_size_match_ref()` for other shots if needed.)
3. **Prompt length** — long cast/color text can **override** the reference; keep the body tight once composition is right (BFL image-edit guidance).
4. **`seed`** — repeatability only; not “closer to panel.”

`scripts/fal_common.py` exposes **`flux_pro_edit_image_size_match_ref()`** for `{width,height}` from the ref file (Pillow).

---

## 4. Project structure (where prompts live)

| Piece | Role |
|-------|------|
| `*_PROMPT_FLUX` in `fal_common.py` | Scene + cast; safe for T2I if reused later. |
| `*_EDIT_LEAD_IN` in shot scripts | **Edit-only**: preserve/change from upload; strip manga UI. |
| `stage_03_series_bible.md` | Human-readable shot bullets + pointer to code. |
| `stage_04_*_visual_qc_log.md` | What failed and why (ground truth vs model). |

---

## 5. Pre-flight checklist (before merging prompt changes)

- [ ] **Positive** wording for colors and roles; no negation chains with risky tokens (**white**, **blue**, etc.) next to the wrong character.
- [ ] **Per-garment** color labels if the scene has a **strong global hue** (flowers, gold city, night).
- [ ] **Edit** lead-in: reference wins **composition**; text refines look.
- [ ] **Hair / face** cues scoped (**hair only**, **human ears**) so they don’t recolor **cloaks**.
- [ ] Cast count and **named roles** explicit for multi-character shots.
- [ ] If output **ignored** layout, check reference crop and shorten competing prompt clauses.

---

## 6. Lessons from Chapter 81 pipeline (S076, S075)

**S075** (`panels/panel_s075.png`): **Cropped single panel** as `image_urls` beats full page. **OTS** shots — describe only **visible** anatomy; naming **beard/monocle** when the panel shows **only the back** can pull wrong rotations or faces. **Background** must match **ground truth** (here: **snowfield + rock breaking through snow on ridges**, grey overcast), not other chapter beats (flower spell-field). **Avoid ambiguous staging** like “character left **or opposite**” — it licenses **horizontal mirroring**; lock **viewer-left / viewer-right** to match the panel. Add **preserve chirality / do not mirror** in the edit lead-in when drift appears.

Documented in `Frierien-chapter081/stage_04_s076_visual_qc_log.md` (party meadow):

- Heavy **per-character hex blocks** + long wardrobe prose → **ignored panel blocking**.
- **“Same blue as tunic”** for Himmel **hair** → **blue capes** unless cloak called **off-white separately**.
- **Heiter “never … white”** (hair) → **white priest robes** (token bleed).
- **Eisen red cape** only in a weak sentence → **ambient blue** wins; put **red cape** in the **character** line.

---

## 7. Revision history

| Date | Note |
|------|------|
| 2026-03-26 | Initial guide; encodes BFL links + S076 failure modes. |
| 2026-03-26 | S075: panel-accurate snow/rock BG; OTS Denken without face tokens. |
| 2026-03-26 | S075: “left or opposite” caused **horizontal flip** — lock viewer-left/right + lead-in **do not mirror**. |
| 2026-03-26 | S075: Denken **not balding** — use **full** head hair from behind; drop “receding/crown” web-scrape noise. |
| 2026-03-26 | S075: Denken hair **white**, not silver/ash grey — avoid “silver-white” on him; keep Frieren’s **silver-white** elf hair separate. |
| 2026-03-25 | S075 **v11:** Denken head hair **brown** (anime); still keep Frieren **silver-white** elf hair separate in the same frame. |
| 2026-03-26 | S075 **v11** tweak: Denken brown hair described **positive-only** — drop adjacent “not silver-white” on him (guide §2.1); Frieren line already locks elf hair. |
| 2026-03-26 | **S002:** forest camp trio — `S002_PROMPT_FLUX` + `generate_s002_ref_edit.py`; BFL order subject→action→style→context; lead-in strips **narrative text boxes** from manga panel. |
| 2026-03-26 | **S002** backends: **`nano-banana-2-edit`** (default) \| `flux-2-pro-edit` \| **`both`**; ref [`panels/panel_s002.png`](../panels/panel_s002.png). |
| 2026-03-26 | **S010:** `generate_s010_ref_edit.py` — default **`nano-banana-2-edit`**; ref [`panels/panel_s010.png`](../panels/panel_s010.png); **`both`** = Pro + Nano; `--with-flex` only for Flux. |
| 2026-03-26 | **S075:** **`fal-ai/nano-banana-2/edit`** default — **identical** `S075_EDIT_LEAD_IN` + `S075_PROMPT_FLUX`; Flux legacy via `--model flux-2-pro-edit`. |
| 2026-03-26 | **S076:** **`generate_s076_ref_edit.py`** default **`nano-banana-2-edit`** — **identical** `S076_EDIT_LEAD_IN` + `S076_PROMPT_FLUX`; `--with-flex` ignored for Nano. |
| 2026-03-26 | **Project policy:** still pipeline defaults to **Nano Banana 2**; Cursor skill **`nano-banana-2-prompting`**; Flux optional only. |
| 2026-03-26 | **S076** default ref **`panels/panel_s076.png`** (was full `016.jpg`) — single-panel crop for Fal uploads. |

*Update this file when you discover new FLUX.2 or Fal edit behaviors worth standardizing.*
