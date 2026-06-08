# S012 Stark Qwen3 dialogue — project log

**Formula:** [`docs/qwen-voice-pipeline-formula.md`](./qwen-voice-pipeline-formula.md)  
**Personality:** [`docs/stark-qwen-personality-guide.md`](./stark-qwen-personality-guide.md) · skill [`qwen-stark-dialogue`](../.cursor/skills/qwen-stark-dialogue/SKILL.md)  
**Frieren S012 (same shot):** [`docs/s012-frieren-qwen-dialogue-log.md`](./s012-frieren-qwen-dialogue-log.md)

> **Stark’s canon gold-awe line is [S011](./s011-stark-qwen-dialogue-log.md)** (`panel_s011Jap`), not S012. S012 Stark stems below are optional only.

## Scene

| Item | Detail |
|------|--------|
| **Beat B3** | Gilt Weise reveal; Frieren lore on `panel_s012jap` |
| **Story source** | [`panels/jap/panel_s012jap.png`](../panels/jap/panel_s012jap.png) |
| **Stark on panel** | Present (right back); **no speech balloon** |

## Line attribution

| Speaker | Source | Japanese |
|---------|--------|----------|
| Frieren | Manga balloons (RTL) | See Frieren log — 2 phrases |
| **Frieren** | `panel_s012jap` (all balloons) | See [`s012-frieren-qwen-dialogue-log.md`](./s012-frieren-qwen-dialogue-log.md) |
| **Stark** | **No balloon** — impressed stem only | v4: `すごい…` + `全部、金色なんだ…` |
| **Not Stark’s line** | Left bubble `噂には…だなんてね` | **Frieren** (tail + lore) — do not give to Stark |

*Not in manga on S012 — stem for animation. See personality guide for v1 vs v2 rationale.*

## Voice reference chain

| Step | File | Notes |
|------|------|-------|
| Source video | `voice_refs/starksource.mp4` | ~2:16 |
| Full extract | `voice_refs/starksource.wav` | mono 44.1 kHz |
| Demucs (Fal) | `voice_refs/starksource_vocals.wav` | `isolate_vocals_fal.py` |
| Qwen window | `Voice Reference/Japanese/Stark/stark_jp_qwen_ref.wav` | **12.0s** @ **16.5s** (VAD) |
| Transcript | `Voice Reference/Japanese/Stark/stark_jp_qwen_ref.txt` | Whisper on ref window |
| Meta | `Voice Reference/Japanese/Stark/stark_jp_qwen_ref.json` | `prepare_frieren_qwen_ref.py` |

**Clone:** `reference_text` from `.txt` on clone only; phrase TTS **without** `reference_text` (ICL 「た」fix).

## Prompt

`STARK_S012_PROMPT` + `STARK_JP_TONE` in `scripts/qwen_tts.py` — young warrior, short awe, not shouting.

## Iterations

| Tag | Line | Notes |
|-----|------|-------|
| `v1_ja` | `うわ…全部、金色だな。` | Too brash — retired |
| `v2_ja` | `…本当に、全部黄金か。` | Sarcastic — retired |
| `v3_ja` | `えっ…` + `すごい…` | Too **confused** — retired |
| **`v4_ja`** | `すごい…` + `全部、金色なんだ…` | **Impressed** teen; no えっ |

**Deliverable:** `outputs/voice/S012/s012_stark_stark_dialogue_v4_ja_20260603T101933Z.wav`

## Pipeline

```powershell
cd scripts
python isolate_vocals_fal.py "..\voice_refs\starksource.mp4" --out "..\voice_refs\starksource_vocals.wav"
python prepare_frieren_qwen_ref.py --source "..\voice_refs\starksource_vocals.wav" --skip-demucs `
  --out-wav "..\Voice Reference\Japanese\Stark\stark_jp_qwen_ref.wav" --out-txt "..\Voice Reference\Japanese\Stark\stark_jp_qwen_ref.txt" `
  --out-meta "..\Voice Reference\Japanese\Stark\stark_jp_qwen_ref.json"
python generate_s012_stark_dialogue.py --reclone --language Japanese --tag stark_dialogue_v1_ja
```

| Constant | Default |
|----------|---------|
| `STARK_S012_DIALOGUE_START_SEC` | `2.5` (under Frieren monologue on mux) |
| Ref | `stark_jp_qwen_ref.wav` |

**Mux:** Optional `--mux`; layer under Frieren stem with offset ~2.5s+ (QC lip on WS backs).
