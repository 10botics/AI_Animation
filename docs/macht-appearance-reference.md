# Macht of El Dorado — appearance reference

**Purpose:** Single place to align **Fal / Nano Banana prompts**, **shot bibles**, and QC with published descriptions of **Macht of El Dorado** (マハト) from *Frieren: Beyond Journey’s End* (*Sousou no Frieren*).

**Not official studio production art** — summarize third-party pages, user-supplied reference stills, and sensible adaptation notes. Re-check sources if character sheets are updated.

**Chapter 81 pipeline shots:** **S034** (defeat flashback, `fb_macht`), **S050** (throne room, `fb_denken`), and any later Macht beats should share the locks below.

---

## One-line summary

Towering **demon lord of El Dorado**: **long slicked-back burgundy hair**, **two long curved horns** from the temples, **pale blue eyes** with **heavy eyebags** (tired, sleepless read). **Dark green high-collared tunic** to the knees, **golden diagonal chest sash with tassels**, **three golden arm braces with yellow tassels** on the **right arm**, **red gloves**, **Stone Bracelet of Servitude** on the **right hand** (under sleeves when equipped). Signature **large dark-blue coat** draped on the **left shoulder only** — his **combat weapon** (transforms to **gold** for sword or shield forms).

---

## Reference images (this repo)

| File | Use |
|------|-----|
| [`reference/macht/macht_portrait_three-quarter.png`](./reference/macht/macht_portrait_three-quarter.png) | Three-quarter portrait — burgundy hair, horns, blue eyes, eyebags, green collar, gold sash, red glove, blue coat on left shoulder |
| [`reference/macht/macht_profile_close.png`](./reference/macht/macht_profile_close.png) | Profile — horn curve, slicked hair, green standing collar with gold trim, blue coat with light fur collar |
| [`reference/macht/macht_coat_magic_glow.png`](./reference/macht/macht_coat_magic_glow.png) | Upper body — golden arm braces + tassels, red glove, blue coat volume, magic glow from right palm (coat-as-weapon beat) |

Manga panel refs for layout/chirality: [`panels/eng/panel_s034.png`](../panels/eng/panel_s034.png) (defeat memory, `007.jpg`).

---

## Sourced appearance notes

### Frieren Wiki (Fandom)

