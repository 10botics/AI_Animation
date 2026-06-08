---
name: prototype-video-music-analysis
description: >-
  Analyzes assembled edit MP4s (e.g. PrototypeFinal01) via ffprobe and sampled frames,
  writes a music brief and MiniMax prompt, and logs to outputs/analysis. Always reads
  docs/prototype-video-music-analysis-guideline.md first. Use for "analyze video for music,"
  "what BGM fits," "match music to prototype," or before fal-ai/minimax-music/v2.6 runs.
---

# Prototype video → music analysis

## 1. Always read first (required)

**Do not skip.** The guideline is the single source of truth for this workflow.

| Resource | Role |
|----------|------|
| **[`docs/prototype-video-music-analysis-guideline.md`](../../../docs/prototype-video-music-analysis-guideline.md)** | **Primary** — pipeline, templates, MiniMax routing, mix notes, checklist |
| [`docs/sfx-models-fal.md`](../../../docs/sfx-models-fal.md) | Foley vs BGM model boundaries |
| [`Chapter-81/stage_01_ingest.md`](../../../Chapter-81/stage_01_ingest.md) | Beat IDs for story-phase labels |
| [`Chapter-81/stage_03_series_bible.md`](../../../Chapter-81/stage_03_series_bible.md) | `PREFIX_PRESENT` mood |
| **Prior log (if exists)** | `outputs/analysis/<VideoBasename>_music_analysis_log.md` |
| **BGM script** | [`scripts/generate_bgm_minimax.py`](../../../scripts/generate_bgm_minimax.py) |

**Reference log:** [`outputs/analysis/PrototypeFinal01_music_analysis_log.md`](../../../outputs/analysis/PrototypeFinal01_music_analysis_log.md) — analysis + **completed generation record** (~66 s, mux approved 2026-05-29).

---

## 2. Trigger

Use when the user:

- Names a **prototype / assembly MP4** and asks what **background music** fits.
- Wants **video analysis** before **MiniMax** or **ElevenLabs Music**.
- Says “analyze the video for score,” “BGM for PrototypeFinal,” or “music brief from the cut.”

**Not** for per-shot I2V — use [`anime-scene-i2v-prompting`](../anime-scene-i2v-prompting/SKILL.md).

---

## 3. Execute the guideline pipeline

Follow **§2** of [`docs/prototype-video-music-analysis-guideline.md`](../../../docs/prototype-video-music-analysis-guideline.md) in order:

1. **ffprobe** — duration, resolution, fps, audio codec, optional `volumedetect`.
2. **Frame extract** — `fps=1/5` (or finer if user asks) → `outputs/analysis/<basename>_frames/`.
3. **Read frames** — build timeline table (time → visual → emotion → music need).
4. **Cross-check** Chapter-81 beats / shot IDs when applicable.
5. **Music brief** — key, BPM, instruments, do/avoid, energy arc, MiniMax prompt.
6. **Write log** — `outputs/analysis/<Basename>_music_analysis_log.md` using guideline **§4** template.

Use **PowerShell** on Windows (`;` not `&&`). Paths: repo root or absolute.

---

## 4. Deliver to the user (every time)

```markdown
## Music analysis — <filename>

- **Duration / audio:** (from ffprobe)
- **Log written:** outputs/analysis/<Basename>_music_analysis_log.md

### Timeline (summary)
(table or bullets)

### Energy arc
(ascii line)

### Recommended music
(key, BPM, genre, instruments, do/avoid)

### MiniMax prompt (`fal-ai/minimax-music/v2.6`)
> … (is_instrumental: true)

### Next steps
(trim to duration, mux commands, optional generate script)
```

Point to the **log file** for full detail. If user asks only for generation, still confirm analysis log exists or run analysis first.

---

## 5. Generation handoff (optional)

When user wants to **generate** after analysis:

| Step | Action |
|------|--------|
| Model | `fal-ai/minimax-music/v2.6` — **text prompt only** (video/frames are **not** sent to Fal) |
| Script | `scripts/generate_bgm_minimax.py --from-log … --mux-video …` (see guideline **§3**) |
| Args | `is_instrumental: true`, `lyrics_optimizer: false`, prompt from log; `audio_setting` sample_rate/bitrate as **integers** |
| Post | Trim to **ffprobe duration**; `afade` out 1–2 s; mux under edit (`--bgm-volume` default **0.22**) |
| Log | Append **## Generation record** to `outputs/analysis/<Basename>_music_analysis_log.md` (paths, command, mix level, QC) |

Do **not** use Beatoven/Cassette text SFX models for BGM. Prefer **one bed per edit** over per-shot music unless user requests acts split.

**PrototypeFinal01 (validated):** one prompt variant + `volume=0.22` was enough when the log’s arc prose matches the cut; raw MiniMax MP3 is ~2+ min — always trim to edit length.

---

## 6. Verification (from guideline §6)

Before finishing, confirm checklist in [`docs/prototype-video-music-analysis-guideline.md`](../../../docs/prototype-video-music-analysis-guideline.md) §6 — especially timeline coverage, act distinction, duck-under-foley note, log file on disk, and **Generation record** if BGM was generated.

---

## 7. Updating the guideline

If the workflow changes (new Fal music model, new log fields), update **`docs/prototype-video-music-analysis-guideline.md`** first, then adjust this skill’s pointers — **never** duplicate long procedure text only in the skill.
