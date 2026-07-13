---
name: qwen-frieren-dialogue
description: >-
  Clones Frieren English dub voice with Fal Qwen3 TTS, synthesizes scene-grounded dialogue
  (split phrases + mux onto Kling I2V), and manages voice refs/registry. Use for Frieren
  Qwen TTS on Chapter 81 shots (S008 primary), voice clone, reference_text, Demucs vocals,
  or muxing onto outputs/video/final/S008_kling*.mp4 and related shots.
---

# Qwen3 Frieren dialogue (AI_Animation)

## 1. Ground with story logs (always)

Before writing **prompts** or **timing**, read:

| File | Use for S008 |
|------|----------------|
| [`Chapter-81/stage_01_ingest.md`](../../../Chapter-81/stage_01_ingest.md) | **B3** — grimoire bribe escalation after B2 camp unease |
| [`Chapter-81/stage_02_shot_list.md`](../../../Chapter-81/stage_02_shot_list.md) | **S008** blocking, who speaks, props |
| [`Chapter-81/stage_03_series_bible.md`](../../../Chapter-81/stage_03_series_bible.md) | § **S008** dialogue order + voice note |
| [`panels/jap/panel_s008jap.png`](../../../panels/jap/panel_s008jap.png) | **Story source** — JP balloons (primary) |
| [`panels/eng/panel_s008.png`](../../../panels/eng/panel_s008.png) | EN scan layout / still anchor |

**Dialogue (JP · EN):**

| Speaker | Japanese | English (Qwen TTS) |
|---------|----------|-------------------|
| Fern | 報酬の魔導書も一緒に送られてきていますけれども… | *A grimoire reward was included with the request, though...* |
| Frieren | よし。やるか。 | **Default TTS** (two phrases) · EN: `--language English` |
| Stark | えぇ… | *Eh?* |

**Frieren delivery:** dry pivot after Fern’s trailing *though…* — **not** excited (JP is shorter than EN idiom).

**Project log (iterations, refs, v11 baseline):** [`docs/s008-frieren-qwen-dialogue-log.md`](../../../docs/s008-frieren-qwen-dialogue-log.md)

---

## 2. Engine and constants

| Item | Value |
|------|--------|
| Clone | `fal-ai/qwen-3-tts/clone-voice/1.7b` |
| TTS | `fal-ai/qwen-3-tts/text-to-speech/1.7b` |
| Code | [`scripts/qwen_tts.py`](../../../scripts/qwen_tts.py) |
| Registry | `voice_registry.local.json` → `qwen_speaker_embeddings.Frieren` |
| **Must pass** | `reference_text` on **clone + TTS** (`.txt` sidecar of ref wav) |

**Production ref:** `Voice Reference/Japanese/Frieren/frieren_jp_qwen_ref.wav` + `.txt` (from [`fireren Japan.mp4`](../../../fireren%20Japan.mp4) → Fal Demucs → ~24.6s Frieren JP window). **Note:** compilation has no ch.81 S008 line; timbre only. Legacy EN: `Voice Reference/English/Frieren/frieren_1min_qwen_ref.wav`.

**Approved mux baseline:** v11 — see [reference.md](reference.md).

---

## 3. Default pipeline (run this)

From `scripts/` (PowerShell — use `;` not `&&`):

```powershell
python generate_s008_dialogue.py --reclone --tag frieren_dialogue_vNN
```

**What it does:**

1. Loads cached Qwen embedding (or clones if missing / `--reclone`)
2. **`synthesize_s008_frieren()`** — two TTS calls (`language: Japanese` by default):
   - `"よし。"` → `FRIEREN_S008_PROMPT_PART1`
   - `"やるか。"` → `FRIEREN_S008_PROMPT_PART2`
