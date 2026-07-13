---
name: pixverse-lipsync
description: >-
  Fal PixVerse lip-sync on AI_Animation I2V clips — default production model
  (fal-ai/pixverse/lipsync). Use when lip-syncing dialogue onto Kling/Seedance
  video, lipsync_fal.py, LipsyncTests outputs, S008 Frieren or S011 Stark mouth
  motion, or comparing to musetalk/latentsync.
---

# PixVerse lip-sync (AI_Animation)

## Production default

| Item | Value |
|------|--------|
| **Model** | `pixverse` → `fal-ai/pixverse/lipsync` |
| **Script** | [`scripts/lipsync_fal.py`](../../../scripts/lipsync_fal.py) |
| **Log** | [`docs/pixverse-lipsync-log.md`](../../../docs/pixverse-lipsync-log.md) |
| **Output** | `outputs/video/LipsyncTests/` (default) |

Do **not** change `--model` unless PixVerse QC fails; then try `musetalk`.

---

## Inputs

| Input | Rule |
|-------|------|
| **Video** | **Silent** base I2V from `outputs/video/final/` — no muxed Qwen dialogue track |
| **Audio** | Approved stem: `outputs/voice/final/S###/*.wav` |
| **start-sec** | Same as dialogue mux for that shot (script prepends silence) |

**Wrong:** muxed MP4 as `--video` with separate `--audio` (double bed). **Wrong:** HeyGen on silent base (needs speech in source).

---

## Command template

```powershell
cd scripts
python lipsync_fal.py `
  --video "..\outputs\video\final\<BASE_I2V>.mp4" `
  --audio "..\outputs\voice\final\S###\<dialogue_stem>.wav" `
  --start-sec <SEC> `
  --tag <tag_suffix>
```

`--model` omitted → **pixverse**. Outputs: `{video_stem}_{tag}_pixverse_{timestamp}.mp4` in `--out-dir` (default `LipsyncTests/`). Run metadata → `outputs/video/meta/lipsync/{same_stem}.json` (not beside the MP4).

Ship after QC: copy **MP4 only** to `outputs/video/final/Voice Added/` or shot folder.

---

## Shot timing (Chapter 81)

| Shot | start-sec | Constant / log |
|------|-----------|----------------|
| **S004** Frieren | `1.2` | `FRIEREN_S004_DIALOGUE_START_SEC` · [`s004-frieren-qwen-dialogue-log.md`](../../../docs/s004-frieren-qwen-dialogue-log.md) |
| **S008** Frieren | `2.05` | `FRIEREN_DIALOGUE_START_SEC` · [`s008-frieren-qwen-dialogue-log.md`](../../../docs/s008-frieren-qwen-dialogue-log.md) |
| **S011** Stark | `0.85` | `STARK_S011_DIALOGUE_START_SEC` · [`s011-stark-qwen-dialogue-log.md`](../../../docs/s011-stark-qwen-dialogue-log.md) |

Base videos:

- S004: `S004_kling-v26-pro_i2v_anime-audio-12fps_20260527_065906_12fps_20260527_065906.mp4`
- S008: `S008_kling-v26-pro_i2v_natural-audio_20260604_045001.mp4`
- S011: `S011_seedance-2-i2v-audio_20260527_090828.mp4`

---

## Workflow

1. **Approve dialogue WAV** (Qwen skill: `qwen-frieren-dialogue` / `qwen-stark-dialogue`).
2. Confirm **mux start-sec** (waveform or prior mux meta).
3. Run `lipsync_fal.py` (defaults → PixVerse + `LipsyncTests`).
4. QC mouth vs profile (MS / partial face = subtle motion is OK).
5. Log path in shot dialogue log + [`pixverse-lipsync-log.md`](../../../docs/pixverse-lipsync-log.md).

---

## Fallbacks (A/B only)

| Model | When |
|-------|------|
| **musetalk** | PixVerse mouth too weak or artifacting |
| **sync-pro** | Frontal live-action–like face |
| **latentsync** | Often fails `face_detection_error` on anime MCU (S011) |
| **kling** | Same vendor as I2V; weak on S008 profile |
| **heygen-*** | Requires **muxed** `--dialogue-video` with audible speech |

```powershell
python lipsync_fal.py --model musetalk --video ... --audio ... --start-sec ...
python lipsync_fal.py --all-models --video ... --audio ...   # pixverse + musetalk + sync-pro
```

---

## API notes

- Args: `video_url`, `audio_url` (Fal upload from local files).
- No `sync_mode` (Sync.so only).
- Padded MP3 built in temp; not committed.

---

## Related

- Voice pipeline: [`docs/qwen-voice-pipeline-formula.md`](../../../docs/qwen-voice-pipeline-formula.md)
- Frieren TTS: [`qwen-frieren-dialogue`](../qwen-frieren-dialogue/SKILL.md)
- Stark TTS: [`qwen-stark-dialogue`](../qwen-stark-dialogue/SKILL.md)
