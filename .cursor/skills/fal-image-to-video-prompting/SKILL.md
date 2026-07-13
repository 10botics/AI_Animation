---
name: fal-image-to-video-prompting
description: >-
  Builds Fal.ai image-to-video (I2V) prompts and API settings for Chapter 81+ anime clips
  from approved Stage 4 stills. Use when adding motion (Stage 5), choosing I2V models,
  or writing motion prompts for shots S002/S010/S075/S076/etc.
---

# Fal image-to-video prompting (AI_Animation)

## 1. Ground with Stages 1–3 (always)

Before writing **any** motion prompt, pull **truth** from the repo:

| Stage | File | What you use for video |
|-------|------|-------------------------|
| **1 — Ingest** | [`Frierien-chapter081/stage_01_ingest.md`](../../../Frierien-chapter081/stage_01_ingest.md) | Beat IDs (B1–B17), page→tier splits (e.g. `016.jpg` white = present **S075**, black = **S076+**), gutter/mood rules — **do not** contradict timeline. |
| **2 — Shot list** | [`Frierien-chapter081/stage_02_shot_list.md`](../../../Frierien-chapter081/stage_02_shot_list.md) | **`Layer`** (`present`, `fb_hero`, …), **framing** (WS/MS/CU), **“What we see”** — motion must match **who is in frame** and **props** (scarf, axe, petals, snow). |
| **3 — Bible** | [`Frierien-chapter081/stage_03_series_bible.md`](../../../Frierien-chapter081/stage_03_series_bible.md) | **Style:** fantasy TV anime, cel shading, painterly BGs. **PREFIX** layer mood (present = cool Northern light; `fb_hero` = petals, warm memory). **Negatives** (no halftone, no bubbles) — echo in I2V `negative_prompt` where the API supports it. |

**Stage 4 input:** one **hero still** per shot (e.g. under `Tests/` or `Tests/Final/`) — the **only** composition anchor. I2V must **not** be asked to redraw layout, add characters, or swap left-right.

**Canonical human doc:** [`docs/stage5-image-to-video-fal.md`](../../../docs/stage5-image-to-video-fal.md) — handbook form for day-to-day reference.

Recipe overview: [`manga-to-anime-fal-stages.plan.md`](../../../manga-to-anime-fal-stages.plan.md) § Stage 5.

---

## 2. Recommended Fal model (feasibility)

**Primary:** [`fal-ai/kling-video/v2.6/pro/image-to-video`](https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video)

| Criterion | Why Kling 2.6 Pro I2V |
|-----------|------------------------|
| **Same platform** | Uses **`FAL_KEY`** and `fal_client.subscribe` like existing `generate_*_ref_edit.py` scripts. |
| **Single start frame** | **`start_image_url`** (+ optional **`end_image_url`**) — fits “best Final PNG → short clip” workflow. |
| **Duration** | **`"5"`** or **`"10"`** seconds — good for tests; start with **5**. |
| **Prompt shape** | Natural-language **motion + atmosphere** (similar to how you already describe scenes in image prompts). |
| **Cost control** | With **`generate_audio`: `false`**, pricing is **~$0.07/s** vs **~$0.14/s** with native audio ([model `llms.txt`](https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video/llms.txt)). For silent cuts / external BGM, **prefer `generate_audio: false`**. |
| **Quality** | Strong **cinematic motion**; widely used on Fal for I2V. |

**Alternatives (when to consider):**

