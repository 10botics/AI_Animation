# Fern — Qwen3 personality & delivery guide

**Companion:** S004 [`generate_s004_fern_dialogue.py`](../scripts/generate_s004_fern_dialogue.py) · **Shot log:** [`s004-fern-qwen-dialogue-log.md`](./s004-fern-qwen-dialogue-log.md)  
**Master formula:** [`qwen-voice-pipeline-formula.md`](./qwen-voice-pipeline-formula.md)  
**Voice (JP):** clone from [`video source/fernsource.mp4`](../video%20source/fernsource.mp4) → `Voice Reference/Japanese/Fern/fern_jp_qwen_ref.wav` + `.txt`

---

## 1. Who Fern is (for TTS)

| Source | Traits relevant to delivery |
|--------|-----------------------------|
| [Frieren Wiki — Fern](https://frieren.fandom.com/wiki/Fern) | Disciple of Frieren; **earnest**, **dutiful**, emotionally reserved but caring; speaks **politely** to elders |
| **Ch.81 S004** (`panel_s004jap.png`) | Presents sealed envelope; **フリーレン様。** — formal address to her teacher, not casual |
| **Arc contrast vs Frieren** | Fern is **younger** and **more polite**; Frieren is flat deadpan — do not copy Frieren’s flatness 1:1 |

**Not Fern:** squeaky child, tsundere shout, sarcastic teen, Frieren-clone monotone, breathy ASMR, male register.

---

## 2. Manga truth — S005 (`002.jpg` row 3 right)

**Story ref:** [`panels/jap/panel_s005jap.png`](../panels/jap/panel_s005jap.png)

| Balloon | Japanese | TTS |
|---------|----------|-----|
| 1 | いえ、 | clip 1 → **pause** |
| 2–3 | 一級魔法使いレルネン様からの個人的な依頼のようです。 | **one continuous clip** (no gap between balloon lines 2 and 3) |

**Delivery:** Reading letter at camp; soft *no* (いえ), then formal report in one breath; *-sama* on Lernen; quiet unease, not panic.

---

## 3. Manga truth — S004 (`002.jpg` row 2 left)

**Story ref:** [`panels/jap/panel_s004jap.png`](../panels/jap/panel_s004jap.png) · still [`panels/eng/panel_s004.png`](../panels/eng/panel_s004.png)

| Speaker | Japanese | Reading | English |
|---------|----------|---------|---------|
| **Fern** | フリーレン様。 | Furiiren-sama. | *Lady Frieren.* |
| Frieren | また大陸魔法協会からの依頼？ | Mata tairiku mahō kyōkai kara no irai? | *Another request from the Continental Magic Association?* |

**Read order:** Fern’s line is the **address** before Frieren’s dry question — mux **before** Frieren (`FERN_S004_DIALOGUE_START_SEC` ≈ **0.4s** vs Frieren **1.2s**).

**Blocking:** Fern **deeper in frame** with sealed envelope; Frieren **foreground** with grimoire (reframed vs flat two-shot).

---

## 4. How Fern speaks (JP patterns)

| Register | When | Delivery |
|----------|------|----------|
| **Honorific address** | Calling Frieren | **様** clear, respectful, short pause after name |
| **Formal report** | Letter / quest (S005) | Measured read; respectful *-sama* on names |
| **Camp unease** | B2 debate (S006) | Polite concern, not whining — ですます calm |
| **vs Frieren** | Same scene | Slightly **warmer** and **younger** than Frieren’s flat line; still restrained |

**Age:** teen disciple — **polite young adult female**, not child voice.

**Particles:** clean **様** ending on S004; avoid dragging 〜ね unless script asks.

---

## 5. Qwen prompt rules

**Global tone (`FERN_JP_TONE` in `qwen_tts.py`):**

> 若い女性エルフ、丁寧語。落ち着いた中音域。甲高い・幼児声・お嬢様芝居にしない。

**S004 scene (`FERN_S004_PROMPT`):** camp greeting before handing envelope; **respect without flattery**; finish **様** clearly.

**Avoid on TTS:** excited, bubbly, sarcastic, whisper-only, ancient/grandmother tone, copying Frieren deadpan.

**Clone / TTS hygiene (same as Frieren pipeline):**

- `reference_text` on **clone only**
- **No** `reference_text` on phrase TTS (`use_reference_text_on_tts=False`)
- **0.5s** trailing silence on ref before clone (`append_trailing_silence`)
- **PCM WAV** export via `export_dialogue_wav`

---

## 6. Manga truth — S006 (`002.jpg` row 3 middle)

**Story ref:** [`panels/jap/panel_s006jap.png`](../panels/jap/panel_s006jap.png)

| Speaker | Japanese |
|---------|----------|
| **Fern** | あまり乗り気じゃありませんね。 |

**Delivery:** Camp fire; polite concern — Frieren seems unenthusiastic about the unofficial request. Not whining; light ね.

**Scene prompt (`FERN_S006_PROMPT`):** measured ですます; mux ~**0.35s** before Frieren @ **0.55s**.

**Log:** [`s006-fern-qwen-dialogue-log.md`](./s006-fern-qwen-dialogue-log.md)

---

## 7. QC checklist

- [ ] Line is **フリーレン様。** — honorific complete, not clipped
- [ ] Polite disciple, not child squeak or Frieren-flat clone
- [ ] No ICL **「た」** prefix on phrase (ref tail + no ref text on TTS)
- [ ] Timbre acceptable vs `fernsource.mp4` window
- [ ] Mux ~**0.4s** on S004 if combined with Frieren at 1.2s
- [ ] Meta + ref paths logged in [`s004-fern-qwen-dialogue-log.md`](./s004-fern-qwen-dialogue-log.md)

---

## 8. Related shots

| Shot | Fern line (JP) | Script |
|------|----------------|--------|
| **S004** | フリーレン様。 | `generate_s004_fern_dialogue.py` |
| **S005** | いえ、一級魔法使いレルネン様からの個人的な依頼のようです。 | `generate_s005_fern_dialogue.py` · [`panel_s005jap.png`](../panels/jap/panel_s005jap.png) |
| S005 (fallback) | EN scan line | `generate_s005_dialogue.py` (MiniMax) |
| **S006** | あまり乗り気じゃありませんね。 | `generate_s006_fern_dialogue.py` |
| S008 | 報酬の魔導書も… | Back to camera — often no Fern lip-sync |

**Frieren on same panel:** [`s004-frieren-qwen-dialogue-log.md`](./s004-frieren-qwen-dialogue-log.md)
