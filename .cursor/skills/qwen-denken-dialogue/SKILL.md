---
name: qwen-denken-dialogue
description: Qwen3 Denken dialogue for AI_Animation — elderly mage baritone, denken_jp_qwen_ref, S016 Serie/warden and S017 hometown stems. Use when cloning Denken, writing Denken TTS prompts, or generating Denken lines (not Frieren/Stark).
---

# Qwen3 Denken dialogue (AI_Animation)

## 1. Read the personality guide first

**[`docs/denken-qwen-personality-guide.md`](../../../docs/denken-qwen-personality-guide.md)** — Saito/Phillips casting, B4 balloon map, QC.

**Master pipeline:** [`docs/qwen-voice-pipeline-formula.md`](../../../docs/qwen-voice-pipeline-formula.md)  
**Appearance:** [`docs/denken-appearance-reference.md`](../../../docs/denken-appearance-reference.md)

---

## 2. Ground with story logs

| File | Use |
|------|-----|
| [`Chapter-81/stage_02_shot_list.md`](../../../Chapter-81/stage_02_shot_list.md) | **S016** meet · **S017** hometown |
| [`Chapter-81/stage_03_series_bible.md`](../../../Chapter-81/stage_03_series_bible.md) | § Denken · § S016 |
| [`panels/jap/panel_s015jap.png`](../../../panels/jap/panel_s015jap.png) | **Frieren** meet line only |
| [`panels/jap/panel_s016jap.png`](../../../panels/jap/panel_s016jap.png) | **Denken** Serie / barrier warden |
| [`panels/jap/panel_s017jap.png`](../../../panels/jap/panel_s017jap.png) | **Denken** hometown (`儂`) |

**S016 meet balloon is Frieren.** Denken’s first speech in the B4 sequence is **`panel_s016jap`**.

---

## 3. Engine and ref

| Item | Value |
|------|--------|
| Code | [`scripts/qwen_tts.py`](../../../scripts/qwen_tts.py) (`DENKEN_*`) |
| Generator | [`scripts/generate_s016_denken_dialogue.py`](../../../scripts/generate_s016_denken_dialogue.py) |
| Ref | `Voice Reference/Japanese/Denken/denken_jp_qwen_ref.wav` + `.txt` |
| Registry | `voice_registry.local.json` → `qwen_speaker_embeddings.Denken` |

**Clone:** `reference_text` on **clone only** — **not** on phrase TTS.

**Current ref source:** `VideosMain/this.mp4` → `voice_refs/denkensource.mp4` (EN-dub Denken timbre / Ben Phillips). Replace with JP Saito clip when available.

---

## 4. Default S016 run

```powershell
cd scripts
python generate_s016_denken_dialogue.py --reclone --language Japanese --tag denken_dialogue_v1_ja
```

**Lines:** `ゼーリエに頼み込んでな。` → pause → `最近結界の管理者の任を継いだんだ。`  
**Log:** [`docs/s016-denken-qwen-dialogue-log.md`](../../../docs/s016-denken-qwen-dialogue-log.md)

---

## 5. Prompt rules

**Do:** low baritone, calm court-mage warmth, unhurried, soft trailing `な` / firm but quiet `だ`.  
**Don’t:** frail grandpa croak, shout, teen pitch, villain rasp, Frieren flatness.

**Global:** `DENKEN_JP_TONE` in `qwen_tts.py`.

---

## 6. Related

- Frieren S016: [`qwen-frieren-dialogue`](../qwen-frieren-dialogue/SKILL.md) · [`generate_s016_dialogue.py`](../../../scripts/generate_s016_dialogue.py)
- Lip-sync: [`pixverse-lipsync`](../pixverse-lipsync/SKILL.md)
