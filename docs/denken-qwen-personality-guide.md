# Denken — Qwen3 personality & delivery guide

**Companion skill:** [`qwen-denken-dialogue`](../.cursor/skills/qwen-denken-dialogue/SKILL.md) · **Master formula:** [`qwen-voice-pipeline-formula.md`](./qwen-voice-pipeline-formula.md)  
**Appearance:** [`denken-appearance-reference.md`](./denken-appearance-reference.md)  
**Voice (JP):** 斉藤次郎 (Jiro Saito) · **EN:** Ben Phillips

---

## 1. Who Denken is (sources)

| Source | Traits relevant to TTS |
|--------|-------------------------|
| [Official site — デンケン](https://frieren-anime.jp/character/chara_group1/1-15/) | First-class mage; court mage after power struggles; **barrier warden** of the Golden Land |
| [Frieren Wiki — Denken](https://frieren.fandom.com/wiki/Denken) | Calm analyst; values **coordination**; personable under the “ruthless politician” reputation; patient (years for Diagoldze) |
| [MAL — Denken](https://myanimelist.net/character/215250/Denken) | Cautious; keeps calm and analyzes before battle; competent leader |
| Fan / VA notes | Saito: **baritone**, warm weight, settled elder delivery — dignity without cartoon “grandpa croak” |

**Name cue:** German *denken* (“to think”) — speech should sound **considered**, not impulsive.

**Not Denken:** shouty shounen elder, comic おじいちゃん squeak, cold villain rasp, young adult pitch, Frieren’s flat elf register, Stark’s teen breathiness.

---

## 2. Manga truth — ch.81 B4 forest meet (`004.jpg`)

| Shot / panel | Speaker | Japanese | Notes |
|--------------|---------|----------|-------|
| **S016** · [`panel_s015jap.png`](../panels/jap/panel_s015jap.png) | **Frieren** | `まさかデンケンだったとはね。` | Meet WS — **Denken silent** on this balloon |
| Crop **s016** · [`panel_s016jap.png`](../panels/jap/panel_s016jap.png) | **Denken** | `ゼーリエに頼み込んでな。` / `最近結界の管理者の任を継いだんだ。` | Denken CU — why he is the warden |
| **S017** · [`panel_s017jap.png`](../panels/jap/panel_s017jap.png) | **Denken** | `この地には…黄金郷には儂の故郷があるからな。` | Hometown motive; **儂 (washi)** |

**Pipeline default for “S016 Denken”:** use **`panel_s016jap`** balloons (his first speech after Frieren’s recognition). Do **not** put Frieren’s `まさかデンケン…` line on Denken.

---

## 3. How Denken speaks (JP patterns)

| Register | When | Markers | Delivery |
|----------|------|---------|----------|
| **Elder first person** | Personal stakes | **儂 (わし)** | Steady, low-mid; not frail |
| **Explanatory** | Serie / barrier role | `〜な。` / `〜だ。` | Matter-of-fact court mage; mild warmth |
| **Wistful weight** | Hometown / wife / gold | ellipsis `…`, `からな` | Slightly slower; still composed |
| **Cold truth** | Later B9+ | blunt appraisal | Dry, not cruel shout |

**Age / body:** elderly **human** mage — **baritone**, full chest, unhurried. Warm authority; never cute.

**Avoid:** だぜ／俺様 bravado, ふぉっほっほ laugh track, trembling senility, high pitch, rushed teen cadence.

---

## 4. Recommended Qwen prompts

### Global tone (`DENKEN_JP_TONE`)

高齢の男性魔法使い。落ち着いた低めのバリトン。威厳と温かみ。叫ばない。おじいちゃん芝居・甲高い声・若者声にしない。

### S016 — Serie / barrier warden (`panel_s016jap`)

Two phrases, pause ~0.55s:

1. `ゼーリエに頼み込んでな。` — calm admission; soft trailing `な`  
2. `最近結界の管理者の任を継いだんだ。` — factual; firm `だ` without bark  

### S017 — hometown (`panel_s017jap`)

Split on the ellipsis beat: `この地には…` → `黄金郷には儂の故郷があるからな。`

---

## 5. Voice reference chain

| Step | Path |
|------|------|
| Source | `voice_refs/denkensource.mp4` (from `VideosMain/this.mp4`) |
| Vocals | `voice_refs/denken_vocals.wav` |
| Qwen window | `Voice Reference/Japanese/Denken/denken_jp_qwen_ref.wav` + `.txt` |
| Registry | `voice_registry.local.json` → `qwen_speaker_embeddings.Denken` |

**Clone:** `reference_text` on **clone only** — **not** on phrase TTS (same ICL rule as Frieren/Stark).

---

## 6. Comparison

| | **Frieren** | **Stark** | **Denken** |
|--|-------------|-----------|------------|
| Age read | Young-adult elf (flat) | Teen warrior | Elderly human mage |
| Pitch | Mid, slightly low for female | Higher young male | Low baritone |
| Emotion | Dry understatement | Soft awe / fear | Calm weight + warmth |
| Pronoun | 私 / casual ね | (teen) | **儂** when personal |
