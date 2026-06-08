---
name: fern-dialogue-s005
description: >-
  Synthesizes Fern S005 letter-read dialogue with MiniMax TTS (split phrases + mux onto
  Kling I2V). Use for S005, Fern dialogue, Lernen personal request line, MiniMax Lovely_Girl,
  or muxing onto outputs/video/final/S005_kling*.mp4. Not Frieren — see qwen-frieren-dialogue.
---

# MiniMax Fern dialogue — S005 (AI_Animation)

## 1. Ground with story logs (always)

| File | Use for S005 |
|------|----------------|
| [`Chapter-81/stage_01_ingest.md`](../../../Chapter-81/stage_01_ingest.md) | **B2** — unofficial letter, quest hook |
| [`Chapter-81/stage_02_shot_list.md`](../../../Chapter-81/stage_02_shot_list.md) | **S005** CU Fern + Lernen telegraph |
| [`Chapter-81/stage_03_series_bible.md`](../../../Chapter-81/stage_03_series_bible.md) | § **S005** |
| [`panels/eng/panel_s005.png`](../../../panels/eng/panel_s005.png) | Balloon + blocking |

**Fern line:** *"Nay, this appears to be a personal request from First-Class Mage Lernen-sama."*

Formal letter read — measured, quiet unease, respectful. **Not** Frieren (use [`qwen-frieren-dialogue`](../qwen-frieren-dialogue/SKILL.md) for S008).

**Log:** [`docs/s005-fern-dialogue-log.md`](../../../docs/s005-fern-dialogue-log.md)

---

## 2. Engine and constants

| Item | Value |
|------|--------|
| TTS | `fal-ai/minimax-tts/text-to-speech` |
| Code | [`scripts/minimax_dialogue.py`](../../../scripts/minimax_dialogue.py) |
| Pipeline | [`scripts/generate_s005_dialogue.py`](../../../scripts/generate_s005_dialogue.py) |
| Mux | [`scripts/dialogue_mux.py`](../../../scripts/dialogue_mux.py) |
| Default voice | `Lovely_Girl` preset |
| Clone | `--character Fern` → `voice_registry.local.json` |

| Constant | Default |
|----------|---------|
| `FERN_S005_DIALOGUE_START_SEC` | `1.85` |
| `FERN_S005_PAUSE_SEC` | `0.45` |
| `FERN_S005_SPEED` | `0.95` |
| `FERN_S005_EMOTION` | `neutral` |

---

## 3. Default pipeline

```powershell
cd scripts
python generate_s005_dialogue.py --tag fern_dialogue_vNN
```

1. MiniMax TTS — two phrases (split) or `--single-clip`
2. `concat_with_pauses()` from `qwen_tts` (fade + apad — same as S008 v11)
3. Mux at **1.85s** onto latest `S005_kling*.mp4`
4. Output: `outputs/video/final/*_fern_dialogue_*_.mp4` + meta in `outputs/voice/S005/`

**Base video:** `outputs/video/final/S005_kling-v26-pro_i2v_anime-audio-12fps_20260527T073521Z_12fps_20260527T073521Z.mp4`

---

## 4. Optional Fern voice clone

```powershell
python minimax_voice_clone.py --character Fern --audio "..\voice_refs\fern_ref.wav"
python generate_s005_dialogue.py --character Fern --tag fern_dialogue_clone_v1
```

---

## 5. Phrase timing

Same rules as S008 v11:

- **Split default** — pause before *"from First-Class Mage Lernen-sama."*
- **`--pause-sec`** to tune (0.35–0.6s typical)
- **`--single-clip`** — one MiniMax call, compressed mid-line pause
- Join uses **apad + fades** — never `anullsrc`

---

## 6. CLI flags

| Flag | Purpose |
|------|---------|
| `--video PATH` | Override base Kling MP4 |
| `--character Fern` | Cloned MiniMax voice |
| `--voice-id ID` | Preset or custom_voice_id |
| `--start-sec FLOAT` | Mux offset (default 1.85) |
| `--pause-sec FLOAT` | Inter-phrase gap |
| `--speed` / `--emotion` | MiniMax voice_setting |
| `--single-clip` | Disable split phrases |
| `--duck FLOAT` | Background bed (default 0.35) |
| `--tag STR` | Output suffix |

---

## 7. QC checklist

- [ ] Formal, measured Fern — not bubbly or panicked
- [ ] Lernen-sama honorific clear
- [ ] Pause before naming Lernen feels natural
- [ ] No click at phrase join
- [ ] Start time fits CU read (~1.5–2.5s on 10s clip)
- [ ] Meta JSON in `outputs/voice/S005/`

---

## Related

- Frieren S008 (Qwen): [`qwen-frieren-dialogue`](../qwen-frieren-dialogue/SKILL.md)
- S008 concat implementation: [`qwen_tts.concat_with_pauses`](../../../scripts/qwen_tts.py)
