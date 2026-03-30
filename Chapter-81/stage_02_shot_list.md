# Stage 2 — Shot list: Frieren Chapter 81 (“El Dorado”)

**Source pages:** `Frierien-chapter081\001.jpg`–`018.jpg`  
**Based on:** [stage_01_ingest.md](./stage_01_ingest.md)  
**Reading order (manga, not Western comics):** On each page, shots follow **Japanese read path**: **right → left** within a row or strip, **top → bottom** across the page. **Do not** order panels **left → right** by screen position.

**Cross-check:** On English scans, **speech-bubble sequence** (how the translation is meant to be read) must agree with that path. If anything was originally listed by LTR geometry, **re-verify** against balloons or JP layout before treating shot IDs as story truth.

**Total shots:** **91** (one shot ≈ one panel; title page = one establishing shot).

**Ingest sweep (2026-03-25):** RTL row order is **verified in prose** for **`002.jpg`–`004.jpg`** only. Pages **`005.jpg`–`018.jpg`** still need a **balloon-order** pass if any tier was first keyed LTR — see [stage_01_ingest.md](./stage_01_ingest.md) §5.1. Per-shot **Characters (on-screen \| vicinity)** is **not** yet a dedicated column on every row (skill target); **§ Character snapshot** below is chapter-level shorthand.

---

## Character snapshot (on-screen · vicinity)

Roll-up by page file for Stage 4 continuity (detail still in each row’s **What we see**).

| Page | On-screen (typical) | Vicinity / implied |
|------|---------------------|---------------------|
| `001.jpg` | Denken | — |
| `002.jpg` | Frieren, Fern, Stark, squirrel messenger | — |
| `003.jpg` | Frieren, Fern, Stark | — |
| `004.jpg` | Frieren, Fern, Stark, Denken | — |
| `005.jpg` | Frieren, Fern, Stark, Denken | — |
| `006.jpg` | Frieren, Fern, Stark, Denken | — |
| `007.jpg` | Frieren, Fern, Stark · Macht (fb **S036**) | Denken not in scene |
| `008.jpg` | Frieren, Fern, Stark, Denken · Qual (memory **S038**) | — |
| `009.jpg` | Frieren, Fern, Stark, Denken | — |
| `010.jpg` | Younger Denken, court, archive figures · **Macht** (throne **S050**) | Present-age Denken (**S049**); party traveling **off-panel** |
| `011.jpg` | Denken · old friend (**S052**) | — |
| `012.jpg` | Denken | Party not shown (solitary return) |
| `013.jpg` | Young Denken & wife (fb) · present Denken · Frieren, Stark | Fern (**S065** edge / next beat) · townspeople (**S063**) |
| `014.jpg` | Denken | — |
| `015.jpg` | Bride & groom (fb) · Denken · Frieren | — |
| `016.jpg` | Denken & Frieren (present **S075**) · young Frieren, Himmel, party (fb **S076–S078**) | — |
| `017.jpg` | Young Frieren, Himmel, Flamme (fb) | — |
| `018.jpg` | Frieren, Fern, Stark, Denken · Himmel (memory **S087**) | — |

---

## Legend

| Field | Meaning |
|--------|---------|
| **Layer** | `present` · `cold_open` · `fb_denken` (past career/regret) · `fb_couple` (young Denken-era town life) · `fb_macht` (defeat memory) · `fb_hero` (Hero party / Himmel / Flamme) |
| **Framing** | WS / MS / MCU / CU / ECU / Profile / OTS (over-the-shoulder) / EST (establishing) |
| **Beat** | Story hinge from Stage 1 (B1–B17) |

**Continuity locks (chapter-wide):** Party travel outfits; Denken = beard + **monocle** + dark robes; golden El Dorado = coherent metallic look when it appears; flashbacks get softer light / line screentone cues vs crisp present.

**Manga gutters (this scan, esp. `013.jpg`–`016.jpg`):** **Black** surround often marks **memory** or **heavier / more enclosed** beats; **white** surround often marks **present-day Denken** where the page splits (**013**, **015**). Exceptions: **`014.jpg`** is **all black gutters** but **S068–S070 = `present`** (solemn sacred approach, not flashback). **`016.jpg`** is **split timeline on one page:** **white-gutter top tier = `present`** (**S075**: Denken + **Frieren with travel scarf**, continues **S074**); **black-gutter tiers below = `fb_hero`** flashback (young Frieren **without** scarf, **S076–S078**). **Always use the shot `Layer` column for truth** — confirm with wardrobe (scarf vs not).