3. **`concat_with_pauses()`** — 0.55s gap, PCM fades, no `anullsrc` clicks
4. Writes **`outputs/voice/S008/*.wav`** + meta JSON (default — **no video mux**)
5. Optional: `--mux --video …S008_kling….mp4` at **`FRIEREN_DIALOGUE_START_SEC` (2.05s)**

**Deliverable:** `outputs/voice/S008/s008_frieren_<tag>_<ts>.wav`

---

## 4. Ref prep (when timbre or clone quality drifts)

```powershell
# Fal Demucs — local Demucs fails on Windows (torchcodec)
python isolate_vocals_fal.py "..\fireren Japan.mp4" --out "..\voice_refs\frieren_jp_vocals.wav"

# Curated window (or hand-set --skip 24.62) + JP Whisper transcript
python prepare_frieren_qwen_ref.py --source ..\voice_refs\frieren_jp_vocals.wav --skip-demucs --scan-seconds 217 --out-wav ..\Voice Reference/Japanese/Frieren/frieren_jp_qwen_ref.wav --out-txt ..\Voice Reference/Japanese/Frieren/frieren_jp_qwen_ref.txt

# Fresh embedding + mux
python generate_s008_dialogue.py --reclone --tag frieren_dialogue_vNN
```

**Legacy timbre A/B:** `voice_refs/frieren_eng_dub_ref_130s_skip0.wav` (v4 iteration — longer, noisier).

---

## 5. Prompt rules (Frieren / Qwen)

**Personality (Rodak EN dub):** flat calm baseline, soft unhurried, dry understated, matter-of-fact. Magic-geek beats = **subtle interest only**.

**S008 scene prompt** lives in `FRIEREN_S008_PROMPT` + per-phrase `FRIEREN_S008_PROMPT_PART1/2`.

**Avoid:** ancient, grandmother, excited, bubbly, loud.

**Override one run:** `--prompt "..."` (single-clip mode only; split mode uses PART1/2 constants).

---

## 6. Phrase timing (critical)

| Issue | Cause | Fix |
|-------|--------|-----|
| Pause before *"Let's do it"* too short | Single TTS clip | Default **split phrases** (do not use `--single-clip`) |
| Click/hitch at pause | `anullsrc` concat (v10) | **`apad` + 35ms fades** in `concat_with_pauses()` (v11+) |
| **"Ta" before each phrase** | Qwen ICL: ref ends on 良かった (った); `reference_text` on every TTS call | **0.5s silence** appended at clone (`append_trailing_silence`); **no** `reference_text` on phrase TTS; `--reclone` |
| Line too short after concat | Aggressive `silenceremove` | **Do not** trim silence on phrases |

**Tune pause:** `--pause-sec 0.7` (longer) or `0.45` (shorter). Default `0.55`.

**Revert to old behavior:** `--single-clip` (one Fal call, compressed pause).

---

## 7. CLI flags (`generate_s008_dialogue.py`)

| Flag | Purpose |
|------|---------|
| `--skip-clone` | Reuse registry embedding |
| `--reclone` | Force new clone from `--ref-wav` |
| `--ref-wav PATH` | Ref override (loads sibling `.txt` for `reference_text`) |
| `--start-sec FLOAT` | Mux offset (default 2.05) |
| `--pause-sec FLOAT` | Inter-phrase silence (default 0.55) |
| `--single-clip` | Disable split-phrase synthesis |
| `--all-speakers` | Fern + Stark via MiniMax |
| `--duck FLOAT` | Background bed level (default 0.35) |
| `--tag STR` | Output filename suffix |
| `--language Japanese\|English` | TTS language (default **Japanese**) |

---

## 8. QC checklist

- [ ] Line matches B3 beat — dry pivot, not celebration
- [ ] Pause between phrases feels natural (~0.5–0.6s)
- [ ] No click/hitch at phrase boundary
- [ ] Timbre acceptable vs v4 reference (if user cares)
- [ ] Dialogue starts ~2.05s — lip/mouth motion acceptable on Kling clip
- [ ] Meta JSON saved under `outputs/voice/S008/`

