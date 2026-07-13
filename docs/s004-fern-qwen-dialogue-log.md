# S004 Fern Qwen3 dialogue — project log

**Personality guide:** [`fern-qwen-personality-guide.md`](./fern-qwen-personality-guide.md)

## Scene

| Item | Detail |
|------|--------|
| **Beat B2** | Fern presents sealed envelope; addresses Frieren |
| **Story source** | [`panels/jap/panel_s004jap.png`](../panels/jap/panel_s004jap.png) |
| **Still** | [`panels/eng/panel_s004.png`](../panels/eng/panel_s004.png) |

## Dialogue (JP · EN)

| Speaker | Japanese | English |
|---------|----------|---------|
| **Fern** | フリーレン様。 | *Lady Frieren.* |
| Frieren | また大陸魔法協会からの依頼？ | *Another request from the Continental Magic Association?* |

**Delivery:** Polite honorific; calm respect; not bubbly.

## Voice ref

| Step | Path |
|------|------|
| Source | `video source/fernsource.mp4` |
| Vocals (optional) | `voice_refs/fern_jp_vocals.wav` (Fal Demucs) |
| Production ref | `Voice Reference/Japanese/Fern/fern_jp_qwen_ref.{wav,txt,json}` |

```powershell
cd scripts
python isolate_vocals_fal.py "..\video source\fernsource.mp4" --out "..\voice_refs\fern_jp_vocals.wav"
python prepare_fern_qwen_ref.py
python generate_s004_fern_dialogue.py --reclone --tag fern_dialogue_v1_ja
```

## Constants

| Constant | Value |
|----------|--------|
| `FERN_S004_PHRASES` | `フリーレン様。` |
| `FERN_S004_DIALOGUE_START_SEC` | `0.4` (before Frieren @ 1.2s) |
| `FERN_S004_LANGUAGE` | `Japanese` |

## Iterations

| Tag | Notes |
|-----|-------|
| `fern_dialogue_v2_ja` | **Use** — ref window @ **40.75s** (12s speech); transcript in `fern_jp_qwen_ref.txt` |
| `fern_dialogue_v1_ja` | Retired — VAD picked **8.5s** gasp (`えっ?` only) |

**Deliverable (v2):** `outputs/voice/final/S004/s004_fern_fern_dialogue_v2_ja_20260604_072740.wav`

**Ref prep:** Demucs → `voice_refs/fern_jp_vocals.wav`; `prepare_fern_qwen_ref.py --skip 20` (default).

## Lip-sync

Fern is **background / not lip-forward** on S004 reframed still — lip-sync optional. Frieren line uses PixVerse per [`s004-frieren-qwen-dialogue-log.md`](./s004-frieren-qwen-dialogue-log.md).
