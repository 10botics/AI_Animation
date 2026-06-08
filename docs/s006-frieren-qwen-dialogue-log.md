# S006 Frieren Qwen3 dialogue — project log

**Skill:** extends [`qwen-frieren-dialogue`](../.cursor/skills/qwen-frieren-dialogue/SKILL.md)

## Scene

| Item | Detail |
|------|--------|
| **Beat B2** | Unofficial letter; camp unease |
| **Story source** | [`panels/jap/panel_s006jap.png`](../panels/jap/panel_s006jap.png) (JP balloons) |
| **Still / EN layout** | [`panels/eng/panel_s006.png`](../panels/eng/panel_s006.png) |
| **Blocking** | Frieren at tree reading; Fern by fire |

## Dialogue (JP · EN)

| Speaker | Japanese | English (scan) |
|---------|----------|----------------|
| Fern | あまり乗り気じゃありませんね。 | *You do not seem particularly enthusiastic, do you?* |
| Frieren (1) | 大陸魔法協会も通さないってことは厄介事の予感がするね。 | Continental Magic Association / trouble, hm? |
| Frieren (2) | 正式な依頼って訳でもなさそうだし、断っちゃっていいんじゃない。 | Not official — we should refuse, shouldn't we? |

**Mux scope:** Frieren-only in early runs; **Fern** WAV: [`s006-fern-qwen-dialogue-log.md`](./s006-fern-qwen-dialogue-log.md).

**Delivery:** Flat, unenthusiastic, pragmatic — not alarmed. Eyes on book; soft trailing ね / ない.

## Voice ref

Same as S008: `Voice Reference/Japanese/Frieren/frieren_jp_qwen_ref.wav` + `.txt` (JP dub compilation timbre).

## Pipeline (default — Japanese WAV)

```powershell
cd scripts
python generate_s006_dialogue.py --skip-clone --language Japanese --tag frieren_dialogue_v1_ja
```

| Constant | Default |
|----------|---------|
| `FRIEREN_S006_DIALOGUE_START_SEC` | `0.55` |
| `FRIEREN_S006_PAUSE_SEC` | `0.6` |
| Phrases | `FRIEREN_S006_PHRASES` (two JP balloons) |

**Optional:**

```powershell
# First balloon only — fits ~5s Kling
python generate_s006_dialogue.py --skip-clone --language Japanese --balloon 1 --tag frieren_dialogue_b1_ja

# Mux to base (warn: full line ~11s vs 5s clip)
python generate_s006_dialogue.py --skip-clone --language Japanese --mux --video ..\outputs\video\final\S006_kling-v26-pro_i2v_anime-audio-12fps_20260527T073942Z_12fps_20260527T073942Z.mp4 --tag frieren_dialogue_v1_ja
```

**Base video (10s, production):** `outputs/video/final/S006_kling-v26-pro_i2v_anime-audio-12fps_20260605T015128Z_12fps_20260605T015128Z.mp4` (~10s — fits full two-balloon Frieren + Fern)

**Legacy 5s:** `..._20260527T073942Z_12fps_20260527T073942Z.mp4` (truncates ~11s dialogue)

## Iterations

| Tag | Language | Duration | F0 median* | Notes |
|-----|----------|----------|------------|-------|
| `frieren_dialogue_v1_ja` | Japanese | **11.09s** | ~221 Hz (+0.8 st vs ref) | Cadence OK; tone slightly bright vs JP ref |
| `frieren_dialogue_v2_ja` | Japanese | **11.09s** | Tuned | `FRIEREN_JP_TONE` prompt — やや低め |
| **`frieren_dialogue_v3_ja`** | Japanese | **~9.9s** | **Compact** | `--compact` brisk prompts + pause **0.35s** (10s Kling fit) |

\*Pitch vs `Voice Reference/Japanese/Frieren/frieren_jp_qwen_ref.wav` (~210 Hz median, librosa pyin).

**Deliverables:**

- v1 (draft): `outputs/voice/S006/s006_frieren_frieren_dialogue_v1_ja_20260603T062750Z.wav`
- v2: `outputs/voice/final/S006/s006_frieren_frieren_dialogue_v2_ja_20260603T063526Z.wav` (~11s)
- **v3 (10s Kling):** `outputs/voice/final/S006/s006_frieren_frieren_dialogue_v3_ja_20260605T015530Z.wav` (~9.9s)
- **PixVerse v3:** `outputs/video/LipsyncTests/..._frieren_dialogue_v3_ja_pixverse_20260605T015836Z.mp4` · copy `outputs/video/final/Voice Added/`

```powershell
python generate_s006_dialogue.py --skip-clone --language Japanese --compact --tag frieren_dialogue_v3_ja
```

## Duration note

Two JP balloons ≈ **11s** TTS — **truncates** on 5s Kling (`-shortest`). Options: `--balloon 1`, regenerate I2V at **duration 10**, or longer base `--video`.
