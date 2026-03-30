# Stage 3 — Series bible & Fal.ai prompt kit (Chapter 81 — “El Dorado”)

**Inputs:** [stage_02_shot_list.md](./stage_02_shot_list.md)  
**Use:** Paste **one layer prefix** + **only the characters in frame** + **shot line** + **negative block** into Fal image models (tune strength if using img2img / image-to-image from the manga panel).

**Style target:** High-end **fantasy TV anime** look — soft cel shading, **painterly backgrounds**, natural lighting, restrained linework (inspired by premium seinen adaptation studies). **Do not** reproduce logos, title cards, or exact studio branding.

**Ingest (Stages 1–3):** [`.cursor/skills/manga-chapter-ingest-stages-1-3/SKILL.md`](../.cursor/skills/manga-chapter-ingest-stages-1-3/SKILL.md) — story truth before Fal. **Nano Banana 2 prompts:** [`.cursor/skills/nano-banana-2-prompting/SKILL.md`](../.cursor/skills/nano-banana-2-prompting/SKILL.md) + shared edit lessons in [`docs/flux-2-pro-prompting-guide.md`](../docs/flux-2-pro-prompting-guide.md) (name is historical; Nano default).

**Blocked model (project blacklist):** `fal-ai/stable-cascade/sote-diffusion` — not used.