Source: [Macht of El Dorado — Frieren Wiki](https://frieren.fandom.com/wiki/Macht_of_El_Dorado) (user excerpt, 2026-07-13).

**Hair & face**

- Long, **slicked-back burgundy** hair.
- **Two long, curved horns** emerging from the **temples**.
- **Blue eyes** with **heavy eyebags** underneath — tired, sleepless look.

**Garments**

- **Dark green, high-collared shirt** reaching **down to the knees**.
- **Golden diagonal sash** with **tassels**, stretching from **left shoulder across the chest**.
- **Three golden braces** with **tassels** on the **right arm**.
- **Red gloves**.
- **Stone Bracelet of Servitude** equipped on the **right hand**, typically **under the sleeves** when worn.

**Coat (weapon)**

- **Large blue coat** worn on the **left shoulder only** (asymmetric drape, not a symmetric double-breasted jacket).
- The coat is his **primary weapon**: can **transform to gold** and back; often shaped into a **large sword** in combat; can remain coat-shaped and turn **gold as a shield**.

Gallery for additional stills: [Macht of El Dorado/Gallery](https://frieren.fandom.com/wiki/Macht_of_El_Dorado/Gallery).

---

## Consensus checklist (for prompting)

Use **positive** tokens; scope **hair**, **eyes**, **shirt**, **coat**, and **gold accents** separately to reduce color bleed (see [`flux-2-pro-prompting-guide.md`](./flux-2-pro-prompting-guide.md)).

| Element | Anime-accurate lock | Manga / greyscale panel note |
|--------|---------------------|------------------------------|
| **Build** | **Very tall**, slender aristocratic demon lord; overwhelming height vs young Frieren | Line art emphasizes vertical dominance |
| **Hair** | **Burgundy / deep magenta**, long, **slicked back**, flows behind shoulders | B&W scans read as light grey screentone — **color to burgundy** in Fal |
| **Horns** | **Two** thick **curved** horns from **temples**; pale bone/beige with ridged texture | Keep horn count **exactly two** |
| **Eyes** | **Pale blue**, narrow; **heavy dark eyebags**; weary, not bright cheerful | |
| **Ears** | Pointed elf-like ears (visible in color refs) | |
| **Shirt / tunic** | **Dark forest green**, **high standing collar** with **gold trim** at collar edge; **knee-length** tunic in full-body shots | Do not swap to generic black military tunic unless panel is extreme distance |
| **Chest sash** | **Golden-yellow diagonal band** from **left shoulder** across chest; **tassel fringe** along lower edge | |
| **Right arm** | **Three golden braces** stacked on upper arm; **long yellow tassels** hanging from braces | |
| **Hands** | **Red / maroon gloves**; **Stone Bracelet of Servitude** on **right wrist** when story requires it (often hidden under sleeve) | Omit bracelet token if hands not visible |
| **Coat** | **Large voluminous dark navy-blue coat** draped **only on left shoulder**; heavy fabric, floor-length when standing; **not** symmetrically worn | Manga flashback may read as black cloak — **color to navy blue** for anime stills |
| **Coat (combat)** | Can **glow gold**, form **gold sword**, or **gold shield** — use only when beat calls for magic/combat transform | S034 defeat memory: coat usually **normal blue**, not mid-transform |
| **Boots** | Dark polished boots (full-length shots) | |
| **Expression** | Regal, cold, weary menace; looking **down** at defeated Frieren in S034 | Not smirking hero energy unless beat demands |

---

## Fal-ready character lock (paste block)

Use in **`stage_03_series_bible.md`**, **`fal_common.py`**, and per-shot `*_PROMPT_FLUX` bodies when Macht is on-screen.

```
Macht of El Dorado: towering demon lord; very tall slender build; long slicked-back burgundy hair;
two long curved pale horns from temples; pointed ears; pale blue eyes with heavy dark eyebags (tired sleepless look);
dark forest-green high-collared knee-length tunic with gold collar trim;
golden diagonal chest sash from left shoulder with tassel fringe;
three golden arm braces with yellow tassels on right upper arm;
red maroon gloves; Stone Bracelet of Servitude on right wrist when hands visible;
large voluminous dark navy-blue coat draped on left shoulder only (asymmetric, floor-length when standing);
dark boots; regal cold menace; overwhelming height vs young Frieren.
Coat weapon (combat beats only): can transform to gold — large gold sword or gold shield form.
```

**Negatives (Macht-specific, append to global negatives when needed):** `third horn, short horns, symmetric double coat, black hair, silver hair, pale white hair, red coat, missing horns, cheerful smile, modern clothing`

---

## Manga greyscale → anime color (S034 / panel_s034)

[`panels/eng/panel_s034.png`](../panels/eng/panel_s034.png) is **B&W manga**. See [`manga-greyscale-to-color.md`](./manga-greyscale-to-color.md).

| Greyscale cue in panel | Anime color lock |
|------------------------|------------------|
| Light screentone hair | **Burgundy** hair (not silver-white — reserve for Frieren) |
| Dark coat mass on one shoulder | **Navy-blue** asymmetric coat (left shoulder) |
| Dark tunic body | **Dark green** high collar shirt |
| Light diagonal chest band | **Golden** sash with tassels |
| Fine vertical rain lines | Keep **vertical rain** + cool desaturated flashback grade |

Composition and chirality still come from the **panel upload**; color locks come from this bible and the reference PNGs above.

---

## This repo’s convention (Chapter 81 pipeline)

| Shot | Layer | Macht notes |
|------|-------|-------------|
| **S034** | `fb_macht` | WS defeat memory — Macht standing, young Frieren kneeling; rain, stone arcade; coat **normal blue**, not gold-transform |
| **S050** | `fb_denken` | Throne room — seated or enthroned Macht; **same costume family** as S034 |

Code: **`S034_PROMPT_FLUX`** in [`scripts/fal_common.py`](../scripts/fal_common.py); **`S034_EDIT_LEAD_IN`** (+ composite lead-in) in [`scripts/generate_s034_ref_edit.py`](../scripts/generate_s034_ref_edit.py). **Default:** panel + [`macht_portrait_three-quarter.png`](./reference/macht/macht_portrait_three-quarter.png) multi-ref.

Stage 2: [`Chapter-81/stage_02_shot_list.md`](../Chapter-81/stage_02_shot_list.md) — S034 row.  
Stage 3: [`Chapter-81/stage_03_series_bible.md`](../Chapter-81/stage_03_series_bible.md) — §3 Macht + §5 S034.

---

## Revision log

| Date | Change |
|------|--------|
| 2026-07-13 | Initial doc: Fandom appearance excerpt, three reference PNGs, Fal lock block, S034 greyscale mapping, pipeline cross-links. |
