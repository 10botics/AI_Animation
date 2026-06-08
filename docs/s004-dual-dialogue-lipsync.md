# S004 dual dialogue (Fern → Frieren) — audio vs lip-sync

**Panel order:** [`panels/jap/panel_s004jap.png`](../panels/jap/panel_s004jap.png)

1. Fern — **フリーレン様。** @ **1.0s**
2. Pause — **0.6s**
3. Frieren — **また大陸魔法協会からの依頼？** @ **~3.1s** (1.0 + Fern clip length + pause)

Constants: `FERN_S004_DIALOGUE_START_SEC`, `FERN_S004_PAUSE_BEFORE_FRIEREN_SEC` in `scripts/qwen_tts.py`.

---

## Why one PixVerse pass with “both voices” feels broken

| Issue | What happens |
|-------|----------------|
| **Single face driver** | `fal-ai/pixverse/lipsync` maps **one** audio track to **one** dominant face in the frame — not per-speaker routing. |
| **S004 layout** | Frieren **foreground profile**; Fern **deeper / partial** — during Fern’s line PixVerse often animates the **wrong** mouth or barely moves Fern. |
| **Not always an API error** | Combined WAV usually **uploads**; failure is often **QC** (weird motion, wrong speaker, frozen mouth) or a **cancelled** long run — not “dual audio forbidden.” |
| **amix timeline** | `mix_dialogue_stems()` is correct for **hearing** both lines; it is **not** a multi-speaker lip-sync format. |

---

## Recommended workflow

### 1. Build combined timeline (both lines, natural pause)

```powershell
cd scripts
python build_s004_combined_dialogue.py `
  --fern-wav "..\outputs\voice\final\S004\s004_fern_fern_dialogue_v2_ja_20260604T072740Z.wav" `
  --frieren-wav "..\outputs\voice\final\S004\s004_frieren_frieren_dialogue_v2_ja_20260604T042026Z.wav" `
  --fern-start 1.0 `
  --pause-sec 0.6 `
  --video "..\outputs\video\S004_kling-v26-pro_i2v_anime-audio-12fps_20260604T064358Z_12fps_20260604T064358Z.mp4" `
  --tag fern_v2_frieren_v2_ja
```

Use **v2 Frieren** WAV for cleaner audio unless you are A/B testing v1 hiss.

### 2a. Ship **sound** (both speakers) — mux, no PixVerse

```powershell
python mux_s004_dual_dialogue.py `
  --video "..\outputs\video\S004_kling-v26-pro_i2v_anime-audio-12fps_20260604T064358Z_12fps_20260604T064358Z.mp4" `
  --fern-wav "..\outputs\voice\final\S004\s004_fern_fern_dialogue_v2_ja_20260604T072740Z.wav" `
  --frieren-wav "..\outputs\voice\final\S004\s004_frieren_frieren_dialogue_v2_ja_20260604T042026Z.wav"
```

Keeps Kling foley; ducks bed under dialogue.

### 2b. Ship **Frieren mouth** — PixVerse **Frieren stem only**

```powershell
python lipsync_fal.py `
  --video "..\outputs\video\S004_kling-v26-pro_i2v_anime-audio-12fps_20260604T064358Z_12fps_20260604T064358Z.mp4" `
  --audio "..\outputs\voice\final\S004\s004_frieren_frieren_dialogue_v2_ja_20260604T042026Z.wav" `
  --start-sec 3.1 `
  --tag frieren_dialogue_v2_ja
```

Then **mux Fern** on top in an edit, or run `mux_s004_dual_dialogue.py` on the lipsync output if the script is pointed at that MP4.

Fern’s line stays **audio-only** (appropriate: she is not lip-forward on this still).

### 2c. Avoid for production

`lipsync_fal.py` + **combined** dual WAV — use only for experiments; expect wrong-face sync on Fern’s line.

---

## ROI lip-sync (single speaker on busy frames)

`scripts/lipsync_fal_roi.py` — crop → PixVerse → overlay. Presets: `--shot S005` (Fern right-center), `S004` (Frieren profile), `S004_FERN` (Fern background), `S008`.

**S004 dual (5s Kling):** two passes + `combine_dual_roi_lipsync.py` (Frieren layer first, Fern on top).

```powershell
# Fern @ 0.4s (fits 5.08s clip); Frieren @ 0.4 + Fern dur + 0.6s pause
python lipsync_fal_roi.py --shot S004_FERN --video ... --audio ...\s004_fern_fern_dialogue_v2_ja_....wav --start-sec 0.4 --tag fern_dialogue_v2_ja --keep-work
python lipsync_fal_roi.py --shot S004 --video ... --audio ...\s004_frieren_frieren_dialogue_v2_ja_....wav --start-sec 2.497 --tag frieren_dialogue_v2_ja --keep-work
python combine_dual_roi_lipsync.py --base ... --meta ..._frieren_..._roi_....json --meta ..._fern_..._roi_....json `
  --fern-wav ... --frieren-wav ... --fern-start 0.4 --pause-sec 0.6 --tag s004_fern_frieren_dual_roi
```

**Shipped (2026-06-04):** `outputs/video/final/Voice Added/..._s004_fern_frieren_dual_roi_20260604T084028Z_dual_mux_20260604T084028Z.mp4`

### Mask workflow (black box on other face — often easier to tune)

`scripts/lipsync_fal_mask.py` — draw black over the **non-speaking** face → full-frame PixVerse → same `combine_dual_roi_lipsync.py` paste step.

```powershell
python lipsync_fal_mask.py --shot S004 --speaker fern --video ...10s_kling....mp4 `
  --audio ...\s004_fern_fern_dialogue_v2_ja_....wav --start-sec 1.0 --tag fern_v2_mask --keep-work
python lipsync_fal_mask.py --shot S004 --speaker frieren --video ... --audio ...\s004_frieren_....wav `
  --start-sec 3.1 --tag frieren_v2_mask --keep-work
python combine_dual_roi_lipsync.py --base ... --meta ...fern...mask....json --meta ...frieren...mask....json `
  --fern-wav ... --frieren-wav ... --fern-start 1.0 --pause-sec 0.6 --tag s004_dual_mask
```

Tune boxes with `--mask-rel x,y,w,h` if the preset hides too much / too little.

---


## Related

- Fern TTS: [`s004-fern-qwen-dialogue-log.md`](./s004-fern-qwen-dialogue-log.md)
- Frieren TTS: [`s004-frieren-qwen-dialogue-log.md`](./s004-frieren-qwen-dialogue-log.md)
- PixVerse log: [`pixverse-lipsync-log.md`](./pixverse-lipsync-log.md)
