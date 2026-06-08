# Denken — appearance reference (online sources)

**Purpose:** Single place to align **Flux / Fal prompts**, **shot bibles**, and QC with published descriptions of **Denken** (デンケン) from *Frieren: Beyond Journey’s End* (*Sousou no Frieren*).

**Not official studio production art** — summarize third-party pages + sensible adaptation notes. Re-check sources if character sheets are updated.

---

## One-line summary

Elderly human **Imperial / first-class mage**: **heavy beard**, **monocle** (see side below), **dark long coat or robe** with **light collar accents**, **stocky** dignified bearing; **brown** head hair **and brown beard/mustache** in this pipeline — **no grey, silver, or white** hair (aligns with Fandom “brown hair” + “long, thick beard” as a single brown read; avoids model drift toward elderly white beard).

---

## Sourced appearance notes

### Frieren Wiki (Fandom)

Source: [Denken — Frieren Wiki](https://frieren.fandom.com/wiki/Denken) (retrieved 2026-03-26).

Quoted **Appearance** section:

> Denken is an elderly man with **brown hair** and a long, thick beard. He wears a **monocle on his left eye**. He is commonly seen wearing a **long, black robe with white collars**.

Additional useful pointers from the same article:

- First-class mage; Imperial background; Weise region history (story context for late arcs).
- Gallery for stills: [Denken/Gallery](https://frieren.fandom.com/wiki/Denken/Gallery).

**Note:** This pipeline locks **brown** for **scalp and facial hair** so Fal does not default to **grey / white** elder hair; scope **hair** vs **garment** in prompts to limit color bleed (see prompting guide).

### MyAnimeList (character page)

Source: [Denken — MyAnimeList](https://myanimelist.net/character/215250/Denken) (retrieved 2026-03-26).

- Role summary emphasizes **elderly Imperial mage**, composure, leadership.
- Does **not** spell out costume tokens (monocle, toggles) — use for **role** and **age class**, not fine wardrobe.

### Anime news / promotional context

- Character emphasis ahead of anime introduction: [Sportskeeda — Denken PV ahead of episode 18](https://www.sportskeeda.com/anime/news-frieren-beyond-journey-s-end-reveals-character-pv-denken-ahead-of-episode-18) (third-party summary; useful for **existence of official PV** and casting, not fine art QA).

---

## Consensus checklist (for prompting)

Use **positive** tokens; scope **hair** vs **beard** vs **garment** to reduce FLUX color bleed (see [`flux-2-pro-prompting-guide.md`](./flux-2-pro-prompting-guide.md)).

| Element | Widely safe for anime-style “Denken read” | Source split to be aware of |
|--------|--------------------------------------------|------------------------------|
| **Age / build** | Elderly, **stocky**, broad-shouldered, dignified | — |
| **Beard** | **Long thick beard** per Fandom; this repo: **brown** (magnificent full beard), not white | Some broadcast stills skew lighter — prompts enforce **brown** for consistency |
| **Head hair** | Fandom and this repo: **short brown** | Reserve **silver-white** for Frieren only |
| **Monocle** | **Left eye** per Fandom | Gold / chain details: use [`stage_03_series_bible.md`](../Frierien-chapter081/stage_03_series_bible.md) series lock |
| **Coat / robe** | **Long dark** outer layer; **white or pale collar** accents; **horizontal toggles / frogging** in many formal travel shots (see project bible) | Exact pattern differs shot to shot |
| **OTS / back-only shots** | Describe only **back of head**, **collar**, **shoulders** — avoid **beard/monocle** tokens if the **panel does not show the face** (prevents rotation / wrong face) | [`stage_04_s075_visual_qc_log.md`](../Frierien-chapter081/stage_04_s075_visual_qc_log.md) |

---

## This repo’s convention (Chapter 81 pipeline)

For **`present`** Fal shots (e.g. S075 with `panels/eng/panel_s075.png`):

- **Head hair:** **Brown** (neat, full from behind in OTS), **not** ash grey and **not** silver-white (reserve silver-white for Frieren’s elf hair only).
- **Beard / brows:** **Brown**, matching head hair; **no** grey or white facial hair on full-face shots.
- **Beard / monocle:** Omitted in **strict OTS** prompts when the reference is **back-only**; full-face shots should restore **brown beard and mustache** + **gold monocle on chain** per [`stage_03_series_bible.md`](../Frierien-chapter081/stage_03_series_bible.md) § Denken.

Code: `S075_PROMPT_FLUX` and `S075_EDIT_LEAD_IN` in [`scripts/fal_common.py`](../scripts/fal_common.py) / [`scripts/generate_s075_ref_edit.py`](../scripts/generate_s075_ref_edit.py).

---

## Revision log

| Date | Change |
|------|--------|
| 2026-03-26 | Initial doc: Fandom + MAL + pipeline convention links. |
| 2026-03-25 | Repo convention: **brown** head hair (anime-accurate); v11 `S075_PROMPT_FLUX`. |
| 2026-03-30 | **Brown** beard and mustache pipeline-wide (no grey/white hair); aligns prompts with user lock + Fandom beard wording. |