**Default image pipeline (reference-guided):** **`fal-ai/nano-banana-2/edit`** with uploaded panel(s); prompt structure still follows [FLUX.2 prompting guide](https://docs.bfl.ai/guides/prompting_guide_flux2) habits. **`--model flux-2-pro-edit`** remains available as **legacy** in scripts. Older **Flash** compares are archival only unless noted.

**Single source of truth for scripted prompts:** [`scripts/fal_common.py`](../../scripts/fal_common.py) — **`S001_PROMPT_FLUX`**, **`S002_PROMPT_FLUX`**, **`S003_PROMPT_FLUX*`**, **`S004_PROMPT_FLUX`**, **`S010_PROMPT_FLUX`**, **`S075_PROMPT_FLUX`**, **`S076_PROMPT_FLUX`**, etc.

---

## 1. Global negatives (append to every generation)

```
anime screentone, halftone dots, manga panel border, speech bubble, caption box,
scan typography, watermark, artist signature, subtitles, collage, split panel,
extra fingers, deformed hands, mangled limbs, duplicate faces, low resolution,
text in image, QR code, modern clothing, contemporary objects
```

**Scan note:** If gutters show **TL/PR credits**, crop the panel reference or add: `caption, credits line, translator text`.

**Layout literacy (`013.jpg`–`016.jpg`):** Black vs white **page gutters** cue **memory vs present** (plus mood on **`014.jpg`**). **`016.jpg`** **white** top = **`present`** (**S075**); **black** lower = **`fb_hero`** (**S076+**). Confirm with **Frieren’s scarf** (present **S074**/**S075** vs flashback **S076**). See [stage_01_ingest.md](./stage_01_ingest.md) (gutter subsection). Fal references should be **per-panel crops** when full pages mix tiers.

---

## 2. Layer prefixes (pick one per shot)

Copy the block that matches `Layer` from the shot list.

### `present` / `cold_open` — **PREFIX_PRESENT**

```
Fantasy anime, cinematic composition, soft natural daylight, clear atmospheric perspective,
high-detail background, cohesive color grade, cool-to-neutral Northern-country light,
subtle film grain optional, emotional restraint in faces, no comic halftone.
```

### `fb_macht` — **PREFIX_FB_MACHT**

```
Same anime rendering as present but scene is a darker memory: slightly desaturated,
heavier shadows, cold stone architecture, oppressive scale, villain presence dominant,
subtle vignette, still no manga textures.
```

### `fb_denken` / `fb_couple` — **PREFIX_FB_PERSONAL**

```
Fantasy anime flashback grade: warm lifted shadows OR soft nostalgic haze (choose one per run),
gentle bloom on highlights, period clothing, European fantasy town or interior,
memory-appropriate lighting, no modern elements, no halftone.
```

### `fb_hero` — **PREFIX_FB_HERO**

```
Fantasy anime golden-age adventure memory: lush nature, open sky, particle petals or sun-dust,
hopeful soft light, heroic wardrobe readable, younger versions of known characters consistent,
dreamy but sharp focal plane on faces, no halftone.
```

---

## 3. Character locks (paste only who appears)

**Rule:** For each Fal call, concatenate **only** the lines for characters **visible in that shot** (plus “other people as generic townspeople” when needed).

### Frieren (adult, present timeline)

```
Frieren: petite elf; silver-white hair in low waist-length twin pigtails; long horizontal elf ears;
thick short rounded eyebrows; large teal-green eyes; calm neutral expression;
short white capelet, high collar, thick gold trim; white long-sleeve tunic, gold at cuffs, mid-thigh hem;
black-and-white striped inner collar at neck; dark navy leggings; brown mid-calf boots with straps;
red teardrop earrings on gold studs; dark wood mage staff on back, gold head frame, large red orb focal.
```

### Fern

```
Fern: human mage, taller than Frieren; waist-length purple hair, blunt bangs, hime-cut sidelocks framing face, purple eyes;
butterfly-style hair ornament at back of head; stoic bearing.
Travel (warm): long buttoned white dress, Victorian frilled collar, puffy white sleeves, black boots, long black coat with hood.
Travel (cold / Northern arc): dark blue long dress, cropped light-gray winter jacket, thick braided blue scarf, black boots.
```

### Stark

```
Stark: young warrior; spiky vivid red hair with darker roots; orange eyes; muscular tall build;
black sleeveless or layered shirt, often black turtleneck in cold; baggy black pants, black boots;
red winter coat with cream lapels and cuffs, black fingerless gloves;
white sash at waist; large double-bitted gray-silver battle axe on back with crossbody strap;
silver wrist bracelet (optional visible).
```

### Denken

**Online appearance digest (sources + OTS notes):** [`docs/denken-appearance-reference.md`](../docs/denken-appearance-reference.md)

```
Denken: elderly human mage, magnificent full beard and mustache in warm brown (same family as scalp hair; no grey or white hair), gold monocle on chain over one eye,
dark heavy formal robes with horizontal toggle closures, dignified weary bearing, shorter than Stark.
Anime notes: short **full brown** head hair; **brown** beard, brows, and mustache when face is visible; heavy dark coat or cape; gold monocle;
when seen from behind (e.g. S075 OTS): high stiff collar, broad shoulders, even brown hair on back of head — omit monocle/beard in prompt only because face is off-camera.
```

### Himmel (flashback)

```
Himmel: young human hero, neat short blue hair, kind handsome face, gentle smile,
white hero's cape or high-collared cloak with structured shoulders, noble proportions.
```

### Eisen (flashback)

```
Eisen: dwarf warrior, stocky wide build, short dark hair and beard stubble, practical dark traveling coat.
```

### Flamme (flashback)

```
Flamme: tall human woman mage, long hair tied back, calm authoritative presence, simple light robe, wooden staff.
```

### Frieren (young, flashback)

```
Young Frieren: childlike elf proportions, same white twin-tail hairstyle but slightly smaller frame,
simpler traveling clothes era-appropriate to flashback.
```

### Macht of El Dorado (flashback)

```
Macht: towering aristocratic demon-mage, long hair, cold sharp features, ornate dark military coat,
heavy fur-trimmed mantle, overwhelming height vs Frieren, regal cruel stillness.
```

### Young couple / townsfolk (fb_couple)

```
European fantasy civilian clothing, waistcoats and long dresses, early-industrial fantasy town fashion,
non-unique extras in background low detail.
```

### Memory demon (Qual-like, S038)

```
Monumental ancient demon silhouette behind character, shaggy mane, curved horns, predatory face,
nightmare memory overlay, soft edge blend—not a separate cartoon character in foreground.
```

### Golden El Dorado environment (when needed)

```
World geometry turned to polished gold: hills, rooftops, roads, trees read as solid gilt metal,
specular highlights, warm reflected light, sky still natural for contrast, readable architecture of a walled city.
```

### Great barrier (when needed)

```
Colossal hemispherical magic barrier over a valley, faint iridescent grain, energy dome, grounded at horizon,
landscape visible inside and outside with different treatment, awe scale.
```

### Cathedral interior (S070)

```
Towering gothic sanctuary interior, massive columns, long aisle of steps, radiant backlight from tall stained-glass windows,
ornate altar with winged vertical relic motif, stone floor, dust motes in light beams.
```

---

## 4. Shot micro-lines (optional tail)

Use the **What we see** column from the shot list as prose, shortened to one line. Examples:

| Shot | One-line tail |
|------|----------------|
| S010 | Extreme wide: three travelers on black ridge facing a distant fortified city and valley transformed entirely into gleaming gold; awe scale. |
| S014 | MCU: Frieren surprised — barrier assignment / warden request (page `004.jpg`, second panel in read order). |
| S015 | Extreme wide: gigantic hemispherical magical barrier sealing a golden region; forest foreground (page `004.jpg`, **first** in read order). |
| S036 | Stone hall: kneeling defeated elf mage before towering Macht; low angle on antagonist. |
| S070 | Low angle from behind old mage at nave threshold facing blinding altar and winged reliquary; cathedral scale. |
| S076 | Wide: four adventurers in endless flower meadow, petals in wind; hero in white cloak mid-field. |
| S085 | Close profile: hero soft smile, flower petals drifting past lens, warm forest bokeh. |
| S091 | Split beat: extreme close-up elder eye behind monocle reflecting resolve; medium two-shot elf girl agreeing beside dark-haired mage girl; grassy field and cabin far back. |

---

## 5. First Fal test batch — **assembled prompts**

Use **PREFIX** + **characters** + **tail** + **negatives**.  
Replace each **`[GLOBAL_NEGATIVES]`** line with the full text from **§1 Global negatives** (same paragraph, pasted under the shot description).  
Aspect ratio: default **16:9** for key frames unless you standardize 2.35:1 or 9:16 for shorts.

---

### **S001** — Cold open: Denken on bench (`cold_open`)

Use §2 **`PREFIX_PRESENT`** (same block as `cold_open` in this bible).

```
PREFIX_PRESENT

One figure only: **Denken** centered on **ornate park bench**, **wood building** + **multi-pane window** behind. **Environment:** **golden-hour / gilded** read — chapter **El Dorado** foreshadow (**B1** → **B3** gold Weise, later **gold-textured** town per ingest); **warm** ambient, **pale-gold** ground shimmer, **not** cold grey only; still subtler than **S010** full gilt ridge. **No** on-image chapter title in Fal — typography in post. Bookends **S059**.

[GLOBAL_NEGATIVES]
```

**Fal-ready string:** **`S001_PROMPT_FLUX`** + **`S001_EDIT_LEAD_IN`** in [`scripts/generate_s001_ref_edit.py`](../../scripts/generate_s001_ref_edit.py). Default ref [`panels/panel_s001.png`](../../panels/panel_s001.png). **`--model nano-banana-2-edit`** (default), **`--model flux-2-pro-edit`**, or **`--model both`**. Greyscale→color material locks: [`docs/manga-greyscale-to-color.md`](../../docs/manga-greyscale-to-color.md) §4. Appearance details: [`docs/denken-appearance-reference.md`](../../docs/denken-appearance-reference.md).

---

### **S002** — Weise forest camp, trio (present)

```
PREFIX_PRESENT

Forest clearing camp day: **Stark** by small central fire **viewer-left**; **Frieren** against a tree reading; **Fern** seated **back to camera** foreground; axe and packs.

Northern Plateau / Weise region establishing tone — not golden-city ridge (**S010**).

[GLOBAL_NEGATIVES]
```

**Fal-ready string:** **`S002_PROMPT_FLUX`** + **`S002_EDIT_LEAD_IN`** in [`scripts/generate_s002_ref_edit.py`](../../scripts/generate_s002_ref_edit.py). Default ref [`panels/panel_s002.png`](../../panels/panel_s002.png). **`--model nano-banana-2-edit`** (default), **`--model flux-2-pro-edit`**, or **`--model both`**. See [`.cursor/skills/nano-banana-2-prompting/SKILL.md`](../.cursor/skills/nano-banana-2-prompting/SKILL.md) and [`docs/flux-2-pro-prompting-guide.md`](../docs/flux-2-pro-prompting-guide.md).

---

### **S003** — Fern + squirrel courier (present)

**Fal-ready string:** [`scripts/generate_s003_ref_edit.py`](../../scripts/generate_s003_ref_edit.py) — **`full`** · **`fern-only`** · **`extend-camp`** · **`extend-camp-squirrel`**. Optional **`--squirrel-ref`** with **extend-camp-squirrel** sends **[camp, squirrel]** to **`image_urls`** and **`S003_PROMPT_FLUX_COMPOSITE_SQUIRREL`**. Prompts: **`S003_PROMPT_FLUX*`** in [`fal_common.py`](../../scripts/fal_common.py). Default ref [`panels/panel_s003.png`](../../panels/panel_s003.png). **`--model nano-banana-2-edit`** default; **`16:9`** (optional **`9:16`**). Legacy Flux / **`both`** still available. **Stage 5 I2V (start + end):** [`scripts/generate_s003_kling_i2v.py`](../../scripts/generate_s003_kling_i2v.py) — default **extendcamp → extendcampsquirrel** keyframes on Kling **v2.6** with **`end_image_url`**.

---

### **S004** — Frieren & Fern, grimoire + envelope (present)

```
PREFIX_PRESENT

**Reframed vs manga panel:** **Frieren** **foreground side profile**, **heavy winter coat / scarf**, **open grimoire**; **Fern** **deeper background**, **sealed envelope** toward her — **depth separation**, not a flat two-shot. Upload `panel_s004.png` = identity/locale; **S003** adjacent on `002.jpg`.

Continuity: **Fern** matches **S002** / **S003** travel look; **Frieren** **cold-arc winter**; **Stark** off-panel.

[GLOBAL_NEGATIVES]
```

**Fal-ready string:** **`S004_PROMPT_FLUX`** + **`S004_EDIT_LEAD_IN`** in [`scripts/generate_s004_ref_edit.py`](../../scripts/generate_s004_ref_edit.py). Default ref [`panels/panel_s004.png`](../../panels/panel_s004.png). **`--model nano-banana-2-edit`** (default), **`--model flux-2-pro-edit`**, or **`--model both`**. **Stage 5 I2V:** [`scripts/generate_s004_kling_i2v.py`](../../scripts/generate_s004_kling_i2v.py) — **`Tests/Final/`** driver.

---

### **S005** — Fern + Lernen telegraph (present)

```
PREFIX_PRESENT

**CU:** **Fern** foreground, **letter** read; **soft memory portrait** of **Lernen** (elder First-Class mage) **behind** — **not** Denken. **`panels/panel_s005.png`**.

[GLOBAL_NEGATIVES]
```

**Fal-ready string:** **`S005_PROMPT_FLUX`** + **`S005_EDIT_LEAD_IN`** in [`scripts/generate_s005_ref_edit.py`](../../scripts/generate_s005_ref_edit.py). Default ref [`panels/panel_s005.png`](../../panels/panel_s005.png). **`--model nano-banana-2-edit`** (default), **`--model flux-2-pro-edit`**, or **`--model both`**. **Stage 5 I2V:** [`scripts/generate_s005_kling_i2v.py`](../../scripts/generate_s005_kling_i2v.py) — **`Tests/Final/`** driver.

---

### **S006** — Camp debate: Frieren at tree, Fern by fire (present)

```
PREFIX_PRESENT

**MS Weise camp:** **Frieren** **on tree** reading, **flat** affect; **Fern** **by campfire**, **pressing** unofficial-request beat. **Fal:** **same camera** as `panel_s006` — **no** pull-back / **no** **S002** WS reframe. **Stark** only **optional** **frame-edge** partial if **no** lens change; else off-panel. **Forest floor** seating (no log). **`panels/panel_s006.png`**.

[GLOBAL_NEGATIVES]
```

**Fal-ready string:** **`S006_PROMPT_FLUX`** + **`S006_EDIT_LEAD_IN`** in [`scripts/generate_s006_ref_edit.py`](../../scripts/generate_s006_ref_edit.py). Default ref [`panels/panel_s006.png`](../../panels/panel_s006.png). **`--model nano-banana-2-edit`** (default), **`--model flux-2-pro-edit`**, or **`--model both`**. **Stage 5 I2V:** [`scripts/generate_s006_kling_i2v.py`](../../scripts/generate_s006_kling_i2v.py) — driver still **`Tests/Final/`**, default **`duration` \"5\"**.

---

### **S007** — Layered camp composite (present)

**Fal-ready string:** **`S007_PROMPT_FLUX`** + **`S007_EDIT_LEAD_IN`** in [`scripts/generate_s007_ref_edit.py`](../../scripts/generate_s007_ref_edit.py). Ref [`panels/panel_s007.png`](../../panels/panel_s007.png). **Stage 5 I2V:** [`scripts/generate_s007_kling_i2v.py`](../../scripts/generate_s007_kling_i2v.py) — driver still **`Tests/Final/`**, default **`duration` \"10\"** (layered read).

---

### **S008** — Daytime camp grimoire trio (present)

**Fal-ready string:** **`S008_PROMPT_FLUX`** + **`S008_EDIT_LEAD_IN`** in [`scripts/generate_s008_ref_edit.py`](../../scripts/generate_s008_ref_edit.py). Ref [`panels/panel_s008.png`](../../panels/panel_s008.png). **Stage 5 I2V:** [`scripts/generate_s008_kling_i2v.py`](../../scripts/generate_s008_kling_i2v.py) — **`Tests/Final/`**, default **`duration` \"5\"**.

---

### **S009** — Forest path walk (present)

**Fal-ready string:** **`S009_PROMPT_FLUX`** + **`S009_EDIT_LEAD_IN`** in [`scripts/generate_s009_ref_edit.py`](../../scripts/generate_s009_ref_edit.py). Ref [`panels/panel_s009.png`](../../panels/panel_s009.png). **Stage 5 I2V:** [`scripts/generate_s009_kling_i2v.py`](../../scripts/generate_s009_kling_i2v.py) — **`Tests/Final/`**, **`duration` \"5\"**; **`--experiment 1`** slow casual walk + doc handheld / soft push-in; **`--experiment 2`** same + dolly + lateral parallax arc + optional slow creep; **`--experiment 3`** single clip merging **1+2** camera grammar; **`--experiment 4`** **TV-anime limited animation** — subtler motion, **Fern** especially soft, **near-locked** camera (steer away from smooth 3D / parallax tour).

---

### **S010** — Golden Weise ridge (present)

Use **`S010_PROMPT_FLUX`** in [`scripts/fal_common.py`](../../scripts/fal_common.py) — it merges **PREFIX_PRESENT-level style**, **wiki-aligned Frieren / Fern (cold) / Stark**, **golden environment**, and cue blocks in one edit-ready string.

**Edit script:** [`generate_s010_ref_edit.py`](../../scripts/generate_s010_ref_edit.py) — **`S010_EDIT_LEAD_IN`** + **`S010_PROMPT_FLUX`**. Default ref [`panels/panel_s010.png`](../../panels/panel_s010.png). **`--model nano-banana-2-edit`** (default), **`--model flux-2-pro-edit`** (optional **`--with-flex`**), or **`--model both`**.

**Stage 5 I2V:** [`scripts/generate_s010_kling_i2v.py`](../../scripts/generate_s010_kling_i2v.py) — **`Tests/Final/`** hero still; default **`duration` \"5\"** (optional **`10`**); subtle breeze on **backs**, **gilt** shimmer / haze, **very slow** push-in **or** near-locked camera — **no** faces-to-camera drift.

For manual Fal UI runs, prepend the §2 **PREFIX_PRESENT** block, then paste the character + scene lines from `fal_common.py`, then §1 **Global negatives**.

---

### **S011** — Stark awe at gold (present)

**Fal-ready string:** **`S011_PROMPT_FLUX`** in [`scripts/fal_common.py`](../../scripts/fal_common.py). **Edit:** [`generate_s011_ref_edit.py`](../../scripts/generate_s011_ref_edit.py); ref [`panels/panel_s011.png`](../../panels/panel_s011.png). **Stage 5 I2V:** [`scripts/generate_s011_kling_i2v.py`](../../scripts/generate_s011_kling_i2v.py) — **`Tests/Final/`**, **`duration` \"5\"**; **MCU** — micro awe on **Stark**, gaze **frame left**, **tripod-locked** camera, gold vista shimmer.

---

### **S012** — Wide backs + gilt Weise (present)

**Fal-ready string:** **`S012_PROMPT_FLUX`** + edit script [`generate_s012_ref_edit.py`](../../scripts/generate_s012_ref_edit.py); ref [`panels/panel_s012.png`](../../panels/panel_s012.png). **Stage 5 I2V:** [`scripts/generate_s012_kling_i2v.py`](../../scripts/generate_s012_kling_i2v.py) — **`Tests/Final/`**, **`duration` \"5\"** / **`10`**; **WS** **Fern – Frieren – Stark** **backs** toward **full gilt** city / valley; restrained motion, optional hairline creep — **Macht / El Dorado** lore read.

---

### **S015** — Great barrier (present)

```
PREFIX_PRESENT

Frieren (optional tiny reaction insert — omit if not in frame).

Landscape extreme wide: colossal hemispherical magic barrier enclosing distant golden region;
outer forest and peaks in foreground; barrier surface subtle shimmering texture; epic fantasy vista.

[GLOBAL_NEGATIVES]
```

---

### **S036** — Macht defeat memory (fb_macht)

```
PREFIX_FB_MACHT

Young Frieren, Macht of El Dorado in same frame.

Interior palace courtyard with tall arches and stone floor; young white-haired elf girl kneeling or collapsed before
an immense standing Macht; low camera emphasizing height and menace; cold directional light; memory stillness.

[GLOBAL_NEGATIVES]
```

---

### **S070** — Cathedral altar (present)

```
PREFIX_PRESENT

Denken alone in frame from behind.

Interior of monumental cathedral: viewer behind elderly robed man at bottom of wide stairs;
ahead, blinding sacred light through tall windows; ornate winged altar relic towering above; dust in light; stone pillars flanking.

[GLOBAL_NEGATIVES]
```

---

### **S075** — Denken & Frieren snowy OTS (`present`)

```
PREFIX_PRESENT

Denken and adult Frieren only — present thread; **wide snowfield**, **distant ridges with rock/scree through snow**, low overcast sky; horizontal OTS — Denken **back to camera**.

Frieren: **thick travel scarf**, winter coat; **S074** continuity. Not the flower-field beat (**S076**). Default ref crop [`panels/panel_s075.png`](../../panels/panel_s075.png).

[GLOBAL_NEGATIVES]
```

**Fal-ready string:** **`S075_PROMPT_FLUX`** (**v11:** Denken **brown** head hair; not Frieren’s silver-white) + **`S075_EDIT_LEAD_IN`** in [`scripts/generate_s075_ref_edit.py`](../../scripts/generate_s075_ref_edit.py) — **same concatenated prompt** for **`--model nano-banana-2-edit`** (default) or **`--model flux-2-pro-edit`** (legacy). Nano: `--aspect-ratio 16:9`, `--resolution 1K`. Flux: `landscape_16_9`. See [`.cursor/skills/nano-banana-2-prompting/SKILL.md`](../.cursor/skills/nano-banana-2-prompting/SKILL.md) and [`docs/flux-2-pro-prompting-guide.md`](../docs/flux-2-pro-prompting-guide.md) §3.4 / §6.

---

### **S076** — Hero party flower field (fb_hero)

```
PREFIX_FB_HERO

Frieren, Himmel, Heiter (priestly figure in traveling robes), Eisen; all younger adventuring versions.

Extreme wide: sunlit fantasy meadow completely covered in wildflowers; four companions spaced in field;
gentle wind lifting thousands of petals; distant tree line; heroic calm; Himmel's white cloak readable at center depth.

[GLOBAL_NEGATIVES]
```

**Fal-ready string:** `S076_PROMPT_FLUX` + `S076_EDIT_LEAD_IN` in [`scripts/generate_s076_ref_edit.py`](../../scripts/generate_s076_ref_edit.py) — **same** text for **`--model nano-banana-2-edit`** (default) or **`--model flux-2-pro-edit`** (legacy; optional `--with-flex`). **`S076_PROMPT_FLUX`** lives in [`fal_common.py`](../../scripts/fal_common.py). **Default ref:** [`panels/panel_s076.png`](../../panels/panel_s076.png); `--ref` for full page or alt crops. QC: [stage_04_s076](stage_04_s076_visual_qc_log.md).

---

### **S082** — Scenic dialogue backing (fb_hero)

```
PREFIX_FB_HERO

No faces required dominant — grass, wildflowers, tree trunks soft focus; suggest two seated figures small in frame or off-camera;
peaceful forest clearing, afternoon warmth, shallow depth of field, anime background art quality.

[GLOBAL_NEGATIVES]
```

---

### **S085** — Himmel profile petals (fb_hero)

```
PREFIX_FB_HERO

Himmel close profile or three-quarter; warm gentle smile.

Shallow depth, drifting flower petals in foreground, forest bokeh, soft rim light on hair, emotional beat, no text.

[GLOBAL_NEGATIVES]
```

---

### **S091** — Chapter close alliance (present)

```
PREFIX_PRESENT

Denken, Frieren, Fern in final beat; Stark may appear distant.

Two-part composition in one frame or consecutive gens stitched: (A) extreme close-up one elder eye behind monocle;
(B) medium shot elf girl with faint confident expression and dark-haired girl beside her, grassy rural field, small wooden hut far background, afternoon.

[GLOBAL_NEGATIVES]
```

---

## 6. Run log template (fill per Fal job)

| field | value |
|--------|--------|
| date | |
| Fal model id | |
| shot id(s) | |
| seed | |
| resolution | |
| img2img strength (if any) | |
| ref image | which panel file |
| pass/fail | |
| notes | identity drift? hands? gold read? |

---

## 7. Stage 4 handoff

- [ ] Pick **hero reference stills** from first passes (faces: Frieren, Denken, Himmel).  
- [ ] Lock **one** gold-material recipe for all El Dorado shots.  
- [ ] Run **image-to-video** only on stable stills (e.g. S085 petals, S010 slow push).  

---

*Stage 3 complete — bible + first-test prompt pack ready for Fal.*
