# Stark — Qwen3 personality & delivery guide

**Companion:** [`qwen-stark-dialogue`](../.cursor/skills/qwen-stark-dialogue/SKILL.md) · **Master formula:** [`qwen-voice-pipeline-formula.md`](./qwen-voice-pipeline-formula.md)  
**Voice (JP):** Chiaki Kobayashi (小林千晃) · **EN:** Jordan Dash Cruz

---

## 1. Who Stark is (sources)

| Source | Traits relevant to TTS |
|--------|-------------------------|
| [Frieren Wiki — Stark](https://frieren.fandom.com/wiki/Stark) | Charismatic, kind, popular with villagers; **cowardly** before fights (trembling hands) but **courage when others need protection**; can be **childish** vs Fern; compassionate |
| [Wikipedia — Stark](https://en.wikipedia.org/wiki/Stark_(Frieren)) | Orphan, Eisen’s apprentice; **lacks confidence**, fears monsters; Kobayashi balances **comedic fear** with **genuine resolve** |
| [Anime Expo 2025 — Kobayashi panel](https://www.animenewsnetwork.com/convention/2025/all-the-news-and-reviews-from-anime-expo/frieren-panel-lets-fans-journey-through-the-anime-soundscape/.226469) | Plays fear as **relatable vulnerability**; Stark grows comfortable **with Frieren and Fern** — not a lone hothead |
| **Ch.81 manga** (`003.jpg` / `081 黄金郷`) | See §2 — **almost no spoken lines** on the golden reveal; **えぇ…** on grimoire beat; ch.82 = pale, then **calm practical question** about the curse |

**Not Stark:** boastful shounen lead, screaming “sugoi”, villain growl, whisper-only ASMR, female register, old-man だなおやじ声.

---

## 2. Manga truth — ch.81 page `003.jpg` (B3)

**Read order on the page** (see `stage_02_shot_list.md`):

1. **S008** — camp: Fern / Frieren / Stark **`えぇ…`** (disbelief at grimoire bribe)  
2. **S010** — wide ridge, trio tiny vs gold  
3. **S011** — **Stark MCU** — balloon: **すごいな…見渡す限りの黄金だ。** ([`panel_s011Jap.png`](../panels/jap/panel_s011Jap.png))  
4. **S012** — wide **backs**; **all JP balloons → Frieren** — **Stark silent**

**Panel text check (`panel_s012jap.png`, RTL):**

| Bubble | Japanese | Speaker |
|--------|----------|---------|
| Right (top→bottom) | 城塞都市ヴァイゼ。50年前に七崩賢黄金郷のマハトの手によって一瞬で黄金に変えられた悲運の都市。 | **Frieren** |
| Left | 噂には聞いていたけど、まさか大陸魔法協会が管理していた**だ**なんてね。 | **Frieren** (not Fern/Stark — they would not know 50y Macht lore) |

**Stark does not speak this line.** Optional stem = **impressed** reaction to the **sight**, not a reading of Frieren’s balloons.

**Later (ch.82, not S012):** After prolonged exposure Stark looks unwell; Fern checks on him; he asks quietly whether **priest magic** lifts the “curse” — **earnest, low, not hype.**

**Implication for S012 TTS:** Any Stark line is **animation-only underscore**, not manga dialogue. It should match **S011 visual awe** + **ch.82 understated dread**, **not** a new loud catchphrase.

---

## 3. How Stark speaks (JP patterns)

| Register | When | Example (canon or near-canon) | Delivery |
|----------|------|----------------------------------|----------|
| **Trailing disbelief** | Absurd reward / party twist | **えぇ…** (S008) | Soft, short, falls off; mouth barely open |
| **Visual awe** | Gold vista (**S011**) | **`すごいな…` / `見渡す限りの黄金だ。`** | Breathy **な…**; impressed **だ** — not **か** irony ([`panel_s011Jap.png`](../panels/jap/panel_s011Jap.png)) |
| **Quiet dread** | Scale of El Dorado (ch.82) | Practical question, not a yell | Low chest voice, slightly unsteady |
| **Brave mode** | Combat | Firm calls | Louder but still **young adult male**, not announcer |

**Age:** ~**18** (teen / young adult) — wonder can be **slightly higher** and more **open** than Frieren’s flat tone; still not a screamer.

**Particles:** **えっ** (gasp), **すごい**, **なんだ…** (innocent realization) — avoid flat **…本当に〜か** (reads **sarcastic** on TTS). Avoid **スゲー**, **マジ**, bro **だな**.

---

## 4. v1 prompt / line vs canon (S012)

| Aspect | **v2** | **v3** | **v4 (impressed)** |
|--------|--------|--------|-------------------|
| **Line** | `…本当に、全部黄金か。` | `えっ…` + `すごい…` | `すごい…` + `全部、金色なんだ…` |
| **Problem** | Sarcastic | **Confused** + surprised | **Impressed** only — no えっ |
| **Prompt** | 確認・呟き | 驚き・困惑 | **感心・見とれる**, anti-戸惑い |

---

## 5. Recommended Qwen prompts (Stark)

### Global tone (`STARK_JP_TONE`)

十代後半・素直・初々しい驚き。やや高めの若い声。**皮肉・冷淡・大人のツッコミにしない。**

### S011 — MCU gold vista (canon, v4)

**2 TTS phrases** — pause **only** after balloon line 1; lines 2–3 one breath:

| Phrase | Text |
|--------|------|
| 1 | `すごいな…` |
| 2 | `見渡す限りの黄金だ。` *(no mid-sentence pause)* |

Soft-spoken `STARK_S011_JP_TONE` (v3 prompts).

### S012 — wide backs (optional stem)

- **Part 1 (`すごい…`):** quiet **admiration** at the gilt vista — **not** `えっ` (confusion).  
- **Part 2 (`全部、金色なんだ…`):** impressed continuation; soft **なんだ…** — **not** skeptical **か**.

**Avoid:** 困惑, 戸惑い, えっ, 皮肉, 呆れ, 反語の「か」.

**Do not assign** Frieren’s left bubble (`噂には…だなんてね`) to Stark.

---

## 6. Comparison to Frieren (same pipeline)

| | **Frieren** | **Stark** |
|---|-------------|-----------|
| **Baseline** | Flat, dry, historian | Breathy, vulnerable, **younger** |
| **JP timbre fix** | `FRIEREN_JP_TONE` (avoid bright elf) | `STARK_JP_TONE` (avoid shouty shounen) |
| **Split phrases** | Pause between **よし。** / **やるか。** | Pause between **exhale** / **mutter** (S012 v2) |
| **Balloon source** | Panel JP primary | Panel often **silent** — scene stem |
| **Ref** | `Voice Reference/Japanese/Stark/stark_jp_qwen_ref.wav` | JP production (S011); source chain in `voice_refs/starksource.*` |

---

## 7. QC checklist (Stark)

- [ ] Does **not** sound louder or brasher than **えぇ…** (S008) without story reason  
- [ ] No 「た」prefix (clone-only `reference_text`; ref tail silence)  
- [ ] Awe = **breath + low mutter**, not announcer  
- [ ] Fits **backs WS** (Stark right): line short enough to sit under Frieren (~2.5s offset)  
- [ ] If timbre too “EN comedy”, swap to **JP Stark** ref clip and `--reclone`

---

## 8. References in repo

| File | Use |
|------|-----|
| `Chapter-81/stage_02_shot_list.md` | S008 / S011 / S012 order |
| `Chapter-81/stage_03_series_bible.md` § Stark, § S012 |
| `panels/jap/panel_s008jap.png` | Canon **えぇ…** |
| `panels/jap/panel_s012jap.png` | Frieren-only balloons |
| `scripts/fal_common.py` `S011_PROMPT_FLUX` | Awestruck face, gaze left |
| `docs/s012-stark-qwen-dialogue-log.md` | Iteration table |

*Last updated: 2026-06-03 — v2 line/prompt after personality pass.*
