# S004 Frieren Qwen3 dialogue — project log

**Skill:** extends [`qwen-frieren-dialogue`](../.cursor/skills/qwen-frieren-dialogue/SKILL.md)

## Scene

| Item | Detail |
|------|--------|
| **Beat B2** | Fern presents envelope; Frieren asks if it's another association request |
| **Story source** | [`panels/jap/panel_s004jap.png`](../panels/jap/panel_s004jap.png) |
| **Still** | [`panels/eng/panel_s004.png`](../panels/eng/panel_s004.png) |
| **Blocking** | Frieren at tree + open grimoire; Fern with sealed envelope |

## Dialogue (JP · EN)

| Speaker | Japanese | English |
|---------|----------|---------|
| Fern | フリーレン様。 | *Lady Frieren.* |
| Frieren | また大陸魔法協会からの依頼？ | *Another request from the Continental Magic Association?* |

**Mux scope:** Frieren-only (Fern line: [`s004-fern-qwen-dialogue-log.md`](./s004-fern-qwen-dialogue-log.md) · ~**0.4s**).

**Delivery:** Dry flat question while reading — weary understated, not alarmed.

## Pipeline

```powershell
cd scripts
python generate_s004_dialogue.py --skip-clone --language Japanese --tag frieren_dialogue_v2_ja
```

| Constant | Default |
|----------|---------|
| `FRIEREN_S004_DIALOGUE_START_SEC` | `1.2` |
| Line | `また大陸魔法協会からの依頼？` |

Voice ref: same as S006/S008 (`frieren_jp_qwen_ref.wav`) + `FRIEREN_JP_TONE` in prompt.

## Iterations

| Tag | Notes |
|-----|-------|
| `frieren_dialogue_v1_ja` | First JP run — **retired:** white noise / hash on playback |
| `frieren_dialogue_v2_ja` | PCM export fix (see below) |

### v1 noise — root cause

| Factor | v1 behavior | v14 S008 (clean) |
|--------|-------------|------------------|
| WAV export | `ffmpeg -i mp3.wav` direct decode | `export_dialogue_wav` → 24 kHz float mono → PCM (same as `concat_with_pauses`) |
| TTS `reference_text` | Not sent on TTS (`use_reference_text_on_tts` default false) — **OK** | Same |
| Clone | Reused embedding `20260603_050516` (ICL pad at clone) — **OK** | Same ref |
| Phrase pipeline | Single Fal MP3 only | Split phrases + concat (S004 is one line — export path was the gap) |

**Fix (v2+):** `synthesize_s004_frieren()` + `export_dialogue_wav()` in `qwen_tts.py`; meta flags `reference_text_on_tts: false`.

**Deliverable (v2):** `outputs/voice/final/S004/s004_frieren_frieren_dialogue_v2_ja_20260604_042026.wav`

**Retired v1:** `s004_frieren_frieren_dialogue_v1_ja_20260603_070054.wav`

## Lip-sync (PixVerse)

**Base:** `outputs/video/final/S004_kling-v26-pro_i2v_anime-audio-12fps_20260527_065906_12fps_20260527_065906.mp4` · **start-sec:** `1.2`

```powershell
cd scripts
python lipsync_fal.py `
  --video "..\outputs\video\final\S004_kling-v26-pro_i2v_anime-audio-12fps_20260527_065906_12fps_20260527_065906.mp4" `
  --audio "..\outputs\voice\final\S004\s004_frieren_frieren_dialogue_v2_ja_20260604_042026.wav" `
  --start-sec 1.2 --tag frieren_dialogue_v1_ja
```

| Run | Audio | Output |
|-----|-------|--------|
| v1 (retired) | v1 WAV | `..._frieren_dialogue_v1_ja_pixverse_20260604_041552.mp4` |
| **v2** | v2 WAV | `LipsyncTests/..._frieren_dialogue_v2_ja_pixverse_20260604_042931.mp4` |
| v1 + Demucs | `s004_frieren_dialogue_v1_ja_demucs.wav` | `LipsyncTests/..._frieren_dialogue_v1_ja_demucs_pixverse_20260604_043949.mp4` |
