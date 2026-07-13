# S014 Frieren Qwen3 dialogue — project log

**Skill:** extends [`qwen-frieren-dialogue`](../.cursor/skills/qwen-frieren-dialogue/SKILL.md)

## Scene

| Item | Detail |
|------|--------|
| **Beat B4** | After great barrier (`004.jpg` row 1) — MCU reaction |
| **Story source** | [`panels/jap/panel_s014jap.png`](../panels/jap/panel_s014jap.png) |
| **stage_02** | Frieren **calm/surprised** — barrier job; request to assist warden |
| **Blocking** | MCU face + scarf; forest BG; balloon lower frame |

## Dialogue (JP · EN)

| # | Japanese | English |
|---|----------|---------|
| 1 | しかし驚いたよ。 | *Still, I'm surprised.* |
| 2 | 依頼書には大陸魔法協会から派遣された結界の管理者を手伝うようにとあったけど。 | *The request said to help the barrier warden dispatched by the Continental Magic Association, though.* |

**Delivery:** Mild dry surprise only (`驚いたよ` ≠ excited). Flat calm historian/practical tone; soft trailing `けど`. Matches stage_02 **calm/surprised** + Rodak-style understatement (no bubbly, no grandmother).

## Pipeline

```powershell
cd scripts
python generate_s014_dialogue.py --skip-clone --language Japanese --tag frieren_dialogue_v1_ja
```

| Constant | Default |
|----------|---------|
| `FRIEREN_S014_DIALOGUE_START_SEC` | `1.0` |
| `FRIEREN_S014_PAUSE_SEC` | `0.5` |
| Split | two phrases (two manga sentences) |

## Iterations

| Tag | Notes |
|-----|-------|
| `frieren_dialogue_v1_ja` | First JP run from `panel_s014jap.png` — two-phrase calm/surprised — **~9.0s** WAV |

**Deliverable (v1 JA):** `outputs/voice/final/S014/s014_frieren_frieren_dialogue_v1_ja_20260710_091920.wav`

**Mux:** Existing Final Kling is ~10s — use `--start-sec 0.8` or trim slightly if needed.

## Lip-sync (PixVerse)

**Current (wary Kling `100541`, ambience stripped):**

```powershell
# silent workfile from anime_audio Kling
ffmpeg -y -i ..\outputs\video\S014_kling-v26-pro_i2v_anime_audio_12fps_20260710_100541.mp4 -c:v copy -an ..\outputs\video\S014_kling_100541_silent_for_lipsync.mp4
python lipsync_fal.py `
  --video ..\outputs\video\S014_kling_100541_silent_for_lipsync.mp4 `
  --audio ..\outputs\voice\S014\s014_frieren_frieren_dialogue_v1_ja_20260710_091920.wav `
  --start-sec 1.0 --tag frieren_dialogue_v1_ja_wary
```

**Deliverable:** `outputs/video/LipsyncTests/S014_kling_100541_silent_for_lipsync_frieren_dialogue_v1_ja_wary_pixverse_20260710_101440.mp4`

Prior (silent Kling `093147`): `LipsyncTests/..._093147Z_frieren_dialogue_v1_ja_pixverse_20260710_093553.mp4`
