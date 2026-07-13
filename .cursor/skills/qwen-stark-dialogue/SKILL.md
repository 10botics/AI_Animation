---
name: qwen-stark-dialogue
description: Qwen3 Stark dialogue for AI_Animation — personality, JP delivery, stark_jp_qwen_ref, S008/S011/S012 stems. Use when cloning Stark, writing Stark TTS prompts, or generating Stark lines (not Frieren).
---

# Qwen3 Stark dialogue (AI_Animation)

## 1. Read the personality guide first

**[`docs/stark-qwen-personality-guide.md`](../../../docs/stark-qwen-personality-guide.md)** — manga ch.81 facts, Kobayashi delivery, v1 vs v2 line comparison, QC.

**Master pipeline:** [`docs/qwen-voice-pipeline-formula.md`](../../../docs/qwen-voice-pipeline-formula.md)

---

## 2. Ground with story logs

| File | Use |
|------|-----|
| [`Chapter-81/stage_02_shot_list.md`](../../../Chapter-81/stage_02_shot_list.md) | **S008** `えぇ…` · **S011** awe MCU · **S012** backs (Frieren speech only on JP panel) |
| [`Chapter-81/stage_03_series_bible.md`](../../../Chapter-81/stage_03_series_bible.md) | § Stark · § S012 |
| [`panels/jap/panel_s008jap.png`](../../../panels/jap/panel_s008jap.png) | Canon Stark line on `003.jpg` |
| [`panels/jap/panel_s011Jap.png`](../../../panels/jap/panel_s011Jap.png) | **Canon Stark** — `すごいな…` / `見渡す限りの黄金だ。` |
| [`panels/jap/panel_s012jap.png`](../../../panels/jap/panel_s012jap.png) | **No Stark balloon** — Frieren only |

**Ch.81 golden land:** Stark is **silent** on S012; awe face on **S011**; disbelief **`えぇ…`** on **S008**. Ch.82 adds **quiet** dread / practical question — not a yell.

---

## 3. Engine and ref

| Item | Value |
|------|--------|
| Code | [`scripts/qwen_tts.py`](../../../scripts/qwen_tts.py) (`STARK_*` constants) |
| Generator | [`scripts/generate_s012_stark_dialogue.py`](../../../scripts/generate_s012_stark_dialogue.py) |
| Ref | `Voice Reference/Japanese/Stark/stark_jp_qwen_ref.wav` + `stark_jp_qwen_ref.txt` |
| Registry | `voice_registry.local.json` → `qwen_speaker_embeddings.Stark` |

**Clone:** `reference_text` from `.txt` on **clone only** — **not** on phrase TTS (see formula doc).

**Ref note:** Production JP Stark timbre (`stark_jp_qwen_ref`). Rebuild from `voice_refs/starksource_vocals.wav` if you replace the source clip.

---

## 4. Default S011 run (canon panel line)

```powershell
cd scripts
python generate_s011_stark_dialogue.py --skip-clone --language Japanese --tag stark_dialogue_v2_ja
```

**Line (v4):** `すごいな…` → pause → `見渡す限りの黄金だ。` (lines 2–3 continuous; soft-spoken)  
**Log:** [`docs/s011-stark-qwen-dialogue-log.md`](../../../docs/s011-stark-qwen-dialogue-log.md)

## 5. S012 (optional)

Separate shot — Stark silent on `panel_s012jap`; optional stem via `generate_s012_stark_dialogue.py` only if needed under Frieren lore.

---

## 5. Prompt rules (Stark)

**Do:** mid-low young warrior, breathy surprise, **mutter**, sincere, slightly scared.  
**Don’t:** うわ／スゲー hype, タメ口 bravado, shout, narrator, female pitch, old-man rasp.

**Global tone constant:** `STARK_JP_TONE` in `qwen_tts.py`.

---

## 6. CLI (`generate_s012_stark_dialogue.py`)

| Flag | Purpose |
|------|---------|
| `--skip-clone` / `--reclone` | Registry cache |
| `--language Japanese\|English` | Default Japanese |
| `--start-sec` | Mux offset (default `2.5`) |
| `--single-clip` | One TTS call (legacy v1 style) |
| `--tag` | Filename suffix |

---

## 7. Shots

| Shot | Stark | Script |
|------|-------|--------|
| S008 | **えぇ…** (panel) | MiniMax via `generate_s008_dialogue.py --all-speakers` (not Qwen yet) |
| **S011** | **すごいな…見渡す限りの黄金だ。** | **`generate_s011_stark_dialogue.py`** |
| S012 | Silent (Frieren speaks) | Optional `generate_s012_stark_dialogue.py` |

---

## 8. Lip-sync (PixVerse)

After **S011** v4 WAV is approved: [`pixverse-lipsync`](../pixverse-lipsync/SKILL.md) — `lipsync_fal.py`, `--start-sec 0.85`, base `S011_seedance-2-i2v-audio_20260527_090828.mp4`.

## 9. Related

- Frieren pipeline: [`qwen-frieren-dialogue`](../qwen-frieren-dialogue/SKILL.md)
- Lip-sync: [`pixverse-lipsync`](../pixverse-lipsync/SKILL.md)
- S011 log: [`docs/s011-stark-qwen-dialogue-log.md`](../../../docs/s011-stark-qwen-dialogue-log.md)
- S012 Frieren log: [`docs/s012-frieren-qwen-dialogue-log.md`](../../../docs/s012-frieren-qwen-dialogue-log.md)
