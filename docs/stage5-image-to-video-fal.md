# Stage 5 — Image-to-video on Fal.ai (reference handbook)

**Project:** AI_Animation — manga → anime-like sequence (Chapter 81 workflow).  
**Purpose:** Single place to **look up** how we turn **approved Stage 4 stills** into **short video clips** on Fal: default model, API fields, prompting rules, research sources, and a copy-paste example.

**Cursor agent skills:** [`.cursor/skills/anime-scene-i2v-prompting/SKILL.md`](../.cursor/skills/anime-scene-i2v-prompting/SKILL.md) (motion prompts from stage/scene files) · [`.cursor/skills/fal-image-to-video-prompting/SKILL.md`](../.cursor/skills/fal-image-to-video-prompting/SKILL.md) (Fal API, research, checklist)

**End-to-end recipe:** [`manga-to-anime-fal-stages.plan.md`](../manga-to-anime-fal-stages.plan.md) — Stage 5 § “Add motion”.

**Stage 4 (still generation):** [`docs/flux-2-pro-prompting-guide.md`](./flux-2-pro-prompting-guide.md)

---

## 1. Pipeline contract

| Stage | Role for I2V |
|-------|----------------|
| **1** — [`stage_01_ingest.md`](../Frierien-chapter081/stage_01_ingest.md) | Beats, page splits (e.g. `016.jpg` tiers), gutter context — motion must not contradict **which timeline** the shot belongs to. |
| **2** — [`stage_02_shot_list.md`](../Frierien-chapter081/stage_02_shot_list.md) | **`Layer`**, framing, “what we see”, props (scarf, axe, petals, snow). |
| **3** — [`stage_03_series_bible.md`](../Frierien-chapter081/stage_03_series_bible.md) | Fantasy TV anime look, PREFIX mood per layer, global negatives — mirror drift tokens in **`negative_prompt`**. |
| **4** | **Driver image only:** one **approved** PNG per shot — **default path [`Tests/Final/`](../Tests/Final/)** (user-accepted Finals). Use `Tests/` only for WIP or until a still is copied into `Tests/Final/`. I2V **does not** replace a bad still — fix identity and layout in Stage 4 first. |

**Rule:** The video model **evolves the still in time**. It does **not** reliably “invent” new composition, new cast, or off-panel reveals. Keep motion **subtle** on v1.

---

## 2. Default model: Kling 2.6 Pro (image-to-video)

| | |
|--|--|
| **Model ID** | `fal-ai/kling-video/v2.6/pro/image-to-video` |
| **Playground** | [fal.ai — Kling 2.6 Pro I2V](https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video) |
| **API** | [OpenAPI / schema](https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video/api) |
| **Parameter summary** | [`llms.txt`](https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video/llms.txt) |

**Why this default**

- Same **`FAL_KEY`** and `fal_client.subscribe` pattern as [`scripts/generate_*_ref_edit.py`](../scripts/).
- **`start_image_url`** + **`prompt`** matches “hero still → clip.”
- **`duration`:** `"5"` or `"10"` seconds — scope one story beat per clip.
- **Cost:** roughly **half per second** with **`generate_audio`: `false`** vs native audio on — see **Pricing** in [`llms.txt`](https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video/llms.txt). **Silent clip + your own BGM** is the default pipeline assumption.

**Alternatives (short)**

