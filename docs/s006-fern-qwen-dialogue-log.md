# S006 Fern Qwen3 dialogue — project log

**Companion:** [`fern-qwen-personality-guide.md`](./fern-qwen-personality-guide.md) · **Script:** [`generate_s006_fern_dialogue.py`](../scripts/generate_s006_fern_dialogue.py)

## Scene

| Item | Detail |
|------|--------|
| **Beat B2** | Camp debate — unofficial Lernen letter |
| **Story** | [`panels/jap/panel_s006jap.png`](../panels/jap/panel_s006jap.png) |
| **Blocking** | Fern by fire; Frieren at tree reading |

## Dialogue (JP)

| Speaker | Japanese |
|---------|----------|
| **Fern** | あまり乗り気じゃありませんね。 |
| Frieren | (two balloons — [`generate_s006_dialogue.py`](../scripts/generate_s006_dialogue.py)) |

## Constants

| Constant | Value |
|----------|-------|
| `FERN_S006_DIALOGUE_START_SEC` | `0.35` (before Frieren @ `0.55`) |
| `FERN_S006_LANGUAGE` | `Japanese` |

## Pipeline

```powershell
cd scripts
python generate_s006_fern_dialogue.py --skip-clone --language Japanese --tag fern_dialogue_v1_ja
```

**Ref:** `Voice Reference/Japanese/Fern/fern_jp_qwen_ref.wav` + `.txt`

## Deliverables

| Tag | WAV |
|-----|-----|
| `fern_dialogue_v1_ja` | `outputs/voice/final/S006/s006_fern_fern_dialogue_v1_ja_20260604_103716.wav` (~2.14s) |

## Lip-sync

**Base I2V (10s):** `outputs/video/final/S006_kling-v26-pro_i2v_anime-audio-12fps_20260605_015128_12fps_20260605_015128.mp4`

Lip-sync: [`pixverse-lipsync`](../.cursor/skills/pixverse-lipsync/SKILL.md) — Fern @ **0.35s**, Frieren @ **0.55s**.
