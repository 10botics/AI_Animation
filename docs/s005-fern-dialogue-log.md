# S005 Fern dialogue — project log

**Status (2026-06-04):** **Qwen3 Fern** (JP from `panel_s005jap.png`) — primary. MiniMax remains optional fallback.  
**Skill:** [`.cursor/skills/fern-dialogue-s005/SKILL.md`](../.cursor/skills/fern-dialogue-s005/SKILL.md) · personality [`fern-qwen-personality-guide.md`](./fern-qwen-personality-guide.md)

---

## Scene context

| Source | Detail |
|--------|--------|
| **Beat B2** | Unofficial letter / quest hook — unease vs obligation |
| **S005** | Fern CU profile; letter in hands; Lernen memory telegraph BG |
| **Panel** | `002.jpg` row 3 right → `panels/eng/panel_s005.png` |
| **Read order** | After S004 (Continental Magic Association beat) |

**Dialogue (JP · `panel_s005jap.png`):**

| Balloon line | Japanese | TTS clip |
|-------------|----------|----------|
| 1 | いえ、 | clip 1 |
| 2 + 3 | 一級魔法使いレルネン様からの + 個人的な依頼のようです。 | **one clip** (no pause between 2↔3) |

**Pause:** `0.5s` **only after いえ、** — v1 wrongly used 3 clips × 0.5s gaps.

**English scan:** *Nay, this appears to be a personal request from First-Class Mage Lernen-sama.*

**Delivery:** Formal letter read; quiet weight; respectful *-sama*; not alarmed, not cheerful.

**Base video:** `outputs/video/final/S005_kling-v26-pro_i2v_anime-audio-12fps_20260527T073521Z_12fps_20260527T073521Z.mp4` (~10s).  
**Default mux start:** `1.85s` (`FERN_S005_DIALOGUE_START_SEC`).

---

## Engine (Qwen — default)

| Item | Value |
|------|--------|
| Clone / TTS | `fal-ai/qwen-3-tts/*` |
| Ref | `Voice Reference/Japanese/Fern/fern_jp_qwen_ref.wav` |
| Script | `scripts/generate_s005_fern_dialogue.py` |
| Pause | `0.5s` (`FERN_S005_PAUSE_SEC`) |
| Mux start | `1.85s` (`FERN_S005_DIALOGUE_START_SEC`) |

| Tag | Notes |
|-----|-------|
| `fern_dialogue_v2_ja` | **Use** — 2 TTS clips; pause **only** after いえ、 |
| ~~v1_ja~~ | 3 clips + 0.5s between **every** phrase (wrong gap between 2↔3) |

**Deliverable (v2):** `outputs/voice/final/S005/s005_fern_fern_dialogue_v2_ja_20260604T081410Z.wav` (~5.8s vs v1 ~6.3s)

## Lip-sync (PixVerse)

```powershell
python lipsync_fal.py `
  --video "..\outputs\video\final\S005_kling-v26-pro_i2v_anime-audio-12fps_20260527T073521Z_12fps_20260527T073521Z.mp4" `
  --audio "..\outputs\voice\final\S005\s005_fern_fern_dialogue_v2_ja_20260604T081410Z.wav" `
  --start-sec 1.85 --tag fern_dialogue_v2_ja
```

| Run | Output |
|-----|--------|
| v2_ja + PixVerse (full frame) | `..._fern_dialogue_v2_ja_pixverse_20260604T081659Z.mp4` |
| v2_ja + PixVerse **ROI** | `..._fern_dialogue_v2_ja_pixverse_roi_20260604T082234Z.mp4` — `lipsync_fal_roi.py --shot S005` |

## Engine (MiniMax — fallback)

| Item | Value |
|------|--------|
| TTS | `fal-ai/minimax-tts/text-to-speech` |
| Script | `scripts/generate_s005_dialogue.py` |

---

## Scripts

| Script | Role |
|--------|------|
| `scripts/generate_s005_dialogue.py` | Main S005 pipeline |
| `scripts/minimax_dialogue.py` | Fern S005 constants + MiniMax synth |
| `scripts/dialogue_mux.py` | Shared ffmpeg mux (S005 + S008) |
| `scripts/minimax_voice_clone.py` | Optional Fern clone |
| `scripts/minimax_tts.py` | One-off MiniMax lines |

---

## Commands

```powershell
cd scripts
python generate_s005_fern_dialogue.py --skip-clone --tag fern_dialogue_v1_ja
python generate_s005_fern_dialogue.py --mux --tag fern_dialogue_v1_ja
# MiniMax fallback:
python generate_s005_dialogue.py --tag fern_dialogue_v1
```

---

## Shared infrastructure (from S008)

- `dialogue_mux.latest_shot_video("S005")` — finds latest Kling MP4
- `qwen_tts.concat_with_pauses()` — reused for smooth phrase joins (v11 fix)

---

## Related shots (B2 camp letter arc)

| Shot | Speaker | Line topic |
|------|---------|------------|
| S004 | Frieren | また大陸魔法協会からの依頼？ (Qwen — [`s004-frieren-qwen-dialogue-log.md`](s004-frieren-qwen-dialogue-log.md)) |
| **S005** | **Fern** | Personal request from Lernen |
| S006 | Fern pressing | Unofficial request debate |
| S008 | Frieren | Grimoire bribe pivot (Qwen) |