| Endpoint | When |
|----------|------|
| `fal-ai/kling-video/v2.1/pro/image-to-video` | Older API; **`image_url`** field — [docs](https://fal.ai/models/fal-ai/kling-video/v2.1/pro/image-to-video/api). |
| `fal-ai/kling-video/o3/standard/image-to-video` | Strong **start + end** frame control — two Finals. |
| `fal-ai/ltx-2-19b/image-to-video` | Built-in **audio** path — heavier. |
| `fal-ai/veo3.1/reference-to-video` | Different contract — validate schema before adopting. |

---

## 3. API quick reference (Kling 2.6 Pro I2V)

Always re-check the [live API page](https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video/api) before shipping automation.

| Field | Notes |
|-------|--------|
| **`prompt`** | **Motion + camera + atmosphere** — short, consistent with the PNG. Do **not** paste full Flux `*_PROMPT_FLUX` blocks (see §5). |
| **`start_image_url`** | **Required.** Public URL (typical: `fal_client.upload_file(path)`). |
| **`duration`** | `"5"` (default) or `"10"`. |
| **`negative_prompt`** | Model default is quality-oriented; **extend** for manga drift: halftone, bubbles, extra limbs, morphing faces, text, watermark. |
| **`generate_audio`** | **`false`** for silent anime assembly. **`true`** only if you want native sound/dialogue and accept cost / unpredictability. |
| **`end_image_url`** | Optional second keyframe. |
| **`voice_ids`** | Optional; use with quoted speech in `prompt` per [`llms.txt`](https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video/llms.txt); [create-voice](https://fal.ai/models/fal-ai/kling-video/create-voice) if needed. |

**Minimal Python call pattern**

```python
import fal_client

result = fal_client.subscribe(
    "fal-ai/kling-video/v2.6/pro/image-to-video",
    arguments={
        "prompt": "<motion-only prompt, see §5>",
        "start_image_url": "<URL from fal_client.upload_file>",
        "duration": "5",
        "generate_audio": False,
        "negative_prompt": (
            "blur, distort, low quality, manga panel, speech bubble, halftone, "
            "extra limbs, morphing face, duplicate person, text, watermark"
        ),
    },
    with_logs=True,
)
# result["video"]["url"] — confirm key from response payload
```

---

## 4. Research-backed prompting (fulfill our needs)

### 4.1 What Fal documents (Kling 2.6)

- Image-conditioned **temporal evolution** — prompt must **match what’s in the frame**.
- **Duration cap** — design for **one moment** in 5–10s, not a full scene arc.
- **Audio:** turning **`generate_audio`** on changes **cost** and means **dialogue in quotes** + optional **voice** IDs — see [`llms.txt`](https://fal.ai/models/fal-ai/kling-video/v2.6/pro/image-to-video/llms.txt).

### 4.2 Transferable I2V patterns (Fal Learn)

Fal’s **[Kandinsky5 Pro Image to Video Prompt Guide](https://fal.ai/learn/biz/kandinsky5-pro-image-to-video-prompt-guide)** is not Kling-specific, but the **instruction pattern** applies:

1. **Anchor** subject / pose (already in the still — reinforce “same composition”).
2. **Action** — what changes over time (hair, cloth, particles, light).
3. **Camera** — **explicit** (e.g. “slow dolly in”), not “camera moves.”

Also: avoid **too many simultaneous motions**, **contradictions**, and **asks that contradict the still** (e.g. dramatic pull-back when the frame is already a wide epic shot). Use **pacing words** (*slowly*, *gently*, *gradually*). Mention **lighting continuity** if faces drift.

*Kandinsky-only knobs (steps, resolution enums) do not apply to Kling.*

### 4.3 Ecosystem note

**[10 Best AI Video Generators in 2026](https://fal.ai/learn/tools/ai-video-generators)** (fal Learn): Kling is generally framed around **fluid motion**, **cinematic cameras**, and **prompt adherence** — good fit for **storyboard-driven** clips from Finals.

---

## 5. Motion prompt recipe (this project)

1. **Anchor:** Fantasy anime; **same composition as the reference image.**
2. **Primary motion:** one clear idea (wind on hair/cloth, snow drift, petals, firelight, distant glints).
3. **Camera:** **static** or **very slow** push/drift — aggressive moves increase identity drift.
4. **Guards:** no new characters; no 180° turns unless the still already implies it; no in-clip “cuts.”
5. **Layer tone:** align with [`stage_03_series_bible.md`](../Frierien-chapter081/stage_03_series_bible.md) PREFIX for that shot’s **`Layer`** (`fb_hero` = soft memory, petals; `present` = cooler Northern air).

**Do not** dump [`scripts/fal_common.py`](../scripts/fal_common.py) `*_PROMPT_FLUX` into I2V — use **short motion prose** only.

---

## 6. Pre-flight checklist

- [ ] Shot ID and **`Layer`** from [`stage_02_shot_list.md`](../Frierien-chapter081/stage_02_shot_list.md) (scarf / flashback rules OK).
- [ ] Final still path chosen and uploaded; URL valid.
- [ ] Motion prompt is **simple**; camera mostly **locked** or **slow**.
- [ ] **`generate_audio`** set **intentionally** (`false` for default pipeline).
- [ ] **`negative_prompt`** extended if manga artifacts or morphing return.
- [ ] First test uses **`duration`: `"5"`**.

---

## 7. Example — S010 golden ridge (copy-paste)

**Still:** any approved **S010** Final (e.g. golden vista, three figures backs to camera).

**`prompt`:**

```text
Fantasy anime wide shot — keep the exact same composition and three silhouettes on the ridge as the reference. Very subtle motion only: a light breeze moves the travelers' hair and coat hems; the golden valley and distant city shimmer with slow, soft reflections; a few gentle dust motes or sparks in the air. Camera almost locked, optional imperceptible slow dolly-in. Smooth, cinematic, no new people, no one turns around, no cuts, no manga or text.
```

**Arguments:** match §3 (`generate_audio`: `False`, extended `negative_prompt`).

---

## 8. Revision log

| Date | Change |
|------|--------|
| 2026-03-26 | Initial handbook: Kling 2.6 Pro I2V default, API + research + S010 example; points to Agent skill and Stages 1–4 sources. |

---

## See also

| Resource | Use |
|----------|-----|
| [`.cursor/skills/fal-image-to-video-prompting/SKILL.md`](../.cursor/skills/fal-image-to-video-prompting/SKILL.md) | Agent checklist, handoff blurb |
| [`docs/flux-2-pro-prompting-guide.md`](./flux-2-pro-prompting-guide.md) | Stage 4 image prompting |
| [`manga-to-anime-fal-stages.plan.md`](../manga-to-anime-fal-stages.plan.md) | Full stage diagram |
