# Prototype video → music analysis guideline (AI_Animation)

**Purpose:** Analyze an **assembled edit MP4** (e.g. `PrototypeFinal01.mp4`) and produce a **music brief** for underscore generation (primarily **`fal-ai/minimax-music/v2.6`**). This is **post-I2V** — separate from per-shot I2V/SFX prompts.

**Related docs:**

| Doc | Role |
|-----|------|
| [`docs/sfx-models-fal.md`](sfx-models-fal.md) | Foley / video-to-audio (not full scores) |
| [`docs/stage5-image-to-video-fal.md`](stage5-image-to-video-fal.md) | I2V; clips often already have ambient audio |
| [`Chapter-81/stage_03_series_bible.md`](../Chapter-81/stage_03_series_bible.md) | `PREFIX_PRESENT` mood |
| [`Chapter-81/stage_01_ingest.md`](../Chapter-81/stage_01_ingest.md) | Beat IDs (B1–B12) for story phase labels |

**Logged examples:** [`outputs/analysis/`](../outputs/analysis/) — one `*_music_analysis_log.md` per analyzed cut.

---

## 1. When to use this workflow

- User has a **timeline assembly** (DaVinci, ffmpeg concat, etc.) and wants **BGM** direction or a **MiniMax prompt**.
- User asks to “analyze the video for music,” “what score fits,” or “match music to PrototypeFinal0x.”
- **Not** for per-shot I2V motion — use [`.cursor/skills/anime-scene-i2v-prompting/SKILL.md`](../.cursor/skills/anime-scene-i2v-prompting/SKILL.md).

---

## 2. Analysis pipeline (agent must execute)

### Step A — Technical probe (`ffprobe`)

```powershell
ffprobe -v error -show_format -show_streams -print_format json "path\to\edit.mp4"
```

Record:

| Field | Why |
|-------|-----|
| **duration** | Target trim length for underscore |
| **width / height / fps** | Delivery context |
| **Audio present?** codec, sample_rate, channels | Mix strategy (duck under existing foley) |
| **mean_volume** (optional) | Headroom for BGM |

```powershell
ffmpeg -i "path\to\edit.mp4" -af volumedetect -f null - 2>&1
```

### Step B — Visual timeline (frame samples)

Extract frames at fixed intervals (default **every 5 s**):

```powershell
$out = "outputs\analysis\<basename>_frames"
New-Item -ItemType Directory -Force -Path $out | Out-Null
ffmpeg -y -i "path\to\edit.mp4" -vf "fps=1/5" -q:v 2 "$out\frame_%03d.jpg"
```

**Read** frames across the timeline. Map each bucket to:

- **Setting** (camp, forest path, ridge, city vista, etc.)
- **Framing** (WS / MS / CU)
- **Emotional read** (cozy, whimsical, melancholic, awe, etc.)
- **Likely shot IDs** if recognizable from repo stills / stage_02 (optional but helpful)

### Step C — Cross-check story phase

Match visual arc to **Chapter-81 beats** when the prototype covers B2/B3:

| Phase | Typical visuals | Music tendency |
|-------|-----------------|----------------|
| Camp / hook | Fire, rest, dialogue | Sparse, intimate, minor key |
| Messenger / letter | Animal, envelope, reading | Gentle, curious |
| Memory / ghost | Overlay figure, somber faces | Bittersweet, piano/flute |
| Travel | Walking path, daylight | Light pulse, tempo up slightly |
| Vista / gold | Backs, wide landscape, city | Slow swell, wider strings, still not trailer |

### Step D — Write the music brief

Deliver:

1. **Technical summary** (duration, audio headroom).
2. **Timeline table** (~5 s buckets): time → visual → emotion → musical need.
3. **ASCII energy arc** (one line).
4. **Genre / instrumentation / key / BPM** recommendations.
5. **Do / avoid** list (Frieren-adjacent underscore, not EDM/trailer).
6. **Ready-to-paste MiniMax prompt** (`is_instrumental: true`) with **arc in prompt text** (Fal v2.6 has no duration API).
7. **Mux notes** (trim BGM to video duration, duck −20 to −26 dB under existing AAC).

### Step E — Log the session

Append or create:

`outputs/analysis/<VideoBasename>_music_analysis_log.md`

Use template in **§4** below. Link from skill runs so history is traceable.

---

## 3. Music model routing (Fal)

