# S012 Frieren Qwen3 dialogue — project log

**Skill:** extends [`qwen-frieren-dialogue`](../.cursor/skills/qwen-frieren-dialogue/SKILL.md)  
**Master formula:** [`docs/qwen-voice-pipeline-formula.md`](./qwen-voice-pipeline-formula.md) · **Stark S012:** [`docs/s012-stark-qwen-dialogue-log.md`](./s012-stark-qwen-dialogue-log.md)

## Scene

| Item | Detail |
|------|--------|
| **Beat B3** | Gilt Weise reveal; Macht / El Dorado exposition |
| **Story source** | [`panels/jap/panel_s012jap.png`](../panels/jap/panel_s012jap.png) |
| **Still** | [`panels/eng/panel_s012.png`](../panels/eng/panel_s012.png) |

## Speaker attribution (corrected 2026-06-03)

On **`panel_s012jap.png`**, **all three speech balloons** have tails pointing to **Frieren** (center). Fern and Stark are too young to know 50-year-old Macht history; the left bubble’s *噂には聞いていたけど…* is first-person Frieren exposition, not Fern.

EN scan layout (`panel_s012.png`) often mis-labels the left bubble as Fern — **ignore for TTS**.

## Dialogue (JP · manga RTL) — all Frieren

Right column top→bottom, then left bubble:

| TTS | Japanese (panel-accurate) |
|-----|---------------------------|
| 1 | 城塞都市ヴァイゼ。50年前に七崩賢黄金郷のマハトの手によって一瞬で黄金に変えられた悲運の都市。 |
| 2 | 噂には聞いていたけど、まさか大陸魔法協会が管理していた**だ**なんてね。 |

**Grammar / 会話調 (2026-06-03):**
- **TTS 1:** Manga uses two appositive fragments (名詞句＋説明). Written JP is fine; spoken aloud needs **one breath** + 会話調 prompt (not 朗読). Optional anime rewrite would add は/という — not in balloons.
- **TTS 2:** **だなんてね** is natural spoken surprise (was missing だ in v5). Panel: 管理していた**だ**なんてね.

## Iterations

| Tag | Notes |
|-----|-------|
| `v5_ja` | Missing **だ** on line 2; speech too 朗読-like |
| **`v6_ja`** | Panel **だ** restored; 会話調 prompts |

**Deliverable:** `outputs/voice/final/S012/s012_frieren_frieren_dialogue_v6_ja_20260603_072738.wav`

## Pipeline

```powershell
cd scripts
python generate_s012_dialogue.py --skip-clone --language Japanese --tag frieren_dialogue_v2_ja
```

| Constant | Default |
|----------|---------|
| `FRIEREN_S012_DIALOGUE_START_SEC` | `1.0` |
| `FRIEREN_S012_PAUSE_SEC` | `0.55` |

**Mux:** Kling **10s** minimum; 5s clip will truncate.
