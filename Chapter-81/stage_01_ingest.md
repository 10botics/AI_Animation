# Stage 1 — Ingest: Frieren Chapter 81 (“El Dorado”)

**Source folder:** `Frierien-chapter081` (note: folder name uses “Frierien”; series title is *Frieren*).  
**Generated:** 2026-03-25 (one pass, for Fal anime pipeline prep).  
**Re-ingest / RTL audit:** 2026-03-26 — `002.jpg`–`004.jpg` corrected in [stage_02_shot_list.md](./stage_02_shot_list.md). **Full sweep 2026-03-25:** `005.jpg`–`018.jpg` **not** yet re-sequenced row-by-row against balloons; see **§5.1** — row order may still follow early LTR listing in places. Do not reorder shots blindly without bubble order on the scan.

---

## 1. Page inventory and order

| Reading order | File      | Role |
|---------------|-----------|------|
| 1 | `001.jpg` | Chapter title splash / cold open (bench, elderly mage figure) — anime grade may **foreshadow El Dorado gold** (chapter arc); see **S001** in Stage 2 for Fal palette note |
| 2 | `002.jpg` | Campsite: letter, Lernen request, party reactions |
| 3 | `003.jpg` | Deal + journey; **golden Weise** reveal; Macht / history |
| 4 | `004.jpg` | Great barrier; **Denken** as warden; forest meet |
| 5 | `005.jpg` | Overlook: city, Denken backstory (Glück / mansion) |
| 6 | `006.jpg` | Barrier rules; El Dorado expansion; Frieren’s no-help warning |
| 7 | `007.jpg` | Refuse job; **defeated by Macht**; defeat flashback |
| 8 | `008.jpg` | Cliff line: seal Macht; “eleven losses”; no confidence to win |
| 9 | `009.jpg` | Denken’s cold pragmatism; never visited wife’s grave |
| 10 | `010.jpg` | Denken flashback: archive / “I will one day return” |
| 11 | `011.jpg` | Monologue: hometown swallowed; warden motives |
| 12 | `012.jpg` | Return walk; town unchanged; bench beat |
| 13 | `013.jpg` | Young-couple flashback vs present; El Dorado texture — **gutters: black = FB couple tiers, white = present Denken** |
| 14 | `014.jpg` | Approach chapel → **cathedral / altar** (large holy interior) — **gutters: all black on scan, story = present** (solemn / sacred mood, not flashback) |
| 15 | `015.jpg` | Wedding flashback vs present regret; Frieren nearby — **gutters: black = wedding FB, white = present** |
| 16 | `016.jpg` | **Split:** **present** top tier — Denken + **scarf** Frieren (bridge from `015.jpg`); **black-gutter** tiers — **hero-party flashback** (young Frieren **no scarf**, Himmel, Flamme thread) |
| 17 | `017.jpg` | Frieren–Himmel on memory being “all right”; Flamme flashback |
| 18 | `018.jpg` | Present: Himmel echo; Denken apology; **Frieren agrees to help** |

**Sort key:** zero-padded `NNN.jpg` — Windows lexical sort matches **chapter page** order for this pack (first story page → last).  
**Span:** single chapter, **18 pages**, no missing indices in-folder.

### Manga panel read path (within each page) — not Western LTR

The table above is **only the order of full page files**, not how panels are read **inside** each `NNN.jpg`.

- **Japanese manga layout** is read **right → left** within each row or “strip,” and **top → bottom** down the page (standard snaking path for irregular grids). **Do not** sequence panels by **left → right** as in American comics.
- **English-localized scans** usually keep the **same panel geometry**; **speech-bubble read order** should match the **original** panel order. Use **balloon order** (1→2→3…) or official typesetting when you need to **verify** ambiguous grids.
- **Pipeline risk:** If shots were listed or cropped by **geometric LTR** without a manga read-path pass, **story order can be wrong**. Cross-check against raw Japanese pages, numbered balloons, or story sense before locking edits and animation.

Stage 2 spells out how shot IDs map to that read path — [stage_02_shot_list.md](./stage_02_shot_list.md).

### Gutter color as reader cue (013–016)

On these English-scan pages the **artist uses white vs black outside the panel borders** (gutters) to steer **how a beat is felt**, not always “which year it is.”

| Idea | Where it shows up |
|------|-------------------|
| **Black gutters = memory block** vs **white = present block** | **`013.jpg`**, **`015.jpg`** — top/black tiers are young-couple flashback; bottom/white is elderly Denken + now. |
| **Black gutters = mood / sacred present** | **`014.jpg`** — entire page is black-guttered, but the action is **Denken walking into the chapel story-now**; treat as **weight and ritual**, not automatic flashback. |
| **016.jpg — present vs flashback on one page** | **White gutters** = **present** (**Denken** + adult **Frieren**, **travel scarf** — matches **`015.jpg`** bottom). **Black gutters** = **hero-party flashback** (young **Frieren** without scarf, **Himmel**). |

**Pipeline rule:** Tag shots by **narrative layer** (`present` / `fb_*`) from dialogue and storyboard — [stage_02_shot_list.md](./stage_02_shot_list.md) — **do not** infer timeline from gutter color alone.

---

## 2. Chapter boundaries

- **Starts:** `001.jpg` (title page “Chapter 81 — El Dorado”).  
- **Ends:** `018.jpg` (Frieren commits to assisting Denken).  
- **No next-chapter pages** in this folder (assumed complete for ch.81).

---