---

## Summary

| Page | File | Shots | Primary beat(s) |
|------|------|-------|-----------------|
| 001 | `001.jpg` | 1 | B1 |
| 002 | `002.jpg` | 6 | B2 |
| 003 | `003.jpg` | 6 | B3 |
| 004 | `004.jpg` | 5 | B4 |
| 005 | `005.jpg` | 5 | B5 |
| 006 | `006.jpg` | 7 | B6 |
| 007 | `007.jpg` | 6 | B7 |
| 008 | `008.jpg` | 5 | B8 |
| 009 | `009.jpg` | 6 | B9 |
| 010 | `010.jpg` | 3 | B9–B10 |
| 011 | `011.jpg` | 5 | B10 |
| 012 | `012.jpg` | 5 | B11 |
| 013 | `013.jpg` | 7 | B12 |
| 014 | `014.jpg` | 3 | B13 |
| 015 | `015.jpg` | 4 | B14 |
| 016 | `016.jpg` | 4 | B15 |
| 017 | `017.jpg` | 7 | B16 |
| 018 | `018.jpg` | 6 | B17 |

---

## Shots by page

### Page 001 — `001.jpg` — cold open

| ID | Layer | Framing | Beat | What we see | Continuity |
|----|-------|---------|------|-------------|------------|
| **S001** | `cold_open` | MS–WS | B1 | Elderly mage (Denken) sits on ornate park bench; wooden building & window behind; chapter title “Chapter 81 · El Dorado” on-art (anime: optional title card). **Fal:** **gold-tinged / gilded** ambience — foreshadows **El Dorado** / **golden Weise** (Stage 1–3 arc), not icy neutral-only. | Bookends **S059** empty bench; same monocle/beard as present Denken. Ref [`panels/panel_s001.png`](../../panels/panel_s001.png) (full `001.jpg`). **`S001_PROMPT_FLUX`** + [`generate_s001_ref_edit.py`](../../scripts/generate_s001_ref_edit.py) — **strip** on-art title for still; titles in post. |

---

### Page 002 — `002.jpg` — Northern Plateau camp

**Manga read order:** one wide (row 1) → row 2 **right → left** (squirrel **then** letter) → row 3 **right → left** (Lernen line → MS debate → Fern CU close). *Earlier ingest listed the middle row LTR; corrected 2026-03-26.*

| ID | Layer | Framing | Beat | What we see | Continuity |
|----|-------|---------|------|-------------|------------|
| **S002** | `present` | WS EST | B2 | Forest camp day: Stark by small fire; Frieren leaning on tree reading; Fern seated back to camera; axe & packs. | EST Weise region. Ref [`panels/panel_s002.png`](../../panels/panel_s002.png). |
| **S003** | `present` | MCU Profile | B2 | **First (viewer’s right):** Fern; small **squirrel-like messenger** with bag at her side — delivers the beat before the letter read. | Fern hair/coat; letter delivery. Ref [`panels/panel_s003.png`](../../panels/panel_s003.png). |
| **S004** | `present` | MS | B2 | **Second (viewer’s left):** Frieren holds **open grimoire** (bound spellbook); Fern faces her with **sealed envelope**; “Continental Magic Association?” line. | Fal: **reframed** — Frieren **side profile** foreground, Fern **deeper background** (not flat panel lens). Ref [`panels/panel_s004.png`](../../panels/panel_s004.png). **`S004_PROMPT_FLUX`** + `generate_s004_ref_edit.py`. |
| **S005** | `present` | CU | B2 | **Third row, right:** Fern profile; faded memory portrait / telegraph of **Lernen** in BG; “personal request from Lernen” beat. | Telegraph sender. Ref [`panels/panel_s005.png`](../../panels/panel_s005.png). **`S005_PROMPT_FLUX`** + [`generate_s005_ref_edit.py`](../../scripts/generate_s005_ref_edit.py). |
| **S006** | `present` | MS | B2 | **Third row, middle:** Camp angle — Frieren at tree, flat expression; Fern pressing (trouble / unofficial request), **looking toward Frieren**. | Ref [`panels/panel_s006.png`](../../panels/panel_s006.png); **Fal:** **camera locked** to panel (no wide reframe); **Stark** optional edge only; **forest floor** (no log). **`S006_PROMPT_FLUX`** + [`generate_s006_ref_edit.py`](../../scripts/generate_s006_ref_edit.py). |
| **S007** | `present` | MCU composite | B2 | **Layered camp beat** (same comic moment as **B3** annoyance dialogue in read order): **translucent Frieren** upper; **Stark** + **Fern** below; Fern holds **grimoire**; **daytime**. | Fal ref [`panels/panel_s007.png`](../../panels/panel_s007.png). **`S007_PROMPT_FLUX`** + [`generate_s007_ref_edit.py`](../../scripts/generate_s007_ref_edit.py). |