| Need | Model | Notes |
|------|--------|------|
| **Full instrumental bed** (default) | [`fal-ai/minimax-music/v2.6`](https://fal.ai/models/fal-ai/minimax-music/v2.6) | `is_instrumental: true`; prompt 10–2000 chars; ~$0.15/gen; typical 2–4 min → **trim** to edit length |
| **Timed sections (ms)** | [`fal-ai/elevenlabs/music`](https://fal.ai/models/fal-ai/elevenlabs/music) | `composition_plan` + `force_instrumental` — paid, precise |
| **Per-clip only** | [`fal-ai/kling-video/video-to-audio`](https://fal.ai/models/fal-ai/kling-video/video-to-audio) | `background_music_prompt` ≤200 chars; 3–20 s — not whole prototype |
| **Not BGM** | Beatoven/Cassette SFX, ThinkSound, Mirelo | Foley only per `docs/sfx-models-fal.md` |

### Text-only generation (important)

**MiniMax Music v2.6 does not accept the prototype video** (no `video_url`, no frames). The agent’s frame analysis informs a **written prompt** only; Fal returns a standalone MP3. **Mux** is local ffmpeg — BGM is layered **under** existing I2V foley, not composed “on top of” pixels by the model.

### Repo script: `scripts/generate_bgm_minimax.py`

After the analysis log exists:

```powershell
cd scripts
python generate_bgm_minimax.py --from-log ..\outputs\analysis\<Basename>_music_analysis_log.md --mux-video ..\<edit>.mp4
```

| Flag | Role |
|------|------|
| `--from-log` | Parse `## MiniMax prompt (instrumental)` blockquote from log |
| `--mux-video` | ffprobe duration → trim/fade → mux; default out: `<stem>_with_bgm_<ts>.mp4` next to source |
| `--bgm-volume` | Default `0.22` (duck under foley) |
| `--dry-run` | Print Fal arguments only |

**Requires:** `FAL_KEY` in `.env`, `fal-client`, ffmpeg on PATH.

**Fal `audio_setting`:** pass `sample_rate` and `bitrate` as **integers** (e.g. `44100`, `256000`) — string values fail API validation.

After a successful run, append a **## Generation record** section to the log (see §4).

### MiniMax prompt pattern (instrumental)

```
[Key], [BPM], fantasy anime underscore instrumental, [mood], [instruments],
[mix note: under dialogue and foley], no vocals, no EDM, no trailer brass.
Emotional arc for [N] second edit: [act 1] → [act 2] → [act 3].
```

**Rules:**

- `is_instrumental: true`; `lyrics_optimizer: false`; omit `lyrics`.
- Specify **key + BPM** (model follows well).
- Describe **energy arc in prose** (no `duration` field on Fal v2.6).
- Generate 2–3 variants; pick closest; **ffmpeg trim + afade**.

### Mix under existing clip audio

Most prototypes already have **I2V foley** (AAC). BGM is a **second stem**, not a replacement.

```powershell
ffmpeg -i edit.mp4 -i bgm_trimmed.mp3 -filter_complex "[1:a]volume=0.22,afade=t=out:st=58:d=2[bgm];[0:a][bgm]amix=inputs=2:duration=first[aout]" -map 0:v -map "[aout]" -c:v copy -c:a aac -b:a 192k edit_with_bgm.mp4
```

Adjust `volume`, `st`, and `d` to duration.

---

## 4. Log file template

Save as `outputs/analysis/<Basename>_music_analysis_log.md`:

```markdown
# Music analysis log — <basename>.mp4

- **Date (UTC):** YYYY-MM-DD
- **Analyzer:** Cursor agent (skill: prototype-video-music-analysis)
- **Source video:** `<repo-relative path>`
- **Guideline version:** docs/prototype-video-music-analysis-guideline.md

## ffprobe summary

| Field | Value |
|-------|-------|
| Duration | |
| Resolution | |
| FPS | |
| Audio | |
| Mean volume (if run) | |

## Timeline (5 s samples)

| Time | Visual | Emotion | Music need |
|------|--------|---------|------------|
| 0–5 s | | | |

## Energy arc

(text diagram)

## Music recommendation

(genre, key, BPM, instruments, do/avoid)

## MiniMax prompt (instrumental)

(blockquote prompt)

## Next steps

- [ ] Generate MiniMax v2.6
- [ ] Trim to duration
- [ ] Mux under prototype

## Generation record

(fill after `scripts/generate_bgm_minimax.py` run: date, model, command, paths, mix level, QC note)
```

---

## 5. Frieren Ch.81 defaults (this repo)

When the cut matches **present** Northern adventure (Chapter 81 prototype):

| Attribute | Default |
|-----------|---------|
| **Key** | D minor or A minor |
| **BPM** | 72–80 (camp) → 76–84 (walk) |
| **Style** | Evan Call–adjacent: bittersweet orchestral fantasy, Celtic color |
| **Instruments** | Piano, alto flute, harp, soft strings; light pulse only after travel |
| **Avoid** | Vocals, EDM, trailer brass, busy percussion, comedy ukulele |
| **Gold vista** | Warm swell at **end** only — not metallic shimmer for whole track if camp is green |

---

## 6. Verification checklist

- [ ] `ffprobe` duration recorded.
- [ ] ≥10 frames or full 5 s coverage of edit length.
- [ ] Timeline table spans **0 → duration**.
- [ ] Brief distinguishes **acts** (not single mood).
- [ ] Existing **clip audio** noted (duck vs replace).
- [ ] MiniMax prompt includes **key, BPM, arc, no vocals**.
- [ ] Log file written under `outputs/analysis/`.
- [ ] User handoff includes trim/mux command with **actual seconds**.
- [ ] If BGM generated: **Generation record** in log; outputs under `outputs/audio/bgm/` and optional `*_with_bgm_*.mp4`.

---

## 7. Changelog

| Date | Change |
|------|--------|
| 2026-05-27 | Initial guideline + PrototypeFinal01 reference log |
| 2026-05-29 | `generate_bgm_minimax.py` handoff; text-only MiniMax note; Generation record in log; PrototypeFinal01 first mux QC |
