# Manga greyscale → color: research and matching notes

**Purpose:** Reusable reference for **interpreting greyscale manga** when adding color (Fal / Nano Banana edits, paint-overs, or prompt writing). Manga has no hue; artists encode **material and lighting** with value, edges, patterns, and highlight **shape**. Colorization should **respect those cues** instead of defaulting everything to dull grey “stand-ins.”

---

## 1. How greyscale signals material

| Cue | What it usually means | Color implication |
|-----|------------------------|-----------------|
| **Hard speculars** — thin graphic whites, clean streaks on curves | Metal, glass, wet or polished surfaces | Use **controlled saturation** in highlights (metal rim, glass reflection); pick **sky/environment color** in reflections. |
| **Soft gradients + dot screens** | Matte surfaces — fabric, skin, painted wood at distance | **Diffuse** colors; avoid chrome unless the panel shows sharp highlights there. |
| **Negative white lines inside solid black** | Fold lines in **very dark cloth** or deep creases | **Matte** dark garment (wool, heavy coat); **not** glossy leather unless line art suggests shine. |
| **Directional hatching / lines** | Form + texture (wood grain, siding, weave) | Align **hue variation** with line direction (e.g. warm wood along plank length). |
| **Uniform stipple / light grain on “white” areas** | Snow, sand, dust, sparkles, or paper fill | In color: decide diegetic read (snow vs golden dust) from **story context**; keep **shadow color** consistent. |
| **Flat darker grey masses** | Glass, shadowed openings, distant shapes | Often **environmental reflection** or **depth**; glass should reflect **sky grade** you commit to for the shot. |

**Techniques in practice:** Screentones (dots, lines, gradients), cross-hatching, solid blacks, and carved highlights are combined to separate materials without color. Introductory overviews: [Shading and texturing a manga page](https://manga-with-stef.com/shading-and-texturing-a-manga-page); [Screentones for shading](https://engineerfix.com/how-manga-artists-use-screentones-for-shading/).

---

## 2. Principles for color matching

1. **Preserve the matte vs shiny split** — If the artist drew **soft folds** in black with white creases, keep the garment **matte**. Put **story-driven warm bounce** on the shadow flank or rim, not a plastic shine across the whole coat.
2. **Same grey ≠ same color** — Ink-black coat vs black hair vs black iron are **different** in color: **cool black** fabric vs **warm brown-black** iron vs **desaturated blue-black** shadows.
3. **High-key areas are underdetermined** — Very light ground or sky in print may be “empty paper + texture.” Color must **choose** snow vs pale stone vs gilded dust; anchor that choice in **continuity** (e.g. chapter arc).
4. **Specular color = environment** — Highlights on metal and glass should **borrow** from the sky and key light (amber hour vs cold overcast).
5. **Small diegetic metals** — Jewelry, monocle frames, buckles can carry **literal gold** without painting the whole scene S010-gilt.

---

## 3. Pitfalls (especially for image-to-edit models)

- **Reference anchoring:** Strong greyscale local values can **pull** the model back toward neutral grey. Strengthen **global light** and **per-material hue locks** in the prompt when the edit must shift mood (e.g. warm foreshadow).
- **Conflicting cues:** Long prompts with many layout constraints may **drown** subtle color direction; repeat **short material/color locks** where the skill guide allows.

---

## 4. Example: *Frieren* ch.81 page 1 (cold open, S001)

Single-panel splash: Denken centered on ornate bench, clapboard building and window behind, light stippled ground, sparkles in air. Greyscale differentiates **heavy coat** (black + crease whites), **wood** (horizontal texture, mid tone), **iron** (gradient + sharp glints), **glass** (flatter midgrey with streaks), **beard** (high key vs coat).

**Directional color read** (see `S001_PROMPT_FLUX` / `S001_EDIT_LEAD_IN` in-repo for full Fal strings):

- **Light:** Soft peach–amber sky and **golden-tinged** fill; foreshadow **El Dorado**, subtler than full ridge-gilt hero shots.
- **Coat:** Matte charcoal / blue-black; **ivory** collar accents; **brown** beard and scalp hair (greyscale high-key beard → **warm brown**, not white) per series lock.
- **Monocle:** Glass + **gold** frame and chain.
- **Bench:** Warm brown wood; dark iron with **champagne / pale gold** rim speculars.
- **Building:** Warm greige siding; window reflecting **amber** sky, warm muntins.
- **Ground:** Snow with **cool** bench contact shadows; sunlit granules may read **champagne** or fine **gold dust** as foreshadow.

Refs: [`panels/eng/panel_s001.png`](../panels/eng/panel_s001.png), [`Frierien-chapter081/stage_02_shot_list.md`](../Frierien-chapter081/stage_02_shot_list.md) (S001), [`docs/denken-appearance-reference.md`](./denken-appearance-reference.md).

---

## Revision log

| Date | Change |
|------|--------|
| 2026-03-30 | Initial doc: greyscale cues, color principles, I2E pitfalls, S001 example. |
