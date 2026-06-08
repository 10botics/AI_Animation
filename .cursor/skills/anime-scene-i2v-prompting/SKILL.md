---
name: anime-scene-i2v-prompting
description: >-
  Builds Kling / Seedance / Fal image-to-video motion prompts from AI_Animation chapter
  stage files (ingest, shot list, series bible, optional Stage 4 QC logs). Includes Seedance
  native audio/SFX and content-policy-safe wording (no copyrighted names, no age terms, production
  framing) to avoid Fal partner_validation_failed on generated_video. Use for “prompt for S0xx”
  / “motion from shot list” / Seedance I2V runs.
---

# Anime scene → I2V motion prompt (AI_Animation)

## 1. Always read first

| Resource | Role |
|----------|------|
| [`docs/stage5-image-to-video-fal.md`](../../../docs/stage5-image-to-video-fal.md) | **Video reference** — Kling + **Seedance 2.0** model IDs, API fields, motion rules |
| [`.cursor/skills/fal-image-to-video-prompting/SKILL.md`](../fal-image-to-video-prompting/SKILL.md) | Fal checklist, Kling `negative_prompt`, Kling audio cost, research links |
| [`docs/sfx-models-fal.md`](../../../docs/sfx-models-fal.md) | **Post-I2V** SFX (ThinkSound, Kling v2a, Mirelo) when Seedance/Kling native audio is not enough |
| [Fal `content_policy_violation`](https://docs.fal.ai/errors#content_policy_violation) | Official error type; Seedance often flags **`generated_video`** after generation completes |

This skill is **scene assembly**: gather **what the shot is** from repo files, then output a **short motion-first** `prompt` (+ suggested API args). It does **not** replace the handbook for endpoint details.

**Seedance API prompts are not Stage 4 prompts:** Never paste `*_PROMPT_FLUX` (names, “petite”, backstory) into I2V. Use **§4b** safe wording for every `bytedance/seedance-2.0/*` call.

---

## 2. Resolve the chapter and shot

- **Chapter root (default):** [`Chapter-81/`](../../../Chapter-81/) — adjust if the user names another chapter folder (e.g. legacy `Frierien-chapter081/`).
- **Shot ID:** Normalize to **`S0xx`** (e.g. `S010`, `s10` → `S010`).

---

## 3. Gather scene truth (read in this order)

Use the shot ID to find rows and beats. Do **not** invent wardrobe, props, layer, or who is on screen.

| Order | File | Extract for the prompt |
|-------|------|-------------------------|
| 1 | [`stage_01_ingest.md`](../../../Chapter-81/stage_01_ingest.md) | Beat(s), page/tier, **timeline** (present vs flashback), gutter context — motion must not contradict **which world** the shot belongs to. |
| 2 | [`stage_02_shot_list.md`](../../../Chapter-81/stage_02_shot_list.md) | **`Layer`**, framing (WS/MS/CU), **“What we see”**, props (scarf, axe, petals, snow, **backs to camera**, etc.). |
| 3 | [`stage_03_series_bible.md`](../../../Chapter-81/stage_03_series_bible.md) | **PREFIX** / mood for that **Layer** (e.g. `present` = cool Northern; `fb_hero` = petals, warm memory). Global **negatives** to mirror in Kling `negative_prompt` only. |
| 4 | **Stage 4 still** | Path or URL of the **Final** PNG that drives I2V — only anchor for composition; if unknown, ask or search `Tests/` / `Tests/Final/` for the shot. |
| 5 | **Optional** `stage_04_s0xx_visual_qc_log.md` | If present under [`Chapter-81/`](../../../Chapter-81/), use approved **look** notes and **drift warnings** — avoid prompt clauses that previously caused morphing or layout breaks. |

**Image prompts are not video prompts:** Use [`scripts/fal_common.py`](../../../scripts/fal_common.py) `*_PROMPT_FLUX` only as **fact-check** (who, what, where). Do **not** paste the full Flux block into I2V `prompt`.

---

## 4. Build the motion prompt (template)

Compose **one** tight English paragraph (or two short sentences max). **For Seedance**, follow **§4b** first (production framing, role labels, plain text).

1. **Anchor (Seedance):** `Fantasy anime television production shot, PG adventure storyboard, cinematic` + **same layout as the reference still** — then layer motion. **Do not** open with bare keywords or shot IDs alone (`storyboard S004` without production context is weak context for the filter).
2. **From stage_02:** Primary **subject motion** (hair, cloth, petals, snow, glints) — **props and roles**, not copyrighted names in API text (see §4b).
3. **Environment:** Wind, particles, light shimmer — match **Layer** mood from stage_03.
4. **Camera:** Prefer **locked** or **very slow** dolly/drift; no whip zoom unless the shot list demands energy and drift is acceptable.
5. **Guardrails:** No new characters, no 180° turns unless already implied, no cuts inside the clip, no manga/halftone (Kling: echo in `negative_prompt`; Seedance: state in `prompt` — no `negative_prompt` field). **Seedance:** no romance, contact, violence, or age-coded characters in the prompt string.

**Cue mapping (examples, not exhaustive):**

| stage_02 signal | Typical motion vocabulary |
|-----------------|---------------------------|
| `present` + exterior | Crisp air, cool light, slow snow or dust |
| `fb_hero` | Warm haze, floating petals, soft bokeh drift |
| WS landscape | Subtle parallax, distant shimmer, almost-static camera |
| CU face | Micro-expression, eye movement, **minimal** camera — **higher policy risk** on Seedance; prefer locked camera, still gaze |

---

## 4b. Seedance — content policy (`Output video has sensitive content`)

### Two different failures (do not conflate)

| `loc` | Meaning | Prompt rewrite helps? |
|-------|---------|------------------------|
| `["body", "prompt"]` or upload rejected early | Input blocked before/during queue | **Yes** — rephrase prompt; fix reference image (photoreal faces, named IP in **text**) |
| `["body", "generated_video"]` | Video **rendered**, then ByteDance **post-filter** rejected output (`partner_validation_failed`) | **Maybe** — often **motion + still composition**; same §4b text can fail repeatedly (see **S004**) |

Fal docs: [content_policy_violation](https://docs.fal.ai/errors#content_policy_violation) — includes **third-party IP** on generated media, not only NSFW.

External Seedance guides (Morphic, Apidog, Segmind): filter reads the **whole scene as one creative brief**; **visual facts + film production vocabulary** pass more often than motion notes or story subtext. **Named copyrighted characters** and **real identifiable faces** are hard blocks; **illustrated** uploads usually pass **input**, but **animated output** can still be flagged as IP or “sensitive” frames.

### Repo evidence (what actually happened)

| Shot | Framing | Names in Seedance prompt? | §4b-style prompt? | Result |
|------|---------|---------------------------|-------------------|--------|
| **S002** | WS, Fern back to camera | **Yes** (Stark, Frieren, Fern) | Partial | **Pass** + audio |
| **S003** | MCU, one face + animal | **Yes** (Fern) | Plain text | **Pass** (`full` still); **Fail** (`extendcampsquirrel` still) |
| **S004** | **MS, two faces** (profile + depth) | Removed → role labels only | **Yes** (production opener, no lean/mouth) | **Fail** ×3+ same `generated_video` error |

**Lesson for the skill:** Removing character names and adding §4b framing **did not fix S004**. Do **not** tell agents that name removal alone prevents this error. Primary levers are **shot routing**, **near-static motion**, **still choice**, then **Kling**.

### Shot routing — pick model before writing

| stage_02 framing | Seedance risk | Default for Chapter 81 |
|------------------|---------------|-------------------------|
| **WS** / backs to camera / tiny figures | Low | Seedance + §4a audio OK |
| **MCU** / single dominant face | Medium | Seedance; minimal face motion; plain text |
| **MS / two-shot, two visible faces** | **High** (S004) | **`generate_s###_kling_i2v.py` first**; Seedance only with **§4b near-static** prompt below |
| **CU** dialogue / lip-sync | High | Kling or Seedance reference-to-video + `audio_urls` |

If **`generated_video`** failed once on a shot/still combo, **do not** burn credits on repeated full-motion Seedance retries with wording tweaks only.

### How to write (guidelines ↔ skill)

ByteDance/Morphic-style rules **not optional** for Seedance:

1. **Visual facts only** — what the camera sees: location, wardrobe props, light, movement. **No** motivations, relationships, beat names (`B2`), or `storyboard S00x` without a **film** frame.
2. **Answer four questions** in the paragraph: **Where?** What does it look like? **What is the camera doing?** **Atmosphere?**
3. **Production register** — include **2–4** terms: `locked-off`, `35mm soft grain`, `2.39:1`, `shallow depth of field`, `overcast diffused light`, `motivated campfire glow`. “PG adventure production shot” alone is necessary but **not sufficient** if motion stays face-heavy.
4. **Plain ASCII** — no `**markdown**` in API strings (repo scripts).
5. **No age-coded words** in API text (`young`, `petite`, `child`, …) — never copy from `*_PROMPT_FLUX`.
6. **Prefer no copyrighted names** in API text (Frieren, Fern, …) — **best practice**, but S002 passed with names; still carries **IP risk on output** when the **still** is recognizable.
7. **Motion on faces** — for MS/CU, use **near-static** wording (below); avoid `lean`, `mouth movement`, `head turn toward`, `conversation` between two figures.

### Seedance prompt templates

**Standard (WS / gentle MCU):**

```
Fantasy anime television production shot, PG adventure, locked-off <framing>, 35mm soft grain, 2.39:1, cool Northern forest daylight, overcast diffused light, same layout as the reference still.
<Visual facts: who in depth, props, environment motion — hair, cloth, pages, leaves only.>
Tripod-locked, no zoom, one continuous beat, no cuts, no on-screen text, no manga texture, no fourth wall.
[Optional §4a audio tail]
```

**Near-static (MS two-face / after one `generated_video` fail):**

```
Fantasy anime television production shot, PG adventure, locked-off medium shot, 35mm soft grain, 2.39:1, cool Northern forest camp, overcast diffused light, same composition as the reference still.
Foreground figure with open illustrated book: only page edge flutter and hair/cloth drift in breeze, seated, no turn to camera, no mouth motion.
Background figure with sealed paper packet: nearly frozen, slight scarf movement only, stays in depth, no step forward, no interaction beat between figures.
Environmental wind in leaves only. No cuts, no text, no fourth wall.
[Optional §4a audio — try silent first if prior fail had audio]
```

**Still avoid in API text:** `**bold**`; age terms; isolated romantic/contact/violence verbs; animal vocalizations on close person+animal shots if flagged.

### Retry ladder (`generated_video` / S004-class)

1. **Route:** MS two-face → run **`generate_s###_kling_i2v.py`** (silent + post-SFX per [`docs/sfx-models-fal.md`](../../../docs/sfx-models-fal.md)).
2. **Near-static** Seedance prompt (template above); `generate_audio: false` first.
3. **`--duration` `"4"`**, **`--resolution` `480p`**, or **`--fast`** — same still, new draw.
4. **Alternate still** (another `Tests/S004_*.png`); avoid hero still that already failed twice.
5. **One** full-motion Seedance retry with §4a audio only after a silent near-static **pass**.
6. Log in **`stage_04_s0xx_visual_qc_log.md`**: still path, prompt variant, audio on/off, error `loc`.

---

## 4c. Kling 2.6 — TV-anime framerate (prompt + optional post)

**Kling has no `fps` API** ([`llms.txt`](https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video/llms.txt)). For **broadcast-anime cadence** (not silky I2V / mocap glide), steer in **`prompt`** + **`negative_prompt`**, then optionally downsample with ffmpeg.

**Repo-approved (S004 MS, 2026-05-27):** limited-animation wording in the motion prompt produced good on-screen timing; keep this pattern for MS/CU dialogue beats on Kling.

### Prompt vocabulary (include 4–6 of these)

| Steer toward | Steer away (also in `negative_prompt`) |
|--------------|----------------------------------------|
| `limited-animation timing`, `cel-shaded`, `broadcast anime television` | `mocap glide`, `video-game interpolation`, `hyperreal motion smear` |
| `short pose holds`, `discrete in-between beats`, `gentle staccato` | `smooth cg camera orbit`, `continuous 3d parallax tour`, `gimbal float` |
| `animation on twos`, `hand-drawn TV anime, not 3D` | `heavy volumetric god-ray sweep` |
| `almost locked 2D anime plate`, `layered painting` background | (for silent beats) `lip-sync mouth flapping` if you want no dialogue |

**Source template:** `generate_s009_kling_i2v.py` **`--experiment 4`** (`MOTION_PROMPT_EXP4_ANIME_SUBTLE`). **S004 implementation:** [`scripts/generate_s004_kling_i2v.py`](../../../scripts/generate_s004_kling_i2v.py) — **`--anime-limited`** default **on**; **`--no-anime-limited`** for cinematic Kling prose only.

### Optional ffmpeg post (`--anime-fps`)

| Flag | Default | Notes |
|------|---------|--------|
| `--anime-fps` | `12` | `ffmpeg` `fps=N` after download; use **`0`** to skip. **Preserves audio** when present (`-c:a aac`). |
| `--audio` | off | Native Kling audio; append §4a-style foley tail in script (`AUDIO_TAIL`). |

**Deliverable naming:** `S004_kling-v26-pro_i2v_anime-audio-12fps_<UTC>.mp4` (tags reflect flags).

**When to use:** MS/CU present beats where Kling defaults feel too **fluid/cinematic**; wide shots (S002/S010) can stay standard motion unless a test looks too 3D.

---

## 4a. Seedance 2.0 — native audio / SFX (when user wants sound in the clip)

**Preferred for new Chapter 81 clips** per [`docs/stage5-image-to-video-fal.md` §2a](../../../docs/stage5-image-to-video-fal.md).

| | |
|--|--|
| **Model ID** | `bytedance/seedance-2.0/image-to-video` (fast: `bytedance/seedance-2.0/fast/image-to-video`) |
| **Playground** | [Seedance 2.0 I2V](https://fal.ai/models/bytedance/seedance-2.0/image-to-video) |
| **Audio toggle** | **`generate_audio`** — boolean, Fal default **`true`**; repo scripts default **off** unless **`--audio`** |
| **Output** | **MP4 with embedded audio track** (SFX + ambience + optional lip-sync) — **not** a separate WAV from I2V |
| **Cost** | Fal documents **same price** with audio on or off |
| **No** | Dedicated `sound_effect_prompt` on I2V — steer foley in the **same** `prompt` string |

**Repo scripts:** `scripts/generate_s###_seedance_i2v.py` — pass **`--audio`** to set `generate_audio: true`.

### Audio lines in the motion prompt (append when `generate_audio: true`)

Add a **short audio clause** at the end of the motion paragraph (still one block — Seedance has no separate SFX field):

| Scene need | Example prompt tail |
|------------|---------------------|
| Camp / forest (S002-style) | `Ambient forest day: soft wind in trees, campfire crackle and thin smoke, cloth rustle; no speech, no dialogue, no singing, no music score.` |
| Quiet present beat | `Subtle environmental foley only; no dialogue; no one speaks.` |
| Action / impact | `Short impact foley synced to motion; no voiceover.` |
| Memory / `fb_hero` | `Soft nostalgic ambience, distant wind, gentle fabric; no modern UI sounds.` |
| **Avoid** | Random dialogue, narrator, pop music, crowd walla unless stage_02 shows a crowd |

**Chapter default:** Most Frieren ch.81 beats are **silent storyboard** until dialogue is explicitly staged — prefer **foley + ambience, no speech** unless the user asks for lip-sync.

### Seedance vs post-pass SFX

| Approach | When |
|----------|------|
| **`generate_audio: true`** on Seedance I2V | One-shot sync SFX/ambience with picture; good first pass; control via prompt words only |
| **Silent Seedance** (`generate_audio: false` or omit `--audio`) + [`docs/sfx-models-fal.md`](../../../docs/sfx-models-fal.md) | Precise or repeatable foley (ThinkSound, Kling `video-to-audio`, Mirelo, Beatoven) |

**Reference-to-video (optional):** `bytedance/seedance-2.0/reference-to-video` accepts **`audio_urls`** + `@Audio1` in prompt for lip-sync or soundtrack reference — only when the user needs driven speech/music, not typical camp/wide shots.

---

## 5. Output format (deliver every time)

Return this block so humans can paste into Fal or scripts. Include **both** model blocks when the target model is unclear; otherwise emit only the block that matches the user’s request.

```markdown
## I2V handoff — <S0xx>
- **Beat / timeline:** (from stage_01)
- **Layer / framing:** (from stage_02)
- **Mood (PREFIX):** (from stage_03)
- **Driver still:** `<path or upload target>`

### Motion prompt (`prompt`) — shared
> …

### Kling 2.6 Pro (silent default)
- **Model:** `fal-ai/kling-video/v2.6/pro/image-to-video`
- **Suggested args:** `duration` `"5"`, `generate_audio` `false`, `start_image_url` = uploaded Final
- **Anime timing:** §4c limited-animation prompt + anti–3D-glide `negative_prompt`; optional `--anime-fps 12` on `generate_s004_kling_i2v.py` (and S009 exp4 pattern)
- **negative_prompt:** extend per fal-image-to-video-prompting §3 + bible drift terms

### Seedance 2.0 (preferred for new clips)
- **Model:** `bytedance/seedance-2.0/image-to-video` (or `…/fast/image-to-video`)
- **Suggested args:** `image_url` = uploaded Final, `duration` `"5"` (or `"auto"`), `resolution` `720p`, `aspect_ratio` `16:9` when known
- **Audio:** `generate_audio` `true` **only if** user asked for native SFX/ambience — then **include audio clause in `prompt`** (§4a); else `false` / omit `--audio` on `generate_s###_seedance_i2v.py`
- **negative_prompt:** N/A — fold drift guardrails into `prompt` text
- **Script:** `python generate_s<shot>_seedance_i2v.py` … `--audio` when audio on
- **Deliverable:** MP4 under `outputs/video/` with muxed audio when `generate_audio` is true
```

Then run the **verification checklist** in [`fal-image-to-video-prompting` §5](../fal-image-to-video-prompting/SKILL.md).

**Seedance extra checks (§4b):**

- [ ] Checked **shot routing** table — MS two-face → Kling first unless near-static Seedance already passed once.
- [ ] Prompt is **visual facts + camera + light** (four questions); no beat IDs alone, no Flux paste, no story subtext.
- [ ] Includes **2+ production terms** (35mm, locked-off, 2.39:1, diffused light, etc.).
- [ ] **Plain text** only; no age-coded words; **avoid** copyrighted names (not sufficient alone to prevent `generated_video` fail).
- [ ] MS/CU: **near-static** face motion unless user explicitly needs performance.
- [ ] After any `generated_video` fail on this still: handoff says **Kling path** + silent near-static Seedance optional; do not promise “rename characters = fixed.”

---

## 6. Related paths

| Path | Role |
|------|------|
| [`manga-to-anime-fal-stages.plan.md`](../../../manga-to-anime-fal-stages.plan.md) | Full pipeline |
| [`docs/flux-2-pro-prompting-guide.md`](../../../docs/flux-2-pro-prompting-guide.md) | Stage 4 stills |
| [`docs/stage5-image-to-video-fal.md`](../../../docs/stage5-image-to-video-fal.md) | Seedance + Kling handbook |