---

### Page 003 — `003.jpg` — deal & golden Weise

**Manga read order (this page):** **S009** (top tier **viewer’s right**) → **S008** (top tier **left** — grimoire bribe) → **path walking** crop = **`panel_s009` / S009** → **S010** (middle **left** — wide gold ridge hero) → **Stark awe** crop = **`panel_s011` / S011**; **S013** (bottom **right** — same story beat if separate panel) → **S012** (bottom **left** — backs + lore). *Shot rows below follow IDs tied to **`panels/panel_s###.png`**.*

| ID | Layer | Framing | Beat | What we see | Continuity |
|----|-------|---------|------|-------------|------------|
| **S009** | `present` | WS | B3 | **Walking beat:** trio on **forest path** toward camera; **Frieren** carries **rectangular case**; **daylight**. | Fal ref [`panels/panel_s009.png`](../../panels/panel_s009.png). **`S009_PROMPT_FLUX`** + [`generate_s009_ref_edit.py`](../../scripts/generate_s009_ref_edit.py). *(Manga dialogue order for “hate that guy” is a different tier; **panel file for S009** here = path shot.)* |
| **S008** | `present` | MS | B3 | **Daytime** camp: **Fern** back to camera; **Frieren** holds **open grimoire**; Stark rear left “Eh.” | Same camp palette as **S002**/**S006**. Ref [`panels/panel_s008.png`](../../panels/panel_s008.png). **`S008_PROMPT_FLUX`** + [`generate_s008_ref_edit.py`](../../scripts/generate_s008_ref_edit.py). |
| **S011** | `present` | MCU | B3 | **Stark** reaction—**awe** at **gold** as far as the eye can see; looks **toward frame left** at vista. | Fal ref [`panels/panel_s011.png`](../../panels/panel_s011.png). **`S011_PROMPT_FLUX`** + [`generate_s011_ref_edit.py`](../../scripts/generate_s011_ref_edit.py). Path-walking trio lives on **`panel_s009`** / **S009**. |
| **S010** | `present` | WS HERO | B3 | **Ridge overlook:** trio tiny vs vast valley—**Fortified City of Weise** + trees all **gold texture**. Key VFX shot. | Define gold material once; reuse. Ref [`panels/panel_s010.png`](../../panels/panel_s010.png). |
| **S013** | `present` | CU low | B3 | Stark looking up—awe at endless gold. | Same beat as **S011** if no separate crop; add script only if **`panel_s013.png`** exists. |
| **S012** | `present` | WS | B3 | **Wide backs:** **Fern – Frieren – Stark** on overlook; **Fortified City of Weise**; **full gilt** forest / terrain (lore / Macht beat). | Ref [`panels/panel_s012.png`](../../panels/panel_s012.png). **`S012_PROMPT_FLUX`** + [`generate_s012_ref_edit.py`](../../scripts/generate_s012_ref_edit.py). |

---

### Page 004 — `004.jpg` — barrier & Denken

**Manga read order:** row 1 **right → left** — great barrier wide **then** Frieren MCU reactions; row 2 single meet wide; row 3 **right → left** — Denken profile CU **then** MS trio (“hometown inside El Dorado”). *Corrected 2026-03-26 from an LTR row listing.*

| ID | Layer | Framing | Beat | What we see | Continuity |
|----|-------|---------|------|-------------|------------|
| **S015** | `present` | WS VFX | B4 | **Great hemispherical barrier** over El Dorado; chibi Frieren omake in bubble optional. | First in read order on this page. Barrier look = recurring. |
| **S014** | `present` | MCU | B4 | Frieren calm/surprised — barrier job; request to assist warden. | |
| **S016** | `present` | WS | B4 | Forest clearing: **Denken** L; **Stark** mid; **Frieren** R — meet. | First full Denken with party. |
| **S018** | `present` | Profile CU | B4 | Denken monocle; Serie / earnest plea; took over as warden. | |
| **S017** | `present` | MS | B4 | Denken L, Stark mid, Frieren R — “my hometown is inside El Dorado.” | |

---

### Page 005 — `005.jpg` — overlook & past

| ID | Layer | Framing | Beat | What we see | Continuity |
|----|-------|---------|------|-------------|------------|
| **S019** | `present` | WS | B5 | **Four backs** at wooden cliff railing: Stark, Fern, Denken, Frieren; building R; forest. | |
| **S020** | `present` | WS detail | B5 | **Weise** architecture; bust icons Stark/Denken speaking. | Glück / stepfather lore. |
| **S021** | `present` | WS | B5 | Group sky ironic “sublime”; city on plateau. | Scan: hide TL credit in Fal/crop. |
| **S022** | `present` | MS | B5 | Mansion focus in city; Denken monologue. | |
| **S023** | `present` | CU back | B5 | Denken at railing; hometown further north. | |

---

### Page 006 — `006.jpg` — rules & ultimatum

| ID | Layer | Framing | Beat | What we see | Continuity |
|----|-------|---------|------|-------------|------------|
| **S024** | `present` | WS | B6 | Stark, Fern, Denken, Frieren along **wood fence**; forest. Barrier mechanics. | Same fence line as other scenes. |
| **S025** | `present` | MCU | B6 | Fern confused — timeline contradiction. | |
| **S026** | `present` | OTS / back | B6 | Denken from behind; Frieren in FG; grave visit admission. | |
| **S027** | `present` | CU | B6 | Frieren approves Serie’s strategy. | |
| **S028** | `present` | MS | B6 | Denken + Frieren; warden passage privilege. | |
| **S029** | `present` | Profile CU | B6 | Frieren sharp warning — **no help fighting Macht.** | |
| **S030** | `present` | CU | B6 | Denken silent reaction. | |

---

### Page 007 — `007.jpg` — refusal & Macht

| ID | Layer | Framing | Beat | What we see | Continuity |
|----|-------|---------|------|-------------|------------|
| **S031** | `present` | MS | B7 | Fern L, Frieren R — return grimoire; trouble confirmed. | |
| **S032** | `present` | Profile MCU | B7 | Frieren downward; “prioritize lives.” | |
| **S033** | `present` | WS | B7 | Path: Frieren leads; Stark & Fern concerned. | |
| **S034** | `present` | MCU | B7 | Stark skeptical — “big deal”? | |
| **S035** | `present` | CU | B7 | Frieren: **defeated by Macht of El Dorado.** | |
| **S036** | `fb_macht` | WS | B7 | Hall/courtyard: younger Frieren kneeling/defeated; **Macht** stands over her, regal menace. | Macht costume / height. |

---

### Page 008 — `008.jpg` — cliff policy

| ID | Layer | Framing | Beat | What we see | Continuity |
|----|-------|---------|------|-------------|------------|
| **S037** | `present` | WS | B8 | Four backs, fence, calm sea, streak clouds. | |
| **S038** | `present` | MS VFX | B8 | Fern; looming **Qual**-like demon memory. | |
| **S039** | `present` | WS | B8 | Frieren walks away with **suitcase**; Stark watches. | |
| **S040** | `present` | MS | B8 | Frieren by fence + suitcase; sea. | |
| **S041** | `present` | CU | B8 | Frieren — seal Macht; still cannot picture winning. | |

---

### Page 009 — `009.jpg` — Denken’s cold truth

| ID | Layer | Framing | Beat | What we see | Continuity |
|----|-------|---------|------|-------------|------------|
| **S042** | `present` | MS | B9 | Behind Frieren; Fern at fence. | |
| **S043** | `present` | Profile MCU | B9 | Frieren — Macht dies of old age; Serie’s calculus. | |
| **S044** | `present` | Profile | B9 | Denken — “heartless” line. | |
| **S045** | `present` | WS | B9 | Small **wood house**; group; Denken turned away. | |
| **S046** | `present` | CU | B9 | Denken — not admirable about wife’s grave. | |
| **S047** | `present` | High WS | B9 | Walking away from house along path. | |

---

### Page 010 — `010.jpg` — archive flash

| ID | Layer | Framing | Beat | What we see | Continuity |
|----|-------|---------|------|-------------|------------|
| **S048** | `fb_denken` | WS interior | B9 | Dim **library/archive**; elders, staff, kneeling scholar; “I will one day return.” | Younger Denken. |
| **S049** | `fb_denken` | CU | B9 | Present-age Denken outdoors; regret narration. | |
| **S050** | `fb_denken` | MS | B9 | **Throne room**; Denken with ornate staff; **Macht** seated on throne (human form). | Same staff as archive; aligns **S036** / **S050** antagonist styling. |

---

### Page 011 — `011.jpg` — monologue march

| ID | Layer | Framing | Beat | What we see | Continuity |
|----|-------|---------|------|-------------|------------|
| **S051** | `present` | CU | B10 | Denken “heartless man.” | |
| **S052** | `fb_denken` | MS composite | B10 | Denken + memory friends formal hall. | |
| **S053** | `present` | MS | B10 | Denken walking forest. | |
| **S054** | `present` | WS | B10 | Back to Denken on cliff; distant town. | |
| **S055** | `present` | WS | B10 | Back along forest path — purpose stated. | |

---

### Page 012 — `012.jpg` — unchanged town

| ID | Layer | Framing | Beat | What we see | Continuity |
|----|-------|---------|------|-------------|------------|
| **S056** | `present` | MS | B11 | Denken walks past building; peaceful end plan. | Gold-era town. |
| **S057** | `present` | WS | B11 | Street of **half-timber** houses; away from camera. | |
| **S058** | `present` | CU front | B11 | Denken wide eyes “However—”. | |
| **S059** | `present` | MS | B11 | **Empty bench** ornate iron; sparkles. | Callback S001. |
| **S060** | `present` | WS low | B11 | Denken small vs tall façades. | |

---

### Page 013 — `013.jpg` — memory vs gold present

**Scan gutters:** **Black** tiers = flashback couple; **white** tiers = present Denken + party (matches reader “memory vs now” read).

| ID | Layer | Framing | Beat | What we see | Continuity |
|----|-------|---------|------|-------------|------------|
| **S061** | `fb_couple` | MS | B12 | Young couple on bench intimate. | Period dress. |
| **S062** | `fb_couple` | MS | B12 | Woman at roses; man BG. | |
| **S063** | `fb_couple` | WS | B12 | Couple walking busy timber-town street; briefcase. | |
| **S064** | `present` | CU | B12 | Elderly Denken — “nothing changed.” | Gold texture on world. |
| **S065** | `present` | WS | B12 | Denken from back; **Stark & Frieren** (Fern edge) on textured **El Dorado** ground. | Party scale vs him. |
| **S066** | `present` | Profile | B12 | Denken “memories remained.” | |
| **S067** | `present` | Profile detail | B12 | Continuation — swallowed years ago. | Monocle. |

---

### Page 014 — `014.jpg` — chapel approach

**Scan gutters:** **All black** on the page — use for **mood / sacred weight**; shots below are still **`present`** (Denken), not `fb_*`.

| ID | Layer | Framing | Beat | What we see | Continuity |
|----|-------|---------|------|-------------|------------|
| **S068** | `present` | MS high | B13 | Denken walks interior/antechamber toward camera; bright hall. | |
| **S069** | `present` | LS | B13 | Back to Denken approaching small **stone chapel** exterior. | |
| **S070** | `present` | WS low “hero” | B13 | **Cathedral interior:** huge columns, winged altar motif, steps, ethereal backlight. | Sacred climax BG. |

---

### Page 015 — `015.jpg` — wedding vs regret

**Scan gutters:** **Black** tiers = wedding flashback; **white** tiers = present Denken + Frieren.

| ID | Layer | Framing | Beat | What we see | Continuity |
|----|-------|---------|------|-------------|------------|
| **S071** | `fb_couple` | MCU | B14 | Young bride portrait flowers in hair smile. | Vertical line texture = memory. |
| **S072** | `fb_couple` | MS | B14 | Wedding hall; couple facing hands joined. | |
| **S073** | `present` | CU | B14 | Denken — euphoric times / distress monologue. | |
| **S074** | `present` | MS | B14 | Denken outdoors; **Frieren** back of head FG; **thick travel scarf** on Frieren. | Bridges to **S075** (same present + scarf). |

---

### Page 016 — `016.jpg` — present bridge + hero-party flashback

**Scan gutters:** **White** upper = **`present`**; **black** lower = **`fb_hero`**. **Frieren:** thick **travel scarf** in **S075** only; **S076–S078** = young flashback, **no** scarf.

| ID | Layer | Framing | Beat | What we see | Continuity |
|----|-------|---------|------|-------------|------------|
| **S075** | `present` | MS | B15 | **Denken** (back to camera) + **adult Frieren**; **snow foreground**, **mountains with rock through snow**, grey sky; **scarf** — **S074**. Ref [`panels/panel_s075.png`](../../panels/panel_s075.png). | Ch81 outdoor highlands; not **S076** meadow. |
| **S076** | `fb_hero` | WS | B15 | Full **Hero party** in **flower field**; petals; **Himmel** mid. | Young Frieren **scarfless** vs **S075**. Ref [`panels/panel_s076.png`](../../panels/panel_s076.png) (`016.jpg` wide tier). |
| **S077** | `fb_hero` | MS back | B15 | Frieren from behind; petals; spell / Flamme emotion. | Flashback wardrobe. |
| **S078** | `fb_hero` | CU | B15 | **Himmel** gentle smile — surprised at her expression. | |

---

### Page 017 — `017.jpg` — Himmel / Flamme / memory thesis

| ID | Layer | Framing | Beat | What we see | Continuity |
|----|-------|---------|------|-------------|------------|
| **S079** | `fb_hero` | MCU | B16 | Frieren thoughtful. | |
| **S080** | `fb_hero` | MS | B16 | Vertical-line **flashback:** **Flamme** + young Frieren walk wooded path. | |
| **S081** | `fb_hero` | WS | B16 | Frieren & Himmel in tall grass/flowers; dialogue. | |
| **S082** | `fb_hero` | MS scenery | B16 | Trees/grass emphasis; Himmel’s lines about painful journey. | Can animate as slow pan. |
| **S083** | `fb_hero` | CU | B16 | Himmel downcast serious. | |
| **S084** | `fb_hero` | MS | B16 | Frieren looks up — “all right to remember.” | |
| **S085** | `fb_hero` | Large CU profile | B16 | Himmel soft smile; **petals** foreground motion cue. | |

---

### Page 018 — `018.jpg` — back to present; alliance

| ID | Layer | Framing | Beat | What we see | Continuity |
|----|-------|---------|------|-------------|------------|
| **S086** | `present` | MCU | B17 | Frieren by fence downward — transition from memory. | |
| **S087** | `fb_hero` | CU | B17 | **Himmel** sparkles: “It is all right to remember, Frieren.” | |
| **S088** | `present` | WS | B17 | Field: **Denken** apart; Stark, Fern, Frieren; apology / fight alone. | |
| **S089** | `present` | CU | B17 | Frieren slight smile — will help secure chance of victory. | |
| **S090** | `present` | MCU | B17 | Denken resolved; BG trio toward **wood shack**. | |
| **S091** | `present` | Split ECU / MS | B17 | Denken eye **monocle** \| Frieren (+ Fern) — “Very well. We will help.” | Chapter close. |

---

## Stage 3 handoff (next)

- [x] Collapse `Layer` into **Fal prefix variants** (`PREFIX_PRESENT`, `PREFIX_FB_*`). → [stage_03_series_bible.md](./stage_03_series_bible.md) §2  
- [x] Write **series bible** bullets: Frieren / Fern / Stark / Denken / Himmel / Macht + negatives / no gutters. → [stage_03_series_bible.md](./stage_03_series_bible.md) §§1–3  
- [x] Batch prompts for first test (S010, S015, S036, S070, S076, S082, S085, S091). → [stage_03_series_bible.md](./stage_03_series_bible.md) §5

---

*Stage 2 complete — 91 shots tagged for continuity and beats.*
