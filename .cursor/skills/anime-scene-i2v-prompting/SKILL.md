---
name: anime-scene-i2v-prompting
description: >-
  Builds Kling / Fal image-to-video motion prompts from AI_Animation chapter stage files
  (ingest, shot list, series bible, optional Stage 4 QC logs and approved still paths).
  Use when the user asks for I2V or video motion prompts from scene or shot context,
  wants prompts grounded in stage markdown, or says “prompt for S0xx” / “motion from shot list.”
---

# Anime scene → I2V motion prompt (AI_Animation)

## 1. Always read first

| Resource | Role |
|----------|------|
| [`docs/stage5-image-to-video-fal.md`](../../../docs/stage5-image-to-video-fal.md) | **Video reference** — model ID, API fields, motion rules, examples |
| [`.cursor/skills/fal-image-to-video-prompting/SKILL.md`](../fal-image-to-video-prompting/SKILL.md) | Fal checklist, `negative_prompt`, audio cost, research links |

This skill is **scene assembly**: gather **what the shot is** from repo files, then output a **short motion-first** `prompt` (+ suggested API args). It does **not** replace the handbook for endpoint details.

---

## 2. Resolve the chapter and shot

- **Chapter root (default):** [`Frierien-chapter081/`](../../../Frierien-chapter081/) — adjust if the user names another `Frierien-chapter*` folder.
- **Shot ID:** Normalize to **`S0xx`** (e.g. `S010`, `s10` → `S010`).

---

## 3. Gather scene truth (read in this order)

Use the shot ID to find rows and beats. Do **not** invent wardrobe, props, layer, or who is on screen.

| Order | File | Extract for the prompt |
|-------|------|-------------------------|
| 1 | [`stage_01_ingest.md`](../../../Frierien-chapter081/stage_01_ingest.md) | Beat(s), page/tier, **timeline** (present vs flashback), gutter context — motion must not contradict **which world** the shot belongs to. |
| 2 | [`stage_02_shot_list.md`](../../../Frierien-chapter081/stage_02_shot_list.md) | **`Layer`**, framing (WS/MS/CU), **“What we see”**, props (scarf, axe, petals, snow, **backs to camera**, etc.). |
| 3 | [`stage_03_series_bible.md`](../../../Frierien-chapter081/stage_03_series_bible.md) | **PREFIX** / mood for that **Layer** (e.g. `present` = cool Northern; `fb_hero` = petals, warm memory). Global **negatives** to mirror in API `negative_prompt`. |
| 4 | **Stage 4 still** | Path or URL of the **Final** PNG that drives I2V — only anchor for composition; if unknown, ask or search `Tests/` / `Tests/Final/` for the shot. |
| 5 | **Optional** `stage_04_s0xx_visual_qc_log.md` | If present under [`Frierien-chapter081/`](../../../Frierien-chapter081/), use approved **look** notes and **drift warnings** — avoid prompt clauses that previously caused morphing or layout breaks. |

**Image prompts are not video prompts:** Use [`scripts/fal_common.py`](../../../scripts/fal_common.py) `*_PROMPT_FLUX` only as **fact-check** (who, what, where). Do **not** paste the full Flux block into Kling `prompt`.

---

## 4. Build the motion prompt (template)

Compose **one** tight English paragraph (or two short sentences max):

1. **Anchor:** Fantasy TV anime; **same composition / same characters** as the reference image.
2. **From stage_02:** Primary **subject motion** (hair, cloth, petals, snow, glints, breath) consistent with **who is in frame**.
3. **Environment:** Wind, particles, light shimmer — match **Layer** mood from stage_03.
4. **Camera:** Prefer **locked** or **very slow** dolly/drift; no whip zoom unless the shot list demands energy and drift is acceptable.
5. **Guardrails:** No new characters, no 180° turns unless already implied, no cuts inside the clip, no manga/halftone (echo in `negative_prompt`).

**Cue mapping (examples, not exhaustive):**

| stage_02 signal | Typical motion vocabulary |
|-----------------|---------------------------|
| `present` + exterior | Crisp air, cool light, slow snow or dust |
| `fb_hero` | Warm haze, floating petals, soft bokeh drift |
| WS landscape | Subtle parallax, distant shimmer, almost-static camera |
| CU face | Micro-expression, eye movement, **minimal** camera |

---

## 5. Output format (deliver every time)

Return this block so humans can paste into Fal or scripts:

```markdown
## I2V handoff — <S0xx>
- **Beat / timeline:** (from stage_01)
- **Layer / framing:** (from stage_02)
- **Mood (PREFIX):** (from stage_03)
- **Driver still:** `<path or upload target>`
- **Motion prompt (`prompt`):**
  > …
- **Suggested args:** `duration` `"5"`, `generate_audio` `False` unless user asked for native audio
- **negative_prompt:** extend per fal-image-to-video-prompting §3 + bible drift terms
```

Then run the **verification checklist** in [`fal-image-to-video-prompting` §5](../fal-image-to-video-prompting/SKILL.md).

---

## 6. Related paths

| Path | Role |
|------|------|
| [`manga-to-anime-fal-stages.plan.md`](../../../manga-to-anime-fal-stages.plan.md) | Full pipeline |
| [`docs/flux-2-pro-prompting-guide.md`](../../../docs/flux-2-pro-prompting-guide.md) | Stage 4 stills |
