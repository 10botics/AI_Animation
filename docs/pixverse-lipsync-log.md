# PixVerse lip-sync — project log

**Production model (2026-06-04+):** [`fal-ai/pixverse/lipsync`](https://fal.ai/models/fal-ai/pixverse/lipsync) via [`scripts/lipsync_fal.py`](../scripts/lipsync_fal.py).

**Skill:** [`.cursor/skills/pixverse-lipsync/SKILL.md`](../.cursor/skills/pixverse-lipsync/SKILL.md)

**Output folder:** `outputs/video/LipsyncTests/` (default `--out-dir`).

---

## Why PixVerse

| Model | Result on AI_Animation |
|-------|------------------------|
| **pixverse** | **Default** — S008 Frieren v14 JA + S011 Stark v4 JA both succeeded |
| musetalk | S011 OK; alternative if PixVerse QC fails |
| latentsync | S011 `face_detection_error` on Seedance profile MCU |
| kling lipsync | Weak on MS / partial profile (S008) |
| heygen-precision | Needs speech in source video (muxed clip, not silent base) |

---

## Inputs (every shot)

1. **Silent base I2V** — e.g. `outputs/video/final/S008_kling-v26-pro_i2v_natural-audio_*.mp4` (no muxed dialogue bed).
2. **Clean dialogue stem** — approved WAV from `outputs/voice/final/S###/`.
3. **`--start-sec`** — same offset as dialogue mux (`FRIEREN_DIALOGUE_START_SEC`, `STARK_S011_DIALOGUE_START_SEC`, etc.).

Script pads audio with leading silence so speech aligns at t=0 for the API.

---

## Canonical command

```powershell
cd scripts
python lipsync_fal.py `
  --video "..\outputs\video\final\<BASE>.mp4" `
  --audio "..\outputs\voice\final\S###\<dialogue>.wav" `
  --start-sec <SEC> `
  --tag <tag>
```

`--model pixverse` is optional (default). Override output: `--out-dir ..\outputs\video\final\Voice Added`.

---

## Runs

| Shot | Tag | start-sec | Output |
|------|-----|-----------|--------|
| **S004** (10s base) | `frieren_dialogue_v1_ja` | `6.0` | `LipsyncTests/..._064358Z_12fps_..._v1_ja_pixverse_20260604_070123.mp4` |
| ~~S004~~ (wrong stem) | `frieren_dialogue_v14_ja_s008_on_s004` | `6.0` | `..._s008_on_s004_pixverse_20260604_065839.mp4` |
| **S004** Frieren | `frieren_dialogue_v2_ja` | `1.2` | `LipsyncTests/..._frieren_dialogue_v2_ja_pixverse_20260604_042931.mp4` |
| **S004** Frieren | `frieren_dialogue_v1_ja_demucs` | `1.2` | `LipsyncTests/..._frieren_dialogue_v1_ja_demucs_pixverse_20260604_043949.mp4` (v1 stem + Fal Demucs) |
| ~~S004 v1~~ | `frieren_dialogue_v1_ja` | `1.2` | `..._v1_ja_pixverse_20260604_041552.mp4` (noisy stem) |
| **S005** Fern | `fern_dialogue_v2_ja` | `1.85` | `LipsyncTests/S005_kling-v26-pro_i2v_anime-audio-12fps_20260527_073521_12fps_20260527_073521_fern_dialogue_v2_ja_pixverse_20260604_081659.mp4` |
| **S005** Fern ROI | `fern_dialogue_v2_ja` | `1.85` | `Voice Added/..._fern_dialogue_v2_ja_pixverse_roi_20260604_082234.mp4` (`lipsync_fal_roi.py --shot S005`) |
| **S004** Fern ROI | `fern_dialogue_v2_ja` | `0.4` | `LipsyncTests/..._fern_dialogue_v2_ja_pixverse_roi_20260604_083835.mp4` (`--shot S004_FERN`) |
| **S004** Frieren ROI | `frieren_dialogue_v2_ja` | `2.497` | `LipsyncTests/..._frieren_dialogue_v2_ja_pixverse_roi_20260604_083923.mp4` (`--shot S004`, 5s base) |
| **S004** dual ROI + mux | `s004_fern_frieren_dual_roi` | Fern `0.4` / Frieren `~2.5` | `Voice Added/..._s004_fern_frieren_dual_roi_20260604_084028_dual_mux_20260604_084028.mp4` (5s base) |
| **S004** Fern mask | `fern_v2_mask` | `1.0` | `LipsyncTests/..._064358Z_..._fern_v2_mask_pixverse_mask_20260604_091524.mp4` |
| **S004** Frieren mask | `frieren_v2_mask` | `3.1` | `LipsyncTests/..._064358Z_..._frieren_v2_mask_pixverse_mask_20260604_091622.mp4` |
| **S004** dual mask + mux | `s004_dual_mask` | Fern `1.0` / Frieren `~3.1` | `LipsyncTests/..._s004_dual_mask_20260604_091719_dual_mux_20260604_091719.mp4` (10s base) |
| **S008** Frieren | `frieren_dialogue_v14_ja` | `2.05` | `LipsyncTests/..._20260604_045001_frieren_dialogue_v14_ja_pixverse_20260604_045309.mp4` (new Kling base) |
| ~~S008~~ | `frieren_dialogue_v14_ja` | `2.05` | `..._20260527_092816_..._pixverse_20260604_040712.mp4` (prior base) |
| **S011** Stark | `stark_dialogue_v4_ja` | `0.85` | `Voice Added/..._stark_dialogue_v4_ja_pixverse_20260603_104245.mp4` (early run; new tests → `LipsyncTests/`) |
| **S014** Frieren | `frieren_dialogue_v1_ja_wary` | `1.0` | `LipsyncTests/S014_kling_100541_silent_for_lipsync_frieren_dialogue_v1_ja_wary_pixverse_20260710_101440.mp4` (wary Kling `100541` stripped) |
| **S012** Stark | `stark_101247_p1` | `2.5` | `LipsyncTests/S012_seedance_091633_silent_for_lipsync_stark_101247_p1_pixverse_20260710_103250.mp4` (p1 only; Seedance stripped) |

---

## Shot-specific logs

| Shot | Dialogue log |
|------|----------------|
| S004 Frieren | [`s004-frieren-qwen-dialogue-log.md`](s004-frieren-qwen-dialogue-log.md) |
| S008 Frieren | [`s008-frieren-qwen-dialogue-log.md`](s008-frieren-qwen-dialogue-log.md) |
| S011 Stark | [`s011-stark-qwen-dialogue-log.md`](s011-stark-qwen-dialogue-log.md) |
| S014 Frieren | [`s014-frieren-qwen-dialogue-log.md`](s014-frieren-qwen-dialogue-log.md) |
| S012 Stark | [`s012-stark-qwen-dialogue-log.md`](s012-stark-qwen-dialogue-log.md) |

---

## A/B (only when PixVerse QC fails)

```powershell
python lipsync_fal.py --model musetalk --video ... --audio ... --start-sec ...
# or: --all-models  (pixverse, musetalk, sync-pro)
```
