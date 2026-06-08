# S008 Frieren Qwen3 dialogue — project log

**Status (2026-06-02):** Approved baseline — **v11** split-phrase TTS + smooth concat.  
**Best deliverable (EN ref v11):** `..._frieren_dialogue_v11_20260602T103647Z.mp4`  
**JP ref trial (v12):** `..._frieren_dialogue_v12_20260603T045232Z.mp4` (clone from `fireren Japan.mp4`, EN line text)  
**JP TTS (v13_ja):** `..._frieren_dialogue_v13_ja_*.wav` — had ICL **"ta"** prefix each phrase (ref ended 良かった)  
**JP TTS (v14_ja):** `outputs/voice/final/S008/s008_frieren_frieren_dialogue_v14_ja_20260603T050516Z.wav` — ref tail silence + no `reference_text` on phrase TTS

**Skill:** [`.cursor/skills/qwen-frieren-dialogue/SKILL.md`](../.cursor/skills/qwen-frieren-dialogue/SKILL.md)

---

## Goal

Replace Kling native dialogue on **S008** with **English dub–matched Frieren** cloned via **Fal Qwen3 TTS 1.7B**, grounded in chapter story logs (B3 grimoire bribe) and Mallorie Rodak–style flat EN delivery, muxed onto the approved Kling I2V clip.

---

## Scene context (from Stages 1–3)

| Source | Detail |
|--------|--------|
| **Beat B3** (`stage_01_ingest.md`) | Grimoire reward escalates the Lernen request after B2 camp unease |
| **S008** (`stage_02_shot_list.md`) | Daytime camp; Fern back to camera with open grimoire; Frieren toward book; Stark rear left |
| **Panel** | `003.jpg` top tier → `panels/eng/panel_s008.png` |
| **Dialogue order** | Fern: *"A grimoire reward was included with the request, though…"* → Frieren → Stark: *"Eh?"* |

**Frieren line (English scan):**

> Now we're talking. Let's do it.

**Delivery:** Dry idiom pivot + pragmatic yes — **not** bubbly; subtle magic-geek spark only. Contrasts B2 indifference (S004–S006). Not golden-Weise awe (S010+).

**Base video (current):** `outputs/video/final/S008_kling-v26-pro_i2v_natural-audio_20260604T045001Z.mp4` — Kling rerun: stable Frieren grimoire hands, Stark face frozen (no blink).  
**Previous base:** `..._natural-audio_20260527T092816Z.mp4` (hand/blink drift).  
**Mux start:** `FRIEREN_DIALOGUE_START_SEC = 2.05` in `scripts/qwen_tts.py`.

---

## Engine choice

| Backend | Outcome |
|---------|---------|
| MiniMax TTS | Early tests; replaced per user direction |
| F5-TTS | Compared in `compare_s008_frieren_voices.py` |
| **Qwen3 1.7B (Fal)** | **Standard** — `clone-voice/1.7b` + `text-to-speech/1.7b` |

**Critical API params:** pass **`reference_text`** on **both** clone and TTS (Whisper transcript of ref clip). Biggest quality lever after ref curation.

---

## Voice reference evolution

| Version | Path | Notes |
|---------|------|-------|
| v4 (user QC favorite on timbre) | `voice_refs/frieren_eng_dub_ref_130s_skip0.wav` | 130s from dub compilation webm start |
| v6 curated | `voice_refs/frieren_qwen_ref_15s.wav` + `.txt` | VAD window from dub comp ~32.5s |
| **JP source (current)** | `fireren Japan.mp4` (repo root) | ~217s JP dub compilation |
| **Demucs vocals** | `voice_refs/frieren_jp_vocals.wav` | Fal Demucs |
| **Production ref (v12+)** | `Voice Reference/Japanese/Frieren/frieren_jp_qwen_ref.wav` + `.txt` | 12s @ 24.62s Frieren solo; JP `reference_text` |
| **Story panel** | `panels/jap/panel_s008jap.png` | JP balloons — see `FRIEREN_S008_DIALOGUE` in `qwen_tts.py` |
| **Legacy 1min EN** | `voice Frieren1min.mp4` → `frieren_1min_qwen_ref.wav` | v7–v11 timbre |

**Registry:** `voice_registry.local.json` (gitignored) → `qwen_speaker_embeddings.Frieren`