---

## 10. Lip-sync (PixVerse)

**Skill:** [`pixverse-lipsync`](../pixverse-lipsync/SKILL.md) · **Log:** [`docs/pixverse-lipsync-log.md`](../../../docs/pixverse-lipsync-log.md)

After dialogue WAV is approved, run [`scripts/lipsync_fal.py`](../../../scripts/lipsync_fal.py) — default **pixverse**, output **`outputs/video/LipsyncTests/`**.

```powershell
python lipsync_fal.py `
  --video ..\outputs\video\final\S008_kling-v26-pro_i2v_natural-audio_20260527_092816.mp4 `
  --audio ..\outputs\voice\final\S008\s008_frieren_frieren_dialogue_v14_ja_20260603_050516.wav `
  --start-sec 2.05 --tag frieren_dialogue_v14_ja
```

Silent base Kling + clean stem only. S008 MS / partial face — motion may stay subtle. Fallback: `--model musetalk`.

---

## 9. Extending to other shots

| Shot | Speaker | Skill / script |
|------|---------|----------------|
| S004 | Frieren | [`panels/jap/panel_s004jap.png`](../../../panels/jap/panel_s004jap.png) · `outputs/voice/final/S004/` · [`generate_s004_dialogue.py`](../../../scripts/generate_s004_dialogue.py) |
| S005 | Fern | [`fern-dialogue-s005`](../fern-dialogue-s005/SKILL.md) |
| S006 | Frieren | `outputs/voice/final/S006/` · [`generate_s006_dialogue.py`](../../../scripts/generate_s006_dialogue.py) |
| S006 | Fern | [`generate_s006_fern_dialogue.py`](../../../scripts/generate_s006_fern_dialogue.py) · [`s006-fern-qwen-dialogue-log.md`](../../../docs/s006-fern-qwen-dialogue-log.md) |
| S008 | Frieren | This skill |
| S012 | Frieren | [`panels/jap/panel_s012jap.png`](../../../panels/jap/panel_s012jap.png) · `outputs/voice/final/S012/` · [`generate_s012_dialogue.py`](../../../scripts/generate_s012_dialogue.py) |
| S016 | Frieren | [`panels/jap/panel_s015jap.png`](../../../panels/jap/panel_s015jap.png) · `outputs/voice/final/S016/` · [`generate_s016_dialogue.py`](../../../scripts/generate_s016_dialogue.py) · [`docs/s016-frieren-qwen-dialogue-log.md`](../../../docs/s016-frieren-qwen-dialogue-log.md) |
| S016 | Denken | [`qwen-denken-dialogue`](../qwen-denken-dialogue/SKILL.md) · [`panels/jap/panel_s016jap.png`](../../../panels/jap/panel_s016jap.png) · [`generate_s016_denken_dialogue.py`](../../../scripts/generate_s016_denken_dialogue.py) |
| S012 | Stark (reaction) | [`qwen-stark-dialogue`](../qwen-stark-dialogue/SKILL.md) · [`docs/stark-qwen-personality-guide.md`](../../../docs/stark-qwen-personality-guide.md) |

**Master formula (all characters):** [`docs/qwen-voice-pipeline-formula.md`](../../../docs/qwen-voice-pipeline-formula.md)

1. Add shot phrases + prompts in `qwen_tts.py` (Frieren) or `minimax_dialogue.py` (others).
2. Clone `generate_s008_dialogue.py` / `generate_s005_dialogue.py` pattern; use `dialogue_mux.py`.
3. Document in `stage_03_series_bible.md` § shot + `docs/` log.

---

## Additional resources

- Iteration table, artifacts, errors: [reference.md](reference.md)
- Full project log: [`docs/s008-frieren-qwen-dialogue-log.md`](../../../docs/s008-frieren-qwen-dialogue-log.md)
