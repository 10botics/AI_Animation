# Stage 4 — S010 visual QC: manga reference vs generated stills

**Shot:** **S010** (ridge overlook — Fortified City of Weise / El Dorado gold vista)  
**Default Fal ref:** [`panels/panel_s010.png`](../panels/panel_s010.png) (single-panel crop). **Page context:** [`003.jpg`](./003.jpg) — wide tier: three figures from behind on a ridge, valley and city covered in **gold screentone**.  
**Dual backend:** `generate_s010_ref_edit.py --model both` → Flux Pro + Nano Banana 2 (same `S010_EDIT_PROMPT`).  
**2026-03-26 panel ref (`094807Z`):** Flux [`Tests/S010_flux-2-pro-edit_20260326T094807Z.png`](../Tests/S010_flux-2-pro-edit_20260326T094807Z.png) · Nano [`Tests/S010_nano-banana-2-edit_20260326T094807Z.png`](../Tests/S010_nano-banana-2-edit_20260326T094807Z.png) · [`S010_ref_edit_summary_20260326T094807Z.json`](../outputs/fal/S010_ref_edit_summary_20260326T094807Z.json)  
**Generated files reviewed (legacy):**  
- [`Tests/S010_flux-2-flash_20260325T100456Z.png`](../Tests/S010_flux-2-flash_20260325T100456Z.png)  
- [`Tests/S010_flux-2-flex_20260325T100456Z.png`](../Tests/S010_flux-2-flex_20260325T100456Z.png)  

