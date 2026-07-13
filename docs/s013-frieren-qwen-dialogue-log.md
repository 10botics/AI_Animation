# S013 Frieren Qwen3 dialogue — project log

**Skill:** extends [`qwen-frieren-dialogue`](../.cursor/skills/qwen-frieren-dialogue/SKILL.md)

## Scene

| Item | Detail |
|------|--------|
| **Beat B4** | Great barrier megashot (`004.jpg` row 1) |
| **Story source** | [`panels/jap/panel_s013jap.png`](../panels/jap/panel_s013jap.png) |
| **Bible** | stage_03 **S015-barrier** (crop / still ID **S013**) |
| **Blocking** | Environment-only plate; balloon + chibi omake on manga — VO over vista |

## Dialogue (JP · EN)

| Speaker | Japanese | English |
|---------|----------|---------|
| Frieren | 黄金郷を覆う大結界の中には今もマハトが封印されているのか。 | *Is Macht still sealed inside the great barrier covering the Golden Land?* |

**Delivery:** Calm historian / analytical question — flat, understated; not awe-struck or excited. One manga sentence (no phrase split).

## Pipeline

```powershell
cd scripts
python generate_s013_dialogue.py --skip-clone --language Japanese --tag frieren_dialogue_v1_ja
python generate_s013_dialogue.py --mux --video ..\outputs\video\S013_seedance-2-i2v-audio_20260710_085900.mp4 --skip-clone --tag frieren_dialogue_v1_ja
```

| Constant | Default |
|----------|---------|
| `FRIEREN_S013_DIALOGUE_START_SEC` | `1.0` |
| Line | single balloon (full sentence) |

Voice ref: `frieren_jp_qwen_ref.wav` + `FRIEREN_JP_TONE` in prompt.

## Iterations

| Tag | Notes |
|-----|-------|
| `frieren_dialogue_v1_ja` | First JP run from `panel_s013jap.png` — **~5.66s** WAV |
| `frieren_dialogue_v2_ja_compact` | Compact prompt — still **~5.74s** |
| `frieren_dialogue_v3_ja_lt5s` | Same line; edge trim + light `atempo` → **~4.86s** |

**Deliverable (v3 JA, &lt;5s):** `outputs/voice/final/S013/s013_frieren_frieren_dialogue_v3_ja_lt5s_20260710_171210.wav`

**Mux note:** ~4.86s line fits a **5s** Seedance clip if `start_sec` ≤ **~0.15s** (default now `0.35` — prefer `--start-sec 0.1` or `--duration 10` I2V for headroom).