---

## Prompts (`scripts/qwen_tts.py`)

**General Frieren (`DEFAULT_PROMPT`):** young adult elf, subdued EN dub, flat calm, dry understated, never loud/bubbly.

**S008 scene (`FRIEREN_S008_PROMPT`):** camp B3 pivot after grimoire mention; dry deadpan; two-beat line.

**Split-phrase micro-prompts (default pipeline):**

- `FRIEREN_S008_PROMPT_PART1` — idiom *"Now we're talking."*
- `FRIEREN_S008_PROMPT_PART2` — agreement *"Let's do it."*

**Avoid in Qwen prompts:** ancient, grandmother, excited, bubbly.

---

## Phrase timing fix (v10 → v11)

**Problem:** Single TTS call compresses the period pause; sounds rushed.

**Fix:** `synthesize_s008_frieren()` — two Fal TTS calls + `concat_with_pauses()`:

- Default gap: **`FRIEREN_S008_PAUSE_SEC = 0.55`**
- PCM normalize → **35ms fade** at join → **`apad`** silence (not `anullsrc` — caused hitch/click in v10)
- Single MP3 encode (`libmp3lame -q:a 2`)

**Do not use:** `silenceremove` on phrase tails (over-trims speech in testing).

---

## Scripts

| Script | Role |
|--------|------|
| `scripts/qwen_tts.py` | Clone, synthesize, S008 split helper, registry |
| `scripts/generate_s008_dialogue.py` | **Main pipeline** — TTS + mux onto latest S008 Kling MP4 |
| `scripts/prepare_frieren_qwen_ref.py` | VAD 10–15s window, optional Demucs, Fal Whisper → `.txt` |
| `scripts/isolate_vocals_fal.py` | Fal Demucs from video/audio |
| `scripts/generate_s008_frieren_v6.py` | Tier-1 ref + reference_text iteration |
| `scripts/generate_s008_frieren_v7.py` | 1min Demucs vocal chain |
| `scripts/generate_s008_frieren_iterations.py` | Batch ref/prompt/timing variants |
| `scripts/compare_s008_frieren_voices.py` | MiniMax / F5 / Qwen A/B (historical) |

---

## Iteration history (final outputs)

| Tag | File pattern | Notes |
|-----|--------------|-------|
| v4 | `outputs/voice/S008/iterations/S008_frieren_qwen_v4_*.mp4` | 130s ref; user timbre reference |
| v6–v7 | `iterations/S008_frieren_qwen_v6|v7_*.mp4` | Curated ref / 1min vocals |
| v8–v9 | `*_frieren_dialogue_v8|v9_*.mp4` | Scene-grounded prompt |
| v10 | `*_frieren_dialogue_v10_*.mp4` | Split phrases; **hitch at join** |
| **v11** | `*_frieren_dialogue_v11_20260602T103647Z.mp4` | **Approved** — smooth concat |

Approved WAV: `outputs/voice/final/S008/` · drafts/meta: `outputs/voice/S008/`

---

## Standard commands (PowerShell)

```powershell
cd scripts

# 1) Optional: refresh vocals from 1min source
python isolate_vocals_fal.py "..\voice Frieren1min.mp4" --out "..\voice_refs\frieren_1min_vocals.wav"

# 2) Optional: rebuild 12s Qwen ref + reference_text
python prepare_frieren_qwen_ref.py --source ..\voice_refs\frieren_1min_vocals.wav --skip-demucs --out-wav ..\Voice Reference/English/Frieren/frieren_1min_qwen_ref.wav --out-txt ..\Voice Reference/English/Frieren/frieren_1min_qwen_ref.txt

# 3) Produce dialogue mux (skip clone if embedding cached)
python generate_s008_dialogue.py --ref-wav ..\Voice Reference/English/Frieren/frieren_1min_qwen_ref.wav --skip-clone --tag frieren_dialogue_vNN

# Tune pause only (re-splice if p0/p1 stems exist — see skill)
python generate_s008_dialogue.py --pause-sec 0.7 --skip-clone --tag frieren_dialogue_vNN
```

**Fern/Stark lines:** `--all-speakers` uses MiniMax presets (not Qwen).

---

## Known issues / platform notes