**Compare run:** same timestamp = **wiki-aligned wardrobe prompt** (post–cross-reference).  
**Clothes cross-check (second pass):** [Frieren fandom — Fern](https://frieren.fandom.com/wiki/Fern) (cold outfit), [Stark](https://frieren.fandom.com/wiki/Stark), local profile [`AI Anime/Characters/Frieren/profile_text_part1.md`](../../AI%20Anime/Characters/Frieren/profile_text_part1.md) (Frieren staff/clothing).

---

## 1. Manga ground truth (S010 panel intent)

| Dimension | Manga (`003.jpg` wide panel) |
|-----------|------------------------------|
| **Character count** | **Exactly three** — Frieren, Fern, Stark. No extra party member. |
| **Height order** | **Stark (tallest, broadest) > Fern (mid) > Frieren (shortest)**. Frieren is **clearly petite** vs humans — roughly to Fern’s **shoulder** zone, not equal height. |
| **Horizon / environment** | Valley, trees, and city read as **one continuous “golden” world** (screentone); distant **walled city on high ground**. |
| **Layout** | Extreme wide; figures **small** in frame; **backs to camera**; **viewer left→right: Fern | Frieren | Stark** on the reference ridge panel. |
| **Key props (this panel)** | **Frieren:** **large rectangular travel trunk / suitcase** in hand (panel-defining). **Stark:** **axe** on back with strap — not holding a mage staff. **Fern:** no staff in hands in the wide silhouette. |
| **S010-relevant wardrobe (ch.81 travel)** | **Frieren:** white coat/capelet, stripes at neck, dark leggings, boots, earrings. **Fern:** **dark blue dress**, **light gray cropped jacket**, **braided blue scarf**, **butterfly ornament on Fern only**. **Stark:** **red coat, cream lapels/cuffs**, crossbody strap, **double-bitted axe**, fingerless gloves, **quilted** jacket OK. |

---

## 2. Observed inconsistencies — Flux 2 Flex (`…100456Z.png`)

| # | Category | Issue | Severity |
|---|-----------|--------|----------|
| F1 | **Cast / count** | **Four** figures visible (extra **small “child elf”** with lavender hair). Manga S010 has **three** only. | **Critical** |
| F2 | **Identity** | Extra figure confuses **Frieren vs Fern** hierarchy (model may have split one archetype into two bodies). | **Critical** |
| F3 | **Environment** | Foreground/midground reads as **natural green forest + blue river**; city stone-colored. **Missing** dominant **gold landscape / gold city** read of the panel. | **Critical** (for S010) |
| F203 | **Scale** | Characters occupy a **large** portion of frame vs manga’s **tiny** silhouettes — less “epic wide” (subjective but noticeable). | Medium |
| F5 | **Stark** | Tallest present, red hair, axe — OK directionally; coat described with **heavy white fur** trim — anime uses **cream lapels/cuffs**; **fur** is a common model drift. | Low–medium |

**Clothes (Flex), element-by-element vs reference:**

| Character | Generated (Flex) | Cross-reference note |
|-----------|------------------|---------------------|
| Frieren-like | White tunic, striped collar, gold trim, blue leggings, boots, **staff with red orb** on back | Matches profile **except** must enforce **one** staff and **no duplicate child**. |
| “Child elf” | **Non-canonical** — remove via prompt/negative/count. | **Error** |
| Fern-like | Purple hair, butterfly ornament, **chunky light knit scarf**, gray cropped top, **long dark skirt** | **Scarf:** wiki = **braided blue scarf**, not necessarily chunky knit infinity scarf — allow “thick” but prefer **braided** wording. Jacket gray = OK (light gray winter jacket). |
| Stark | Red coat, **fur-like** white trim, cross straps, large axe | Prefer **cream lapels/cuffs** over **fur**; add **quilted** if we want manga jacket texture. |

---

## 3. Observed inconsistencies — Flux 2 Flash (`…100456Z.png`)

| # | Category | Issue | Severity |
|---|-----------|--------|----------|
| H1 | **Cast count** | **Three** figures — **matches manga**. | OK |
| H2 | **Height** | **Fern and Frieren nearly same height**; manga keeps **Fern clearly taller** than Frieren (Frieren petite). | **High** |
| H3 | **Staff** | **Two** staves crossed on Frieren’s back. Canon is **one** staff (gold frame, **large red orb**). | **High** |
| H4 | **Environment** | **Strong gold city / golden valley** — **aligned** with S010 VFX intent. | OK |
| H5 | **Stark** | Red jacket with **white fur** collar — again drift from **cream lapels/cuffs**; axe present — OK. | Low–medium |
| H6 | **Composition** | Characters **larger** in frame than manga panel; still acceptable for anime key art but **not** panel-faithful scale. | Medium |

**Clothes (Flash), element-by-element:**

| Character | Generated (Flash) | Cross-reference note |
|-----------|-------------------|---------------------|
| Frieren | White coat, gold hem detail, striped collar, leggings, boots | Good; **remove twin staves** → explicitly **single staff**. |
| Fern | Purple hair, butterfly clips, **thick blue scarf**, gray jacket, dark skirt | **Scarf:** prefer **braided blue scarf** (wiki cold outfit). |
| Stark | Red coat **fur trim**, straps, gloves, axe | **Cream** trim + optional **quilted** jacket closer to manga. |

---

## 4. Summary verdict

| Model | S010 panel fidelity (layout + gold + 3 bodies) | Wardrobe direction | Priority fixes |
|-------|-----------------------------------------------|--------------------|----------------|
| **Flux 2 Flash** | **Better** gold world; correct **3** people | Good trend; **height** + **one staff** | Explicit **height order**; **exactly three silhouettes**; **one staff only**; **cream** trim not fur |
| **Flux 2 Flex** | **Poor** for S010 — wrong **cast count**, weak **gold** | Mixed — extra character derails read | Same as above + strengthen **golden environment** clause; possibly **lower guidance** or different seed; consider **Kontext** with panel crop |

---

## 5. Prompt / pipeline actions (next iteration)

1. **Lock cast:** “**Exactly three people, no children, no extra characters** — only the elf mage, the purple-haired mage girl, and the red-haired warrior.”  
2. **Lock heights:** “**Height order strict:** tallest man, medium-tall purple-haired woman **clearly taller** than petite elf; elf reaches near woman’s **shoulder**.”  
3. **Lock staff:** “**One** wooden mage staff, gold fittings, **one** large red orb — never two staffs.”  
4. **Lock environment:** Re-assert **entire valley + forest + city turned to polished gold** (Flex regression).  
5. **Lock Stark jacket:** “**Red coat, cream-colored lapels and cuffs**” — add negative: “excessive fur trim, white fur collar” if fur persists.  
6. **Lock Fern scarf:** “**thick braided blue scarf**” (reduce “knit infinity scarf” drift).  
7. **Optional:** **img2img** [`fal-ai/flux-pro/kontext`](https://fal.ai/models/fal-ai/flux-pro/kontext) with a **crop of `003.jpg` S010 panel** to nail silhouette scale.

---

## 6. Wardrobe double-check table (authority: wiki + Frieren profile)

| Character | Element | Approved wording for next prompt |
|-----------|---------|-----------------------------------|
| **Frieren** | Hair | Silver-white, **low twin pigtails** |
| | Ears | Long horizontal **elf ears** |
| | Face cue | **Thick short brows**, teal-green eyes |
| | Top | **White** capelet + tunic, **gold** trim at collar/cuffs/hem, **black-white stripes** at neck |
| | Legs | **Dark navy** leggings, **brown** mid-calf boots |
| | Jewelry | **Red teardrop** earrings |
| | Weapon | **One** staff: wood, **gold** head, **large red orb** |
| **Fern** (Northern / cold) | Hair | Waist-length **purple**, hime sidelocks, **butterfly ornament** back of head |
| | Eyes | **Purple** |
| | Dress | **Dark blue** long dress |
| | Outer | **Cropped light gray** winter jacket |
| | Neck | **Braided blue scarf** (thick OK) |
| | Feet | **Black** boots |
| **Stark** | Hair | **Spiky red**, darker roots |
| | Eyes | **Orange** |
| | Coat | **Red** with **cream** lapels and cuffs (not fur-first); optional **quilted** body |
| | Hands | **Black fingerless** gloves |
| | Weapon | **Large double-bitted** axe, **crossbody strap** |

---

---

## 7. Round 3 — reference crop vs `102233Z` Flash / Flex (user compare)

**Reference:** S010 ridge panel — **3** figures, **backs**; **center** elf with **rectangular travel trunk**; **right** tallest with **diagonal strap + axe**; **left** long dark/purple hair (Fern). Heights **Stark > Fern > Frieren**.

| Issue | Flash / Flex generations (round 2) |
|--------|-----------------------------------|
| Cast | Flex run sometimes **5** bodies or duplicated archetypes; Flash sometimes **3** but order **Stark–Frieren–Fern** instead of **Fern–Frieren–Stark**. |
| Props | **Staff / axe swap** — Stark-like figure with **mage staff**; Frieren should show **suitcase** per panel, not staff-primary. |
| Hair jewelry | **Butterfly clips** applied to **elf** — canon: **Fern only**. |
| Coats | Over-ornate **gold embroidery** on multiple chars; **fur** instead of **cream** trim on Stark. |

**Prompt v3 change (implemented in `scripts/fal_common.py`):** explicit **left–center–right** placement; **suitcase for Frieren**, **no back staff** for this shot; **empty-handed Fern**, **axe-only on Stark**; **butterfly ornament Fern-only**; negatives for **5 people**, **two red-haired warriors**, **staff in Stark’s hands**.

---

## 8. Round 4 — image reference: Flux 2 **Pro** / **Flex** **edit** (`103440Z`)

**Goal:** Use the manga page as `image_urls[0]` and the same cast/environment constraints as text (`S010_PROMPT_FLUX` with an edit lead-in).

| Item | Detail |
|------|--------|
| **Script** | [`scripts/generate_s010_ref_edit.py`](../scripts/generate_s010_ref_edit.py) — `fal_client.upload_file` → **`fal-ai/flux-2-pro/edit`** + **`fal-ai/flux-2-flex/edit`**. |
| **Reference** | Full chapter page [`003.jpg`](./003.jpg) (contains multiple tiers; **single-panel crop** is preferable for tighter layout lock — pass `--ref path`). |
| **Pro output** | [`Tests/S010_flux-2-pro-edit_20260325T103440Z.png`](../Tests/S010_flux-2-pro-edit_20260325T103440Z.png) |
| **Flex output** | [`Tests/S010_flux-2-flex-edit_20260325T103440Z.png`](../Tests/S010_flux-2-flex-edit_20260325T103440Z.png) |
| **Logs / meta** | [`outputs/fal/S010_ref_edit_meta_20260325T103440Z.json`](../outputs/fal/S010_ref_edit_meta_20260325T103440Z.json), per-model JSON + [`S010_ref_edit_summary_20260325T103440Z.json`](../outputs/fal/S010_ref_edit_summary_20260325T103440Z.json) |

**Visual QC:** compare both PNGs against the S010 ridge crop for cast count, L→R order, suitcase vs axe, gold vista, and height separation — add bullet findings here after review.

---

*Log created for traceability of manga vs generation for S010. Update this file on each QC round.*