## 3. Story beats (for Stage 2 shot list)

Beats are **narrative hinges** (good for cuts, music, and Fal batches). Panel-level work happens in Stage 2.

| Beat ID | After page | What shifts |
|---------|------------|-------------|
| B1 | 001 | Tone: solitary, symbolic opener → story proper |
| B2 | 002 | **Quest hook:** unofficial letter, unease vs obligation |
| B3 | 003 | **Escalation:** grimoire; **first full reveal of golden Weise** + Macht lore |
| B4 | 004 | **New cast + place:** Denken; **great barrier** megashot |
| B5 | 005 | Personal stake: family / mansion / irony of the view |
| B6 | 006 | **Conflict rule:** barrier politics; Frieren draws line on fighting Macht |
| B7 | 007 | **Reversal:** refuse commission; **Macht trauma** + defeat flashback |
| B8 | 008 | Strategic stance: containment vs victory; fear of Macht |
| B9 | 009 | Denken’s moral shading; grief / avoidance |
| B10 | 011 | Motive crystallized: return after loss, not heroism |
| B11 | 012 | **Uncanny return:** town “unchanged”; bench motif |
| B12 | 013 | Memory vs gold reality; couple flashback glue |
| B13 | 014 | **Scale / sacred:** chapel → cathedral interior |
| B14 | 015 | Emotional peak: wedding vs “what have I been doing?” |
| B15 | 016 | **Bridge + memory:** present Denken/Frieren at field (**scarf**) → hero-party flashback flower field (**no** scarf) |
| B16 | 017 | Thesis beat: “okay to remember” (Himmel / Frieren) |
| B17 | 18 | **Resolution:** alliance; Frieren helps Denken |

---

## 4. Continuity / casting notes (quick, for later bible)

Recurring in this chapter:

- **Party:** Frieren, Fern, Stark (travel clothes; forest / cliff / village).
- **Denken:** elderly, long beard, **monocle**, dark robes — barrier warden.
- **Antagonist lore:** Macht of El Dorado; Seven Sages; golden transmutation ~50 years ago.
- **Locations:** Northern Plateau / Weise region → forest camp → ridge **golden city** → barrier vista → overlook → village / **half-timber town** → **church interior** → present fields + **flashbacks** (hero party flower field; younger Frieren / Himmel / Flamme).
- **Time layers:** heavy use of **flashback vs present** — Stage 2 should tag each panel with `present | flashback_denken | flashback_hero_party`.
- **Gutters (013–016):** black/white page surround is a **composition/emotion** cue — see **Gutter color as reader cue** above; align Fal crops/refs with **shot layer**, not gutter color.

---

## 5. Debugging log (this run)

### 5.1 Full ingest sweep — gaps vs `manga-chapter-ingest-stages-1-3` (2026-03-25)

| Gap | Severity | Action |
|-----|----------|--------|
| **RTL / row order** on `005.jpg`–`018.jpg` | High | Only `002`–`004` have explicit RTL fix notes. **Remaining pages:** confirm each multi-panel tier with **speech-bubble read order** on the JPGs; then, if needed, **reorder rows** in Stage 2 (shot **IDs** stay fixed — only Markdown table order changes). Do **not** infer order from “panel top left / top right” in auto descriptions alone. |
| **`Characters (on-screen \| vicinity)`** per shot | Medium | Stage 2 encodes cast mainly in **What we see** / **Continuity**, not as mandatory split fields on **all 91 rows**. Add two columns or **On-screen / Vicinity** sub-bullets when touching a page. |
| **`panels/panel_s*.png` refs** | Medium | In-repo crops today: **S001** (full `001.jpg` splash), **S002–S006, S010, S075, S076** (plus `panel_s003old.png`). Other bible shots lack named panel files — add crops as refs lock. |
| **Antagonist naming on `010.jpg`** | Low | Bottom flashback tier: seated ruler = **Macht** (human-form); Stage 2 **S050** says “seated figure” — align wording with **S036** for continuity. |
| **Flashback extras** | Low | **S048** archive / **S050** court / **S063** street: crowds, guards, scholars **unnamed** — optional “extras” line per shot for blocking. |
| **`017.jpg` grid** | Low | Irregular 7-shot layout — verify **S083–S085** tier order against scan if dialogue ever feels out of sequence. |

### 5.2 Legacy notes

| Issue | Severity | Notes |
|--------|----------|------|
| Folder spelling `Frierien` vs `Frieren` | Low | Cosmetic; scripts or docs should use one spelling on purpose. |
| `002.jpg` at repo root `AI_Animation\002.jpg` | Low | Same size as `Frierien-chapter081\002.jpg` (236606 bytes) — likely duplicate; source of truth should be the chapter folder only. |
| Vision via tool = image descriptions | Info | Descriptions can confuse **Glück** (feudal house) with who is on screen; trust bubbles + Stage 2. |
| Scan credits / overlay text | Medium for Fal | Some pages have translator credits in gutters — prompt negatives or crop in Stage 4. |

---

## 6. Stage 2 handoff checklist

- [x] Build numbered **shot list** from beats B1–B17 (multi-panel pages → multiple shots). → see `stage_02_shot_list.md`  
- [x] Tag each planned shot: `present` / `flashback` + location + characters.  
- [x] Pull **series bible** (style lock + Denken / party anchors) for Fal prefix blocks — see [stage_03_series_bible.md](./stage_03_series_bible.md)

---

*End of Stage 1 — one attempt, full chapter ingested.*