- **Local Demucs** on Windows: torchcodec save error → use **`isolate_vocals_fal.py`**
- **`reference_text` missing** on early runs hurt clone quality — always ship `.txt` sidecar
- **130s mixed ref** works for timbre but noisy; **10–15s clean vocal** + transcript is Tier-1
- Full **Qwen ICL mode** (self-hosted) beats embedding-only; Fal gap partially closed by `reference_text`

---

## Handoff for next shots

1. Read shot dialogue + beat from `stage_01` / `stage_02` / `stage_03`.
2. Add shot-specific `FRIEREN_S###_PROMPT` + phrase split if line has natural beats.
3. Reuse `frieren_1min_qwen_ref.wav` embedding unless timbre QC fails.
4. Mux with shot-specific `--start-sec` after waveform review.
5. Document in series bible § shot + this log pattern.

## Lip-sync (post-mux)

**Lip-sync (production):** **PixVerse** — [`docs/pixverse-lipsync-log.md`](pixverse-lipsync-log.md) · skill [`.cursor/skills/pixverse-lipsync/SKILL.md`](../.cursor/skills/pixverse-lipsync/SKILL.md).

After Qwen mux, drive mouth motion with [`scripts/lipsync_fal.py`](../../scripts/lipsync_fal.py) (default `--model pixverse`). **Outputs:** `outputs/video/LipsyncTests/`.

```powershell
cd scripts
python lipsync_fal.py --model pixverse `
  --video ..\outputs\video\final\S008_kling-v26-pro_i2v_natural-audio_20260604T045001Z.mp4 `
  --audio ..\outputs\voice\final\S008\s008_frieren_frieren_dialogue_v14_ja_20260603T050516Z.wav `
  --start-sec 2.05 --tag frieren_dialogue_v14_ja
```

| Run | Output |
|-----|--------|
| **v14_ja + PixVerse** (2026-06-04, new base) | `outputs/video/LipsyncTests/S008_kling-v26-pro_i2v_natural-audio_20260604T045001Z_frieren_dialogue_v14_ja_pixverse_20260604T045309Z.mp4` |
| ~~v14_ja + PixVerse~~ (old base) | `..._20260527T092816Z_..._pixverse_20260604T040712Z.mp4` |

Legacy kling trial:

```powershell
python lipsync_fal.py `
  --video ..\outputs\video\final\S008_kling-v26-pro_i2v_natural-audio_20260604T045001Z.mp4 `
  --audio ..\outputs\voice\S008\s008_frieren_20260602T103112Z.mp3 `
  --start-sec 2.05 --model kling
```

| Model | Fal ID | Notes |
|-------|--------|-------|
| **pixverse** (**default**) | `fal-ai/pixverse/lipsync` | Production — anime / stylized |
| **musetalk** | `fal-ai/musetalk` | Fallback A/B |
| **sync-pro** | `fal-ai/sync-lipsync/v2/pro` | Fallback A/B |
| **kling** | `fal-ai/kling-video/lipsync/audio-to-video` | Weak on S008 MS profile |
| **sync-v3** | `fal-ai/sync-lipsync/v3` | Legacy |

Use **silent base Kling** + **clean dialogue stem** (not the muxed MP4’s mixed bed). S008 MS: Frieren is partial profile — expect subtle mouth motion only.

### HeyGen (via Fal)

Uses **`FAL_KEY`** only — [`fal-ai/heygen/v3/lipsync/precision`](https://fal.ai/models/fal-ai/heygen/v3/lipsync/precision) or `.../speed`.

```powershell
cd scripts
# HeyGen requires speech in the source video — use muxed v11 (not silent Kling alone)
python lipsync_fal.py --model heygen-precision `
  --dialogue-video ..\outputs\video\final\S008_kling-v26-pro_i2v_natural-audio_20260527T092816Z_frieren_dialogue_v11_20260602T103647Z.mp4 `
  --audio ..\outputs\voice\S008\s008_frieren_20260602T103112Z.mp3 --start-sec 2.05 --tag lipsync_v11
python heygen_lipsync.py --mode precision --tag lipsync_v11
```

| Run | Output |
|-----|--------|
| v11 + HeyGen precision | `..._frieren_dialogue_v11_..._lipsync_v11_heygen-precision_20260603T024933Z.mp4` |

Silent base alone returns Fal error: *No speech detected in the input video*.