| Model | Endpoint | Notes |
|-------|-----------|--------|
| **Kling 2.1 Pro I2V** | `fal-ai/kling-video/v2.1/pro/image-to-video` | Uses **`image_url`** (not `start_image_url`); simpler older API — [docs](https://fal.ai/models/fal-ai/kling-video/v2.1/pro/image-to-video/api). |
| **Kling O3** | `fal-ai/kling-video/o3/standard/image-to-video` | **Start + end frame** interpolation — use if you have two keyframes. |
| **LTX-2 19B** | `fal-ai/ltx-2-19b/image-to-video` | Video **with audio** generation — heavier; good when you want built-in ambience/music later. |
| **Veo 3.1** | `fal-ai/veo3.1/reference-to-video` | Google stack; check schema for reference image count and use case. |

For **this** chapter pipeline, **default to Kling 2.6 Pro I2V** until a shot proves it wrong.

### 2.1 Research — what Fal **officially** documents (Kling 2.6 Pro I2V)

Treat the **live API + `llms.txt`** as the source of truth for parameter names and defaults:

- **Endpoint:** [`fal-ai/kling-video/v2.6/pro/image-to-video`](https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video) — full schema: [API](https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video/api), machine-readable summary: [`llms.txt`](https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video/llms.txt).

**Documented input behavior (maps to our needs):**

| Topic | Guideline |
|--------|-----------|
| **Start frame** | **`start_image_url`** must be a **reachable URL** (upload via `fal_client.upload_file` is the usual path — same pattern as Stage 4 edits). |
| **Motion vs redraw** | The model is **image-conditioned**: the prompt drives **how the still evolves through time**, not a full text-only reshoot. Keep instructions **consistent with what is already in the frame** (see §2.2). |
| **Duration** | **`"5"`** or **`"10"`** seconds only — plan motion that **finishes inside one beat**, not a multi-plot sequence ([`llms.txt`](https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video/llms.txt)). |
| **Negative quality** | Default **`negative_prompt`** is quality-focused; **extend** it for manga/anime pipeline drift (halftone, bubbles, extra limbs) — API supports it. |
| **Audio off (default pipeline)** | Set **`generate_audio`: `false`** for **silent** anime assembly + external BGM; halves per-second cost vs audio on ([`llms.txt` pricing](https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video/llms.txt)). |
| **Audio / dialogue on** | When **`generate_audio`: `true`**, examples use **natural speech in quotes** inside **`prompt`**. English: **lowercase** for normal words; **uppercase** for acronyms/proper nouns per [`llms.txt`](https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video/llms.txt). |
| **Voices** | Optional **`voice_ids`**; reference in prompt with **`<< >>`** (max 2 voices) — see [create-voice](https://fal.ai/models/fal-ai/kling-video/create-voice) if you add dubbed lines later. |
| **End keyframe** | **`end_image_url`** optional — use when you have **two** approved stills and want an interpolated transition (rare for v1 chapter tests). |

**Not spelled out on the public `llms.txt` page:** pixel-perfect “anime cel” fidelity rules — that’s why we **lock look in Stage 4** and keep I2V prompts **minimal** (§4).

### 2.2 Research — Fal’s **image-to-video prompting** patterns (transferable)

Kling does not have a dedicated long-form “prompt guide” on Fal Learn at the time of this skill. Fal **does** publish I2V prompt doctrine for [**Kandinsky5 Pro Image to Video**](https://fal.ai/models/fal-ai/kandinsky5-pro/image-to-video) — the **ideas** transfer to any image-driven video model, including Kling:

**Source:** [Kandinsky5 Pro Image to Video Prompt Guide](https://fal.ai/learn/biz/kandinsky5-pro-image-to-video-prompt-guide) (fal Learn, enterprise).

| Idea | Application to **this** project |
|------|----------------------------------|
| **Temporal evolution, not T2V** | I2V “determines **temporal evolution**” from the still — don’t ask for **new** layout, new cast, or **reveal** that isn’t in the PNG (e.g. “pull back to full body” when the still is already a wide shot). |
| **Three instruction streams** | Split your thinking into **camera**, **subject motion**, **environment** (wind, particles, light flicker, clouds). In the **prompt sentence**, cover all three **without** contradicting each other. |
| **Structured prompt** | Anchor **who/what and pose** → **what moves** → **camera words** (explicit: “slow dolly in,” not “camera moves”). |
| **Cinematic vocabulary** | Terms like **dolly, crane, rack focus, shallow depth** map to training — useful for **epic wides** (S010 ridge, S076 field) **if** motion stays gentle. |
| **Pacing words** | **gradually, smoothly, slowly** vs abrupt zoom — controls velocity without extra API knobs. |
| **“What should not happen”** | State static background or **no sudden moves** when you need faces stable — complements **`negative_prompt`**. |
| **Lighting continuity** | Acknowledge light in the still (**side light, rim, overcast**) so temporal changes don’t fight Stage 4 lighting. |
| **Common failures** | **Too many motions at once** (more than ~3 distinct motions → simplify); **vague camera**; **contradictory** lines (“perfectly still” + “dancing”); **prompt fights source image**. |

Kandinsky-specific knobs (**resolution**, **inference steps**) **do not** apply to Kling — only the **prompt structure and habits** above do.

### 2.3 Research — Fal ecosystem: why Kling fits “quality I2V” on platform

**Source:** [10 Best AI Video Generators in 2026](https://fal.ai/learn/tools/ai-video-generators) (fal Learn — tool roundup).

Useful **qualitative** points from that article for scoping expectations:

- **Kling family** is repeatedly positioned around **fluid motion**, **cinematic camera behavior**, and **prompt adherence** vs many competitors — aligns with **controlled, storyboard-driven** clips from Finals.
- **Native audio** on newer Kling / other models is powerful but introduces **lip-sync, dialogue correctness, and cost** — for *Frieren*-style assembly from manga, **silent I2V + your own audio mix** is usually safer until you opt in.
- **One API pattern on fal** — same `FAL_KEY`, queue, and client as Stage 4; switching I2V endpoints later is mostly an **endpoint string + schema** change.

---

## 3. Kling 2.6 Pro I2V — API checklist

Read the live schema: [API](https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video/api) · [LLM summary](https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video/llms.txt).

**Required**

- **`prompt`** — Describe **only what moves** and **how the camera behaves**; repeat “keep same composition / same characters” when drift is an issue.
- **`start_image_url`** — Public URL (e.g. `fal_client.upload_file` on your Final PNG).

**Common optional fields**

- **`duration`:** `"5"` (default) or `"10"`.
- **`negative_prompt`:** Start from model default (`blur, distort, and low quality`) and add project drift terms: `manga panel, speech bubble, halftone, extra limbs, morphing face, duplicate character, text overlay, watermark`.
- **`generate_audio`:** **`false`** for silent anime-style clips (cheaper, no random dialogue). **`true`** only when you intentionally want native audio / voice (and accept higher cost).
- **`end_image_url`:** Optional second keyframe for transition shots.

**Driver image**

- Upload the **sharpest, color-graded** still that already matches **Stage 2** description and **Stage 3** wardrobe.
- **Aspect ratio:** Match the still (most chapter keys are **16:9**); if the API crops oddly, fix resolution in Stage 4 first.

---

## 4. How to write the motion prompt (not the image prompt)

Image prompts (Flux / Nano Banana) lock **identity, wardrobe, and background**.  
Video prompts should be **short, motion-first**, and **subtle** for v1:

1. **Anchor:** “Fantasy anime, same composition as the reference image.”
2. **Motion:** One primary idea (**hair / cloth / snow / petals / fire / glints**) + small secondary (**gentle wind, slow particle drift**).
3. **Camera:** Prefer **static** or **very slow** push / drift — aggressive moves cause identity drift.
4. **Anti-drift:** “No new characters, no turning subjects to face camera unless already implied, no cuts inside the clip.”
5. **Layer tone:** Match **stage_03** prefix (e.g. `fb_hero` → dreamy petals, soft sun-dust; `present` Northern → cool air, crisp light).

Do **not** paste the entire `*_PROMPT_FLUX` block unless you are debugging; it overloads motion models and fights the still.

**TV-anime framerate on Kling (no `fps` API):** use [anime-scene-i2v-prompting **§4c**](../anime-scene-i2v-prompting/SKILL.md) — limited-animation / on-twos prompt + anti–3D-glide negatives; optional `generate_s004_kling_i2v.py --anime-fps 12`. **Approved on S004** (2026-05-27).

---

## 5. Verification (before calling Fal)

```markdown
## I2V prompt verification
- [ ] Shot ID + **Layer** + beat from stage_02; scarf/flashback rules respected
- [ ] Start frame path or URL identified (Stage 4 / Final)
- [ ] Motion prompt is **subtle**; camera mostly static or slow
- [ ] `generate_audio` chosen on purpose (false for silent BGM workflow)
- [ ] `negative_prompt` extended if faces morph or manga artifacts return
- [ ] `duration` 5s for first test
```

---

## 6. Handoff template

```text
Task: Stage 5 I2V for shot <S0xx>
Use skill: fal-image-to-video-prompting
Model: fal-ai/kling-video/v2.6/pro/image-to-video
Steps: (1) Read stage_02 row + stage_03 PREFIX for Layer (2) Pick Final still → upload (3) Build motion-only prompt + JSON args (4) Run fal_client.subscribe (5) Log output path in stage_04 or Tests
```

---

## 7. Example — apply skill (Kling 2.6) for **S010**

**Context (stages 1–3):** `present`, WS HERO, golden Weise ridge — three travelers **backs to camera**, valley + city **gold**; beat **B3**. Stills: e.g. [`Tests/S010_flux-2-pro-edit_20260326_094807.png`](../../../Tests/S010_flux-2-pro-edit_20260326_094807.png).

**Motion prompt (paste as `prompt`):**

```text
Fantasy anime wide shot — keep the exact same composition and three silhouettes on the ridge as the reference. Very subtle motion only: a light breeze moves the travelers' hair and coat hems; the golden valley and distant city shimmer with slow, soft reflections; a few gentle dust motes or sparks in the air. Camera almost locked, optional imperceptible slow dolly-in. Smooth, cinematic, no new people, no one turns around, no cuts, no manga or text.
```

**Suggested `arguments` (Python / `fal_client`):**

```python
{
    "prompt": "<motion prompt above>",
    "start_image_url": "<upload URL of Final S010 PNG>",
    "duration": "5",
    "generate_audio": False,
    "negative_prompt": "blur, distort, low quality, manga panel, speech bubble, halftone, extra limbs, morphing face, duplicate person, text, watermark",
}
```

**Model ID:** `fal-ai/kling-video/v2.6/pro/image-to-video`

---

## Related paths

| Path | Role |
|------|------|
| [`manga-to-anime-fal-stages.plan.md`](../../../manga-to-anime-fal-stages.plan.md) | Stage 5 overview |
| [`docs/stage5-image-to-video-fal.md`](../../../docs/stage5-image-to-video-fal.md) | **Handbook** — I2V model, API, prompts, examples |
| [`.cursor/skills/anime-scene-i2v-prompting/SKILL.md`](../anime-scene-i2v-prompting/SKILL.md) | **Scene-first** — pull shot truth from stage_01–04 → motion prompt |
| [`docs/flux-2-pro-prompting-guide.md`](../../../docs/flux-2-pro-prompting-guide.md) | Image side (Stage 4) |
| [`scripts/fal_common.py`](../../../scripts/fal_common.py) | Image `*_PROMPT_FLUX` (reference for shot content, not full I2V paste) |

**External (Fal research linked in §2):**

| URL | Role |
|-----|------|
| [Kling 2.6 Pro I2V API](https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video/api) | Schema + examples |
| [Kling 2.6 Pro I2V `llms.txt`](https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video/llms.txt) | Pricing, parameters, audio quoting |
| [Kandinsky5 Pro I2V prompt guide](https://fal.ai/learn/biz/kandinsky5-pro-image-to-video-prompt-guide) | Transferable I2V prompt structure |
| [Best AI video generators (fal Learn)](https://fal.ai/learn/tools/ai-video-generators) | Kling positioning vs other fal models |
