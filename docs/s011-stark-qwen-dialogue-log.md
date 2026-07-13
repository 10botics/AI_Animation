# S011 Stark Qwen3 dialogue — project log

**Panel:** [`panels/jap/panel_s011Jap.png`](../panels/jap/panel_s011Jap.png) · still [`panels/eng/panel_s011.png`](../panels/eng/panel_s011.png)  
**Personality:** [`docs/stark-qwen-personality-guide.md`](./stark-qwen-personality-guide.md)  
**Formula:** [`docs/qwen-voice-pipeline-formula.md`](./qwen-voice-pipeline-formula.md)

## Scene (B3)

MCU — Stark alone, gaze **frame left** at gold-to-the-horizon. **Impressed** teen awe (not confused, not sarcastic).

## Dialogue (JP · panel-accurate)

| Line | Japanese (panel) | TTS |
|------|------------------|-----|
| 1 | すごいな… | Phrase 1 |
| 2–3 | 見渡す限りの / 黄金だ。 | **One TTS phrase** — no pause mid-sentence |

**Full:** `すごいな…` + pause + `見渡す限りの黄金だ。` (one breath)

## Iterations

| Tag | Structure | Notes |
|-----|-----------|-------|
| `v1_ja` | 2 phrases | **Sarcastic** — flat `だ` on line 2 |
| `v2_ja` | 3 phrases | Still too sharp / sarcastic edge |
| `v3_ja` | 3 phrases | Soft — unwanted pause before 黄金だ |
| **`v4_ja`** | 2 phrases | Soft + **pause only after すごいな…** |

## Delivery (v2)

- **すごいな…** — warm teen wow, soft **な…**  
- **見渡す限りの** — still impressed, not narrator-flat  
- **黄金だ。** — soft awe **だ**, not deadpan punchline

## Pipeline

```powershell
cd scripts
python generate_s011_stark_dialogue.py --skip-clone --language Japanese --tag stark_dialogue_v4_ja
```

**Deliverable:** `outputs/voice/S011/s011_stark_stark_dialogue_v4_ja_20260603_102959.wav`

## Lip-sync (PixVerse — production)

**Model:** `pixverse` (default in `lipsync_fal.py`) · **Log:** [`docs/pixverse-lipsync-log.md`](pixverse-lipsync-log.md)

Base: `outputs/video/final/S011_seedance-2-i2v-audio_20260527_090828.mp4` · Audio: v4 Stark WAV · `--start-sec 0.85` · **out:** `outputs/video/LipsyncTests/`

*Note: base clip ~5.08s; dialogue ~5.0s @ 0.85s — tail may trim to video length.*

```powershell
cd scripts
python lipsync_fal.py `
  --video "..\outputs\video\final\S011_seedance-2-i2v-audio_20260527_090828.mp4" `
  --audio "..\outputs\voice\S011\s011_stark_stark_dialogue_v4_ja_20260603_102959.wav" `
  --start-sec 0.85 --tag stark_dialogue_v4_ja
```

| Run | Output |
|-----|--------|
| **PixVerse** (production) | `Voice Added/..._stark_dialogue_v4_ja_pixverse_20260603_104245.mp4` |
| MuseTalk (legacy A/B) | `Voice Added/..._musetalk_20260603_103635.mp4` |
| LatentSync | **Failed** — `face_detection_error` on Seedance MCU |

| Constant | Default |
|----------|---------|
| `STARK_S011_DIALOGUE_START_SEC` | `0.85` |
| `STARK_S011_PAUSE_SEC` | `0.6` |

## Note on S012

**S012** (`panel_s012jap`) = **Frieren only** (lore balloons). Stark optional stem there is separate — **this shot’s canon Stark line is S011.**
