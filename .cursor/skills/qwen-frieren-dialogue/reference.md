# Qwen Frieren dialogue — reference

Companion to [SKILL.md](SKILL.md). Read when debugging quality, reproducing v11, or extending the pipeline.

---

## Approved deliverable (2026-06-02, EN ref)

```
outputs/video/final/S008_kling-v26-pro_i2v_natural-audio_20260527_092816_frieren_dialogue_v11_20260602_103647.mp4
```

## JP ref trial (2026-06-03)

```
outputs/video/final/S008_kling-v26-pro_i2v_natural-audio_20260527_092816_frieren_dialogue_v12_20260603_045232.mp4
```

- **Engine:** Qwen3 1.7B (Fal clone + TTS)
- **Ref (current):** `Voice Reference/Japanese/Frieren/frieren_jp_qwen_ref.wav` + `.txt` from `fireren Japan.mp4`
- **Story:** `panels/jap/panel_s008jap.png` — `FRIEREN_S008_DIALOGUE` in `qwen_tts.py`
- **Legacy ref:** `Voice Reference/English/Frieren/frieren_1min_qwen_ref.wav` + `.txt`
- **Synthesis:** split phrases, 0.55s pause, fade+apad concat
- **Mux:** start 2.05s, duck 0.35

---

## Work timeline (summary)

1. **MiniMax** early dialogue tests → user chose **Qwen3**
2. **v4** — 130s dub compilation ref; best timbre reference for user QC
3. **Tier-1 research** — `reference_text` on clone+TTS; 10–15s curated ref; Demucs vocals
4. **v6** — `frieren_qwen_ref_15s` from dub comp VAD window
5. **v7** — `voice Frieren1min.mp4` → Fal Demucs → `frieren_1min_qwen_ref`
6. **v8–v9** — scene-grounded `FRIEREN_S008_PROMPT` from chapter B3 logs
7. **v10** — split-phrase TTS (fixed rushed pause); **hitch** from `anullsrc` concat
8. **v11** — PCM normalize, 35ms fades, `apad` silence; **current best**

---

## Iteration outputs

| Tag | Location | Notes |
|-----|----------|-------|
| v4 | `outputs/voice/S008/iterations/S008_frieren_qwen_v4_20260602_035231.mp4` | 130s ref timbre benchmark |
| v6 | `iterations/S008_frieren_qwen_v6_*.mp4` | Curated 15s ref |
| v7 | `iterations/S008_frieren_qwen_v7_*.mp4` | 1min Demucs chain |
| v8 | `outputs/video/final/*_frieren_dialogue_v8_*.mp4` | Scene prompt |
| v9 | `outputs/video/final/*_frieren_dialogue_v9_*.mp4` | Scene prompt (single clip) |
| v10 | `outputs/video/final/*_frieren_dialogue_v10_*.mp4` | Split phrase; hitch |
| **v11** | `outputs/video/final/*_frieren_dialogue_v11_20260602_103647.mp4` | **Ship** |

Compare folder (historical backends): `outputs/voice/S008/compare/`

---

## Voice reference files

| Path | Role |
|------|------|
| `voice Frieren1min.mp4` | Source dub clip (~74s) |
| `voice_refs/frieren_1min_vocals.wav` | Fal Demucs output |
| `Voice Reference/English/Frieren/frieren_1min_qwen_ref.wav` | 12s VAD window for Qwen |
| `Voice Reference/English/Frieren/frieren_1min_qwen_ref.txt` | Whisper transcript → `reference_text` |
| `voice_refs/frieren_qwen_ref_15s.wav` + `.txt` | v6 curated (dub comp source) |
| `voice_refs/frieren_eng_dub_ref_130s_skip0.wav` | v4 long ref |
| `voice_registry.local.json` | Cached `speaker_embedding` URL + metadata |

**1min ref transcript (approx.):** potion/clothing gift scene — used for ICL-style alignment on Fal.

---

## Code map

### `scripts/qwen_tts.py`

| Symbol | Purpose |
|--------|---------|
| `QWEN_CLONE` / `QWEN_TTS` | Fal endpoints |
| `DEFAULT_PROMPT` | General Frieren delivery |
| `FRIEREN_S008_PROMPT` | Scene context (doc / fallback) |
| `FRIEREN_S008_PHRASES` | `("Now we're talking.", "Let's do it.")` |
| `FRIEREN_S008_PAUSE_SEC` | `0.55` |
| `FRIEREN_S008_PROMPT_PART1/2` | Per-phrase TTS prompts |
| `FRIEREN_DIALOGUE_START_SEC` | `2.05` |
| `synthesize()` | Single Fal TTS call |
| `synthesize_s008_frieren()` | Two calls + concat |
| `concat_with_pauses()` | PCM join with fades + apad |
| `resolve_character_embedding()` | Clone + registry cache |

### `scripts/generate_s008_dialogue.py`

Main entry: TTS → stems → ffmpeg mux → `outputs/video/final/`.

### Supporting scripts

- `prepare_frieren_qwen_ref.py` — VAD, optional Demucs, Whisper
- `isolate_vocals_fal.py` — `fal-ai/demucs`
- `generate_s008_frieren_v6.py` / `v7.py` — frozen iteration runners
- `generate_s008_frieren_iterations.py` — batch variants
- `compare_s008_frieren_voices.py` — MiniMax / F5 / Qwen

---

## `concat_with_pauses` implementation notes

**v10 (bad):** insert silence via `anullsrc` between decoded streams → boundary click.

**v11 (good):**

```
[0:a] → resample 24k mono → fade-out 35ms → apad 0.55s → [p0]
[1:a] → resample 24k mono → fade-in 35ms → [a1]
[p0][a1] concat → libmp3lame
```

**Failed experiment:** `silenceremove` on phrase edges — trimmed speech, total duration ~1.75s.

---

## Fal API arguments (Qwen)

**Clone:**

```json
{
  "audio_url": "<uploaded ref wav>",
  "reference_text": "<Whisper transcript of ref>"
}
```

**TTS:**

```json
{
  "text": "Now we're talking.",
  "language": "English",
  "speaker_voice_embedding_file_url": "<from clone>",
  "prompt": "<FRIEREN_S008_PROMPT_PART1>",
  "reference_text": "<same transcript>"
}
```

---

## Mux filter (dialogue over Kling bed)

From `generate_s008_dialogue.py` → `_mux_dialogue`:

- Background: `[0:a]volume={duck}`
- Dialogue: `adelay={start_ms}|{start_ms},apad=whole_dur={video_dur}`
- `amix` → AAC 192k, video copy

---

## Troubleshooting

| Symptom | Action |
|---------|--------|
| Robotic / wrong timbre | Re-run `--reclone`; verify `.txt` sidecar matches ref wav |
| Rushed two-beat line | Ensure split mode (no `--single-clip`); increase `--pause-sec` |
| Click at pause | Confirm `concat_with_pauses` uses apad+fades (v11+ code) |
| No embedding | Run without `--skip-clone` or `--reclone` |
| Demucs local fail | Use `isolate_vocals_fal.py` only |
| Fern/Stark needed | `--all-speakers` (MiniMax presets) |

---

## Dialogue balloon order (English scan)

```
Fern:    "A grimoire reward was included with the request, though..."
Frieren: "Now we're talking. Let's do it."
Stark:   "Eh?"
```

Frieren-only mux is default; full trio requires `--all-speakers` and manual timing QC on Fern/Stark `start_sec` in `S008_ALL_LINES`.
