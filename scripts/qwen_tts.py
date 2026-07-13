"""
Qwen3 TTS voice clone + speech (Fal).

Tier-1 defaults: curated ~12s ref + reference_text (see prepare_frieren_qwen_ref.py).

Usage:
  cd scripts
  python prepare_frieren_qwen_ref.py
  python qwen_tts.py --text "Line here"
  python qwen_tts.py --text "Line here" --reclone
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import fal_client

from fal_common import ROOT, download_file, read_fal_key
from voice_paths import (
    VR_EN_FRIEREN,
    VR_JP_DENKEN,
    VR_JP_FERN,
    VR_JP_FRIEREN,
    VR_JP_STARK,
    VOICE_REFS_WORK,
)

REGISTRY_PATH = ROOT / "voice_registry.local.json"
QWEN_CLONE = "fal-ai/qwen-3-tts/clone-voice/1.7b"
QWEN_TTS = "fal-ai/qwen-3-tts/text-to-speech/1.7b"

# ICL clone continues the last mora of the ref (e.g. 良かった → "ta" before each phrase).
REF_ICL_TRAILING_SILENCE_SEC = 0.5

# Personality-aligned delivery hints (Qwen `prompt` field — not a script direction).
# Frieren: flat baseline, dry deadpan, soft natural dub; magic-geek beats = subtle interest only.
# Ref: Mallorie Rodak (EN) — subdued, introspective; avoid "ancient"/grandmother/old-crone tone.
# Sources: Frieren wiki, Anime Corner Rodak interview, ch.81 S008 = grimoire-bribe micro-spark.
DEFAULT_PROMPT = (
    "Young adult female elf. Subdued natural English anime dub. "
    "Flat calm baseline, soft and unhurried. Dry understated delivery. "
    "Slightly lower middle register—not bright or childlike. "
    "Matter-of-fact, never loud, bubbly, or overly emotional."
)

# JP dub timbre: ref median ~210 Hz; Qwen drifts ~1 semitone high without this hint.
FRIEREN_JP_TONE = (
    "やや低めの落ち着いた中音域。高め・幼い・甲高い声にしない。"
)

# Fern: polite disciple register — younger than Frieren, not childish squeak.
FERN_JP_TONE = (
    "若い女性エルフ、丁寧語。落ち着いた中音域。甲高い・幼児声・お嬢様芝居にしない。"
)

# S008 — ch.81 B3 / `003.jpg` top-left tier
# Story ref (JP balloons): [`panels/jap/panel_s008jap.png`] · layout still: [`panels/eng/panel_s008.png`]
FRIEREN_S008_PHRASES_EN = ("Now we're talking.", "Let's do it.")
# Default pipeline (2026-06): JP manga balloons from panel_s008jap.png
FRIEREN_S008_PHRASES = ("よし。", "やるか。")
FRIEREN_S008_LANGUAGE = "Japanese"
FRIEREN_S008_DIALOGUE = {
    "Fern": {
        "ja": "報酬の魔導書も一緒に送られてきていますけれども…",
        "ja_reading": "Hōshū no madōsho mo issho ni okurarete kite imasu keredomo…",
        "en": "A grimoire reward was included with the request, though...",
    },
    "Frieren": {
        "ja": "よし。やるか。",
        "ja_reading": "Yoshi. Yaru ka.",
        "ja_phrases": ("よし。", "やるか。"),
        "en_phrases": FRIEREN_S008_PHRASES_EN,
        "en": "Now we're talking. Let's do it.",
    },
    "Stark": {
        "ja": "えぇ…",
        "ja_reading": "Ee…",
        "en": "Eh?",
    },
}
# Fern (back to camera) reads grimoire reward; Frieren dry pivot; Stark disbelief.
FRIEREN_S008_PROMPT = (
    "昼の森のキャンプ。魔導書の報酬を聞いたあと、淡々とした同意。感情を込めない。"
    "若い女性エルフ、フラットで落ち着いた日本語アニメ声。微かな興味だけ。"
    + FRIEREN_JP_TONE
)
FRIEREN_S008_PROMPT_EN = (
    "Daytime forest camp. Frieren replying to Fern after hearing a grimoire "
    "is included with a request she was ignoring. Dry deadpan pivot—not excitement. "
    "Soft unhurried English dub; subtle magic-geek spark only."
)
# Qwen rushes period-pause in one clip; split synth + explicit gap reads natural.
FRIEREN_S008_PAUSE_SEC = 0.55
FRIEREN_S008_PROMPT_PART1 = (
    "昼のキャンプ。魔導書の報酬を聞いて、静かな同意の一言「よし」。"
    "フラットでウィットに欠けない淡々とした声。落ち着いた日本語。"
    + FRIEREN_JP_TONE
)
FRIEREN_S008_PROMPT_PART2 = (
    "昼のキャンプ。実務的な決断「やるか」。短く matter-of-fact。"
    "感情を抑えた若い女性エルフの日本語。微かな魔法好きの気配だけ。"
    + FRIEREN_JP_TONE
)
FRIEREN_S008_PROMPT_PART1_EN = (
    "Daytime forest camp. Dry deadpan idiom of quiet approval—flat wit, subtle interest "
    "after hearing a grimoire reward. Soft unhurried English dub; finish the phrase cleanly."
)
FRIEREN_S008_PROMPT_PART2_EN = (
    "Daytime forest camp. Pragmatic matter-of-fact yes—decisive agreement after a brief beat. "
    "Flat calm English dub, subtle magic-geek spark only."
)
FRIEREN_DIALOGUE_START_SEC = 2.05

# S004 — ch.81 B2 / `002.jpg` row 2 (viewer's left)
# Story ref (JP): [`panels/jap/panel_s004jap.png`] · still: [`panels/eng/panel_s004.png`]
FRIEREN_S004_PHRASES_EN = ("Another request from the Continental Magic Association?",)
FRIEREN_S004_PHRASES = ("また大陸魔法協会からの依頼？",)
FRIEREN_S004_LANGUAGE = "Japanese"
FRIEREN_S004_DIALOGUE = {
    "Fern": {
        "ja": "フリーレン様。",
        "ja_reading": "Furiiren-sama.",
        "en": "Lady Frieren.",
    },
    "Frieren": {
        "ja": "また大陸魔法協会からの依頼？",
        "ja_reading": "Mata tairiku mahō kyōkai kara no irai?",
        "ja_phrases": FRIEREN_S004_PHRASES,
        "en_phrases": FRIEREN_S004_PHRASES_EN,
        "en": FRIEREN_S004_PHRASES_EN[0],
    },
}
FRIEREN_S004_PROMPT = (
    "昼の森のキャンプ。本を読みながらフェルンに向かって、また協会からの依頼かと淡々と問う。"
    "フラットで matter-of-fact な日本語。軽い疑問の語尾。"
    + FRIEREN_JP_TONE
)
FRIEREN_S004_PROMPT_EN = (
    "Daytime forest camp. Frieren at the tree with open grimoire, dry flat question after Fern "
    "addresses her—another Continental Magic Association request? Soft unhurried English dub; "
    "weary understated, not alarmed or bubbly."
)
FRIEREN_S004_DIALOGUE_START_SEC = 1.2

# S016 — ch.81 B4 / `004.jpg` row 2 — forest meet (Denken L, Stark mid, Frieren R)
# Story ref (JP): [`panels/jap/panel_s015jap.png`] — panel crop id s015; shot list **S016**.
FRIEREN_S016_PHRASES_EN = ("To think it was Denken.",)
FRIEREN_S016_PHRASES = ("まさかデンケンだったとはね。",)
FRIEREN_S016_LANGUAGE = "Japanese"
FRIEREN_S016_DIALOGUE = {
    "Frieren": {
        "ja": "まさかデンケンだったとはね。",
        "ja_phrases": FRIEREN_S016_PHRASES,
        "en_phrases": FRIEREN_S016_PHRASES_EN,
        "en": FRIEREN_S016_PHRASES_EN[0],
    },
}
FRIEREN_S016_PROMPT = (
    "深い森の中、デンケンと対面した直後。まさかデンケンだったとは、と淡々と一言。"
    "軽い驚きはあるが大げさにしない。だったとはねの語尾を自然な話し言葉で。"
    + FRIEREN_JP_TONE
)
FRIEREN_S016_PROMPT_EN = (
    "Forest clearing meet. Frieren recognizes Denken the warden—dry mild realization, not loud surprise. "
    "To think it was Denken. Soft unhurried English dub, understated, matter-of-fact."
)
FRIEREN_S016_DIALOGUE_START_SEC = 1.0

# Denken — personality: docs/denken-qwen-personality-guide.md
# JP VA: 斉藤次郎 (baritone elder); EN: Ben Phillips
DENKEN_QWEN_REF_WAV = VR_JP_DENKEN / "denken_jp_qwen_ref.wav"
DENKEN_QWEN_REF_TXT = VR_JP_DENKEN / "denken_jp_qwen_ref.txt"
DENKEN_QWEN_REF_META = VR_JP_DENKEN / "denken_jp_qwen_ref.json"
DENKEN_SOURCE_MP4 = VOICE_REFS_WORK / "denkensource.mp4"

DENKEN_JP_TONE = (
    "高齢の男性魔法使い。落ち着いた低めのバリトン。威厳と温かみがある。"
    "叫ばない。おじいちゃん芝居・甲高い声・若者声・悪役の掠れ声にしない。"
)

# S016 Denken — B4 after meet; story balloons on panel crop s016 (not Frieren's S016 meet balloon)
# Shot-list S016 meet WS = Frieren only (`panel_s015jap`). Denken CU: [`panels/jap/panel_s016jap.png`]
DENKEN_S016_PHRASES = (
    "ゼーリエに頼み込んでな。",
    "最近結界の管理者の任を継いだんだ。",
)
DENKEN_S016_PHRASES_EN = (
    "I pleaded with Serie, you see.",
    "I recently took over as the barrier's warden.",
)
DENKEN_S016_LANGUAGE = "Japanese"
DENKEN_S016_DIALOGUE = {
    "Frieren": {
        "ja": "まさかデンケンだったとはね。",
        "panel": "panels/jap/panel_s015jap.png",
        "note": "Shot-list S016 meet — Frieren only.",
    },
    "Denken": {
        "ja": "".join(DENKEN_S016_PHRASES),
        "ja_phrases": DENKEN_S016_PHRASES,
        "en_phrases": DENKEN_S016_PHRASES_EN,
        "en": " ".join(DENKEN_S016_PHRASES_EN),
        "panel": "panels/jap/panel_s016jap.png",
    },
}
DENKEN_S016_PROMPT_PART1 = (
    "森の中、フリーレンに認識された直後のデンケン。"
    "ゼーリエに頼み込んでな、と落ち着いて認める。低めのバリトン。柔らかく余韻のあるな。"
    + DENKEN_JP_TONE
)
DENKEN_S016_PROMPT_PART2 = (
    "続けて、最近結界の管理者の任を継いだんだ、と事実を淡々と述べる。"
    "宮廷魔法使いの落ち着き。断定のだは強く張り上げない。温かみを残す。"
    + DENKEN_JP_TONE
)
DENKEN_S016_PROMPTS = (DENKEN_S016_PROMPT_PART1, DENKEN_S016_PROMPT_PART2)
DENKEN_S016_PROMPT = DENKEN_S016_PROMPT_PART1 + " " + DENKEN_S016_PROMPT_PART2
DENKEN_S016_PROMPT_EN = (
    "Forest meet. Elderly mage Denken calmly admits he pleaded with Serie and recently "
    "became the barrier warden—warm baritone, composed, never shouty or frail."
)
DENKEN_S016_DIALOGUE_START_SEC = 1.0
DENKEN_S016_PAUSE_SEC = 0.55

# S017 — hometown reveal (`panels/jap/panel_s017jap.png`)
DENKEN_S017_PHRASES = (
    "この地には…",
    "黄金郷には儂の故郷があるからな。",
)
DENKEN_S017_PHRASES_EN = (
    "In this land…",
    "In the Golden Land, my hometown is there.",
)
DENKEN_S017_LANGUAGE = "Japanese"
DENKEN_S017_PROMPT_PART1 = (
    "森の崖際。この地には、と少し間を置いて切り出す。低めのバリトン。感慨はあるが泣き声にしない。"
    + DENKEN_JP_TONE
)
DENKEN_S017_PROMPT_PART2 = (
    "黄金郷には儂の故郷があるからな、と静かに明かす。儂は自然な老人の一人称。"
    "郷愁はあるが淡々と。叫ばない。"
    + DENKEN_JP_TONE
)
DENKEN_S017_PROMPTS = (DENKEN_S017_PROMPT_PART1, DENKEN_S017_PROMPT_PART2)
DENKEN_S017_PROMPT = DENKEN_S017_PROMPT_PART1 + " " + DENKEN_S017_PROMPT_PART2
DENKEN_S017_DIALOGUE_START_SEC = 1.0
DENKEN_S017_PAUSE_SEC = 0.55

# S013 — ch.81 B4 / `004.jpg` row 1 — great barrier megashot (stage_03 **S015-barrier**)
# Story ref (JP): [`panels/jap/panel_s013jap.png`] — chibi omake + balloon; still ID **S013**.
# One manga sentence — do not split across TTS phrases (formula §1).
FRIEREN_S013_PHRASES_EN = (
    "Is Macht still sealed inside the great barrier covering the Golden Land?",
)
FRIEREN_S013_PHRASES = ("黄金郷を覆う大結界の中には今もマハトが封印されているのか。",)
FRIEREN_S013_LANGUAGE = "Japanese"
FRIEREN_S013_DIALOGUE = {
    "Frieren": {
        "ja": FRIEREN_S013_PHRASES[0],
        "ja_phrases": FRIEREN_S013_PHRASES,
        "en_phrases": FRIEREN_S013_PHRASES_EN,
        "en": FRIEREN_S013_PHRASES_EN[0],
    },
}
FRIEREN_S013_PROMPT = (
    "黄金郷を覆う巨大な大結界を見下ろす展望。今もマハトが封印されているのか、と静かに問う。"
    "歴史を思い出すような淡々とした口調。分析的。興奮しない。"
    "テンポやや早め、間を詰め、簡潔に一続きで言い切る。語尾「のか」は短く。"
    + FRIEREN_JP_TONE
)
FRIEREN_S013_PROMPT_EN = (
    "Extreme wide barrier overlook. Frieren wonders whether Macht is still sealed "
    "inside the great ward over the Golden Land—calm historian tone, soft unhurried English dub, "
    "slightly brisker pace, concise, no long pauses, never melodramatic."
)
FRIEREN_S013_DIALOGUE_START_SEC = 0.35
FRIEREN_S013_TARGET_MAX_SEC = 4.9

# S014 — ch.81 B4 / `004.jpg` row 1 left — MCU Frieren after barrier reveal
# Story ref (JP): [`panels/jap/panel_s014jap.png`]
# stage_02: calm/surprised — barrier job; request to assist warden (not loud shock).
FRIEREN_S014_PHRASES_EN = (
    "Still, I'm surprised.",
    "The request said to help the barrier warden dispatched by the Continental Magic Association, though.",
)
FRIEREN_S014_PHRASES = (
    "しかし驚いたよ。",
    "依頼書には大陸魔法協会から派遣された結界の管理者を手伝うようにとあったけど。",
)
FRIEREN_S014_LANGUAGE = "Japanese"
FRIEREN_S014_DIALOGUE = {
    "Frieren": {
        "ja": "".join(FRIEREN_S014_PHRASES),
        "ja_phrases": FRIEREN_S014_PHRASES,
        "en_phrases": FRIEREN_S014_PHRASES_EN,
        "en": " ".join(FRIEREN_S014_PHRASES_EN),
    },
}
FRIEREN_S014_PROMPT = (
    "森の中、大結界を見た直後のフリーレン。しかし驚いたよ、と淡い驚きだけ。"
    "依頼書では大陸魔法協会から派遣された結界の管理者を手伝うとあった、と続ける。"
    "フラットで落ち着いた話し言葉。大げさな驚き・興奮・甲高い声にしない。"
    + FRIEREN_JP_TONE
)
FRIEREN_S014_PROMPT_PART1 = (
    "森の中。しかし驚いたよ、と短く。軽い驚きだけ、フラットで落ち着いた日本語。"
    "大げさにしない。語尾よは自然に。"
    + FRIEREN_JP_TONE
)
FRIEREN_S014_PROMPT_PART2 = (
    "依頼書には大陸魔法協会から派遣された結界の管理者を手伝うようにとあったけど、と一続きで。"
    "説明口調、淡々と。けどで柔らかく余韻。朗読調にしない。"
    + FRIEREN_JP_TONE
)
FRIEREN_S014_PROMPTS = (FRIEREN_S014_PROMPT_PART1, FRIEREN_S014_PROMPT_PART2)
FRIEREN_S014_PROMPT_EN = (
    "Forest MCU after the great barrier. Frieren notes mild surprise—calm, dry, understated—"
    "then explains the request was to assist the barrier warden from the Continental Magic Association. "
    "Soft unhurried English dub; trailing though; never excited or bubbly."
)
FRIEREN_S014_PROMPTS_EN = (
    "Forest MCU. Soft dry: Still, I'm surprised. Mild only—flat calm English dub.",
    "Continuing: the request said to help the barrier warden from the Continental Magic Association, though. "
    "Matter-of-fact, soft trailing though, never loud.",
)
FRIEREN_S014_PAUSE_SEC = 0.5
FRIEREN_S014_DIALOGUE_START_SEC = 1.0

# Fern S004 — same panel; speaks first (honorific before Frieren’s question)
FERN_S004_PHRASES = ("フリーレン様。",)
FERN_S004_PHRASES_EN = ("Lady Frieren.",)
FERN_S004_LANGUAGE = "Japanese"
FERN_S004_PROMPT = (
    "昼の森のキャンプ。師匠フリーレンに向けた短い呼びかけ。封筒を差し出す前の丁寧な挨拶。"
    "畏敬はあるが媚びない。はっきり「様」まで。"
    + FERN_JP_TONE
)
FERN_S004_PROMPT_EN = (
    "Daytime forest camp. Fern addresses her teacher politely before handing over the sealed envelope. "
    "Young female elf, respectful *Lady Frieren*, measured and calm, not bubbly or loud."
)
FERN_S004_DIALOGUE_START_SEC = 1.0
# Gap after フリーレン様。 before Frieren’s reply (panel read order).
FERN_S004_PAUSE_BEFORE_FRIEREN_SEC = 0.6

# S005 — ch.81 B2 / `002.jpg` row 3 right — story: [`panels/jap/panel_s005jap.png`]
FERN_S005_PHRASES_EN = (
    "Nay, this appears to be a personal request",
    "from First-Class Mage Lernen-sama.",
)
# Manga balloon is three lines; TTS is **two** clips — pause only after いえ、 (not between 2↔3).
FERN_S005_PHRASES_BALLOON = (
    "いえ、",
    "一級魔法使いレルネン様からの",
    "個人的な依頼のようです。",
)
FERN_S005_PHRASES = (
    "いえ、",
    "一級魔法使いレルネン様からの個人的な依頼のようです。",
)
FERN_S005_LANGUAGE = "Japanese"
FERN_S005_DIALOGUE = {
    "Fern": {
        "ja": "いえ、一級魔法使いレルネン様からの個人的な依頼のようです。",
        "en": " ".join(FERN_S005_PHRASES_EN),
    },
}
FERN_S005_PROMPT = (
    "森のキャンプ。手紙を読みながら報告する若い女性エルフ。丁寧語、落ち着いた声。"
    "一級魔法使いレルネン様からの個人的な依頼だと淡々と伝える。驚きすぎない、軽く否定する「いえ」から入る。"
    + FERN_JP_TONE
)
FERN_S005_PROMPT_PART1 = (
    "手紙を見て、いえ、と短く否定してから続ける。丁寧で落ち着いた日本語。"
    + FERN_JP_TONE
)
FERN_S005_PROMPT_PART2 = (
    "一級魔法使いレルネン様からの、と敬称をはっきり。報告口調、フラット。"
    + FERN_JP_TONE
)
FERN_S005_PROMPT_PART3 = (
    "個人的な依頼のようです、と結ぶ。です・ます調、静かな重み、朗読調にしない。"
    + FERN_JP_TONE
)
FERN_S005_PROMPT_PART2_3 = (
    "一級魔法使いレルネン様からの個人的な依頼のようです、と一続きで淡々と報告。"
    "敬称をはっきり、ですます調、句の途中で切れない自然な流れ。"
    + FERN_JP_TONE
)
FERN_S005_PROMPTS = (FERN_S005_PROMPT_PART1, FERN_S005_PROMPT_PART2_3)
FERN_S005_PROMPTS_EN = (
    "Reading a letter at camp. Soft correction: Nay — formal, measured English.",
    "Naming First-Class Mage Lernen-sama with respectful weight.",
    "Closing: personal request — quiet unease, not alarmed.",
)
FERN_S005_PAUSE_SEC = 0.5
FERN_S005_DIALOGUE_START_SEC = 1.85

# S012 — ch.81 B3 / `003.jpg` bottom tier (viewer's left)
# Story ref (JP): [`panels/jap/panel_s012jap.png`] — **all balloon tails → Frieren** (center).
# EN scan layout often mis-reads the left bubble as Fern; Fern/Stark are too young for 50y Macht lore.
FRIEREN_S012_PHRASES_EN = (
    "The fortress city of Weise—a tragic city turned to gold in an instant fifty years ago "
    "by the hand of Macht of El Dorado, one of the Seven Sages of Destruction.",
    "I'd heard the rumors, but to think the Continental Magic Association was managing it, of all things.",
)
# Manga RTL: right column = one breath (label + appositive Macht line); then left 噂 bubble.
# Panel text verified: 城塞都市ヴァイゼ。 (furigana じょうさいとし) — not 城壁; name ヴァイゼ is correct.
FRIEREN_S012_PHRASES = (
    "城塞都市ヴァイゼ。50年前に七崩賢黄金郷のマハトの手によって一瞬で黄金に変えられた悲運の都市。",
    "噂には聞いていたけど、まさか大陸魔法協会が管理していただなんてね。",
)
FRIEREN_S012_LANGUAGE = "Japanese"
FRIEREN_S012_DIALOGUE = {
    "Frieren": {
        "ja": "城塞都市ヴァイゼ。50年前に七崩賢黄金郷のマハトの手によって一瞬で黄金に変えられた悲運の都市。噂には聞いていたけど、まさか大陸魔法協会が管理していただなんてね。",
        "ja_phrases": FRIEREN_S012_PHRASES,
        "en_phrases": FRIEREN_S012_PHRASES_EN,
        "en": " ".join(FRIEREN_S012_PHRASES_EN),
        "note": "All three balloons on panel_s012jap.png point to Frieren; not Fern.",
    },
}
FRIEREN_S012_PROMPT = (
    "城塞都市を見下ろす広い背中ショット。フリーレンが仲間に向けて淡々と歴史を語る。"
    "感情を込めないフラットな解説口調。落ち着いた日本語。"
    + FRIEREN_JP_TONE
)
FRIEREN_S012_PROMPT_EN = (
    "Wide backs toward the gilt fortress city. Frieren lectures the party—Weise, the Association, "
    "Macht and El Dorado—calm historian tone, soft unhurried English dub, never melodramatic."
)
FRIEREN_S012_PAUSE_SEC = 0.55
FRIEREN_S012_PROMPT_PART1 = (
    "広い展望。仲間に向けた淡々とした会話調の説明。まず城塞都市ヴァイゼと名乗り、"
    "続けて50年前マハトに黄金にされた悲運の都市と、同じ話の続きとして自然につなぐ。"
    "「という」のある話し方。朗読・ナレーション調にしない。フラットな日本語。"
    + FRIEREN_JP_TONE
)
FRIEREN_S012_PROMPT_PART2 = (
    "広い展望。噂は聞いていたが、まさか協会が管理していただなんて、と軽く驚きを込めない"
    "淡々とした会話。だなんてねの語尾を自然に。落ち着いた話し言葉。"
    + FRIEREN_JP_TONE
)
FRIEREN_S012_PROMPTS = (
    FRIEREN_S012_PROMPT_PART1,
    FRIEREN_S012_PROMPT_PART2,
)
FRIEREN_S012_PROMPTS_EN = (
    "Wide vista. Frieren names Weise then continues in one flowing line—the tragic city Macht "
    "turned to gold fifty years ago—flat calm exposition, no pause after the city name, English dub.",
    "Wide vista. Frieren adds she'd heard rumors but not that the Association manages it—soft unhurried dub.",
)
FRIEREN_S012_DIALOGUE_START_SEC = 1.0

# S012 — Stark optional stem (no balloon on panel_s012jap; Frieren monologue only)
STARK_SOURCE_VIDEO = VOICE_REFS_WORK / "starksource.mp4"
STARK_SOURCE_WAV = VOICE_REFS_WORK / "starksource.wav"
STARK_VOCALS_WAV = VOICE_REFS_WORK / "starksource_vocals.wav"
STARK_QWEN_REF_WAV = VR_JP_STARK / "stark_jp_qwen_ref.wav"
STARK_QWEN_REF_TXT = VR_JP_STARK / "stark_jp_qwen_ref.txt"
STARK_QWEN_REF_META = VR_JP_STARK / "stark_jp_qwen_ref.json"

FERN_QWEN_REF_WAV = VR_JP_FERN / "fern_jp_qwen_ref.wav"
FERN_QWEN_REF_TXT = VR_JP_FERN / "fern_jp_qwen_ref.txt"
FERN_QWEN_REF_META = VR_JP_FERN / "fern_jp_qwen_ref.json"
FERN_SOURCE_MP4 = ROOT / "video source" / "fernsource.mp4"

# Personality: docs/stark-qwen-personality-guide.md · skill: qwen-stark-dialogue
STARK_DEFAULT_PROMPT = (
    "Young adult male warrior. Sincere Japanese anime voice, mid-low register. "
    "Often breathy or slightly unsteady when afraid; never shouty shounen hype."
)

STARK_JP_TONE = (
    "十代後半の若い男性戦士。素直で初々しい日本語アニメ声。やや高めの若い声域。"
    "感心・感嘆・見とれるトーン。困惑・戸惑い・疑問・皮肉・冷淡にしない。叫ばない。"
)

# S011 — ch.81 B3 / `003.jpg` Stark MCU awe (`panels/jap/panel_s011Jap.png`)
STARK_S011_JP_TONE = (
    "十五歳前後の少年の声。小声で柔らかく、息多めのささやきに近いがはっきり聞える。"
    "素直な感心。声量は抑える。明るすぎる・張り上げ・雄叫び・皮肉・冷笑・ツッコミ禁止。"
)

# v1 (retired): 2 phrases — part2 flat だ sounded sarcastic on Qwen
STARK_S011_PHRASES_V1 = ("すごいな…", "見渡す限りの黄金だ。")

# v2: 3 phrases — pause between line 2 and 3 felt wrong; v4 merges 2+3 (one breath)
STARK_S011_PHRASES_V2 = ("すごいな…", "見渡す限りの", "黄金だ。")

# v4: pause only after すごいな…; 見渡す限りの黄金だ。 continuous (panel lines 2–3)
STARK_S011_PHRASES = ("すごいな…", "見渡す限りの黄金だ。")
STARK_S011_PHRASES_EN = ("Wow…", "It's gold as far as the eye can see.")
STARK_S011_LANGUAGE = "Japanese"
STARK_S011_DIALOGUE = {
    "Stark": {
        "ja": "すごいな…見渡す限りの黄金だ。",
        "ja_phrases": STARK_S011_PHRASES,
        "en_phrases": STARK_S011_PHRASES_EN,
        "en": "Wow… It's gold as far as the eye can see.",
        "panel": "panels/jap/panel_s011Jap.png",
    },
}
STARK_S011_PROMPT_PART1 = (
    "昼の空の下。十代の少年が黄金の景色を見つめ、小声で柔らかく「すごいな」と呟く。"
    "声量は弱め、息が混じる。好意的な感心。張り上げない。「な…」は優しく長く。"
    + STARK_S011_JP_TONE
)
STARK_S011_PROMPT_PART2 = (
    "続けて、間を空けず一続きで小声のまま「見渡す限りの黄金だ」。"
    "見渡す限りのから黄金だまで息を切らさず流す。ナレーション調にしない。"
    "柔らかい感動の「だ」で締める。皮肉・冷たい断定・張り上げ禁止。"
    + STARK_S011_JP_TONE
)
STARK_S011_PROMPT_PART3 = STARK_S011_PROMPT_PART2  # legacy alias
STARK_S011_PROMPTS = (STARK_S011_PROMPT_PART1, STARK_S011_PROMPT_PART2)
STARK_S011_PROMPT = STARK_S011_PROMPT_PART1 + " " + STARK_S011_PROMPT_PART2
STARK_S011_PROMPT_EN = (
    "Daytime MCU. Teen boy speaks softly at endless gold—quiet gentle wow, hushed continuing "
    "awe, then soft impressed 'it's gold.' Low volume, breathy, sincere, never loud or sarcastic."
)
STARK_S011_DIALOGUE_START_SEC = 0.85
STARK_S011_PAUSE_SEC = 0.55

# v1 (retired): うわ…全部、金色だな。 — too brash
STARK_S012_PHRASES_V1 = ("うわ…全部、金色だな。",)
# v2 (retired): …本当に、全部黄金か。 — flat か reads sarcastic / rhetorical on Qwen
STARK_S012_PHRASES_V2 = ("…はぁ。", "…本当に、全部黄金か。")

# v3 (retired): えっ… — reads confused/baffled, not impressed
STARK_S012_PHRASES_V3 = ("えっ…", "すごい…全部、金色なんだ…")

# v4: impressed teen (no panel line — all balloons are Frieren's; see STARK_S012_DIALOGUE)
STARK_S012_PHRASES = ("すごい…", "全部、金色なんだ…")
STARK_S012_PHRASES_EN = ("Wow…", "It's all gold…")
STARK_S012_LANGUAGE = "Japanese"
STARK_S012_DIALOGUE = {
    "Frieren": {
        "ja_phrases": FRIEREN_S012_PHRASES,
        "note": "All tails on panel_s012jap → Frieren (center); RTL right column then left bubble.",
    },
    "Stark": {
        "ja_phrases": STARK_S012_PHRASES,
        "ja_note": "Silent on panel — optional animation stem: impressed, not confused.",
        "en_phrases": STARK_S012_PHRASES_EN,
        "en": " ".join(STARK_S012_PHRASES_EN),
        "canon_on_page": "S008: えぇ… only",
    },
}
STARK_S012_PROMPT_PART1 = (
    "広い展望。十代の少年が黄金の城塞と街並みを初めて見て、素直に感心して「すごい」。"
    "褒め言葉・感嘆。困惑の「えっ」、戸惑い、皮肉、呆れは一切入れない。穏やかに感動。"
    + STARK_JP_TONE
)
STARK_S012_PROMPT_PART2 = (
    "続けて、圧倒的な景色に見とれながら「全部、金色なんだ」と感心して呟く。"
    "語尾は柔らかい発見のなんだ…。疑問・反語・不安な震えにしない。感動が主。"
    + STARK_JP_TONE
)
STARK_S012_PROMPTS = (STARK_S012_PROMPT_PART1, STARK_S012_PROMPT_PART2)
STARK_S012_PROMPT = STARK_S012_PROMPT_PART1 + " " + STARK_S012_PROMPT_PART2
STARK_S012_PROMPT_EN = (
    "Wide backs toward gilt Weise. Teenage warrior quietly impressed by the golden vista—"
    "admiring wow, then soft awe at the scale. Not confused, not sarcastic. Young English dub."
)
STARK_S012_DIALOGUE_START_SEC = 2.5
STARK_S012_PAUSE_SEC = 0.55

# S006 — ch.81 B2 / `002.jpg` row 3 middle
# Story ref (JP): [`panels/jap/panel_s006jap.png`] · still: [`panels/eng/panel_s006.png`]
FRIEREN_S006_PHRASES_EN = (
    "For it not to go through the Continental Magic Association gives the feeling that it will spell trouble, hm?",
    "It doesn't seem to be an official request either, so we should be able to refuse, shouldn't we?",
)
FRIEREN_S006_PHRASES = (
    "大陸魔法協会も通さないってことは厄介事の予感がするね。",
    "正式な依頼って訳でもなさそうだし、断っちゃっていいんじゃない。",
)
FRIEREN_S006_LANGUAGE = "Japanese"
FRIEREN_S006_DIALOGUE = {
    "Fern": {
        "ja": "あまり乗り気じゃありませんね。",
        "ja_reading": "Amari noriki ja arimasen ne.",
        "en": "You do not seem particularly enthusiastic, do you?",
    },
    "Frieren": {
        "ja": "大陸魔法協会も通さないってことは厄介事の予感がするね。正式な依頼って訳でもなさそうだし、断っちゃっていいんじゃない。",
        "ja_phrases": FRIEREN_S006_PHRASES,
        "en_phrases": FRIEREN_S006_PHRASES_EN,
        "en": " ".join(FRIEREN_S006_PHRASES_EN),
    },
}
FRIEREN_S006_PROMPT = (
    "昼の森のキャンプ。焚き火のフェルンに向かって、木に寄りかかって本を読むフリーレン。"
    "非公式の依頼への淡々とした不満。感情を込めないフラットな若い女性エルフの日本語。"
    + FRIEREN_JP_TONE
)
FRIEREN_S006_PROMPT_EN = (
    "Daytime forest camp. Frieren leaning on tree, reading, replying flatly to Fern by the fire. "
    "Unenthusiastic about an unofficial Lernen request—not alarmed, pragmatic unease. "
    "Soft unhurried English dub; matter-of-fact; never bubbly or loud."
)
FRIEREN_S006_PAUSE_SEC = 0.6
# ~9s target on 10s Kling (v2 full line ~11s @ pause 0.6).
FRIEREN_S006_PAUSE_SEC_COMPACT = 0.35
FRIEREN_S006_PROMPT_PART1 = (
    "昼のキャンプ。本を読みながら、協会を通さない依頼への厄介な予感を淡々と述べる。"
    "落ち着いたフラットな日本語。末尾は軽いね。"
    + FRIEREN_JP_TONE
)
FRIEREN_S006_PROMPT_PART2 = (
    "昼のキャンプ。正式な依頼ではなさそうだから断ってよい、という実務的な結論。"
    "フラットで matter-of-fact な日本語。本は手放さない。"
    + FRIEREN_JP_TONE
)
FRIEREN_S006_PROMPT_PART1_COMPACT = (
    "昼のキャンプ。本を読みながら厄介な予感を淡々と一言。テンポやや早め、間を詰め、簡潔に。"
    "フラットな日本語。末尾のねは短く。"
    + FRIEREN_JP_TONE
)
FRIEREN_S006_PROMPT_PART2_COMPACT = (
    "続けて実務的な結論——正式な依頼ではないから断れる、と短く述べる。"
    "やや早めのテンポ、間を詰め、フラット。本は手放さない。"
    + FRIEREN_JP_TONE
)
FRIEREN_S006_PROMPT_PART1_EN = (
    "Daytime camp. Frieren flat and unhurried, eyes on her book, pragmatic unease about trouble "
    "when a request bypasses the Continental Magic Association. Soft trailing hm; English dub."
)
FRIEREN_S006_PROMPT_PART2_EN = (
    "Daytime camp. Frieren matter-of-fact conclusion—they can refuse an unofficial request. "
    "Flat calm English dub, soft trailing shouldn't we; still reading at the tree."
)
FRIEREN_S006_DIALOGUE_START_SEC = 0.55

# Fern S006 — speaks first (camp fire → Frieren at tree); story: panel_s006jap.png
FERN_S006_PHRASES = ("あまり乗り気じゃありませんね。",)
FERN_S006_PHRASES_EN = ("You do not seem particularly enthusiastic, do you?",)
FERN_S006_LANGUAGE = "Japanese"
FERN_S006_PROMPT = (
    "昼の森のキャンプ。焚き火のそばから、木で本を読むフリーレンへ向けた控えめな問いかけ。"
    "非公式の依頼にあまり乗り気ではない、という丁寧な指摘。心配しすぎず、ですます調、静か。末尾のねは軽く。"
    + FERN_JP_TONE
)
FERN_S006_PROMPT_EN = (
    "Daytime forest camp. Fern by the campfire, addressing Frieren at the tree with quiet polite concern—"
    "not very enthusiastic about this unofficial request. Measured young female elf, not whining or bubbly."
)
# Before Frieren reply on ~5s Kling (Frieren @ 0.55s).
FERN_S006_DIALOGUE_START_SEC = 0.35

# Voice clone ref: JP anime dub [`fireren Japan.mp4`] (compilation; S008 line not in file).
FRIEREN_JP_SOURCE_VIDEO = ROOT / "fireren Japan.mp4"
FRIEREN_JP_VOCALS_WAV = VOICE_REFS_WORK / "frieren_jp_vocals.wav"
FRIEREN_JP_QWEN_REF_WAV = VR_JP_FRIEREN / "frieren_jp_qwen_ref.wav"
FRIEREN_JP_QWEN_REF_TXT = VR_JP_FRIEREN / "frieren_jp_qwen_ref.txt"
FRIEREN_JP_QWEN_REF_META = VR_JP_FRIEREN / "frieren_jp_qwen_ref.json"

# Production ref (2026-06-03): JP dub timbre @ ~24.6s Frieren solo window in compilation
FRIEREN_QWEN_REF_WAV = FRIEREN_JP_QWEN_REF_WAV
FRIEREN_QWEN_REF_TXT = FRIEREN_JP_QWEN_REF_TXT
FRIEREN_QWEN_REF_META = FRIEREN_JP_QWEN_REF_META

# Legacy refs
FRIEREN_QWEN_REF_15S_WAV = VOICE_REFS_WORK / "frieren_qwen_ref_15s.wav"
FRIEREN_1MIN_QWEN_REF_WAV = VR_EN_FRIEREN / "frieren_1min_qwen_ref.wav"
FRIEREN_1MIN_QWEN_REF_TXT = VR_EN_FRIEREN / "frieren_1min_qwen_ref.txt"
FRIEREN_1MIN_QWEN_REF_META = VR_EN_FRIEREN / "frieren_1min_qwen_ref.json"

# Legacy v4 long ref (fallback only)
FRIEREN_ENG_DUB_REF_SECONDS = 130.0
FRIEREN_ENG_DUB_REF_SKIP = 0.0
FRIEREN_ENG_DUB_REF_WAV = VOICE_REFS_WORK / "frieren_eng_dub_ref_130s_skip0.wav"


def _audio_ext_from_url(url: str) -> str:
    low = url.split("?", 1)[0].lower()
    for ext in (".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"):
        if low.endswith(ext):
            return ext
    return ".mp3"


def save_audio_from_result(result: dict, key: str, dest: Path) -> Path:
    block = result.get(key)
    url = None
    if isinstance(block, dict):
        url = block.get("url")
    elif isinstance(block, str):
        url = block
    if not url:
        raise RuntimeError(f"No audio URL at {key}: {result}")
    out = dest.with_suffix(_audio_ext_from_url(url))
    download_file(url, out)
    return out


def load_reference_text(ref_txt: Path | None = None) -> str:
    path = ref_txt or FRIEREN_QWEN_REF_TXT
    if not path.is_file():
        raise FileNotFoundError(
            f"Missing reference transcript: {path}\nRun: python prepare_frieren_qwen_ref.py"
        )
    text = path.read_text(encoding="utf-8-sig").strip()
    if not text:
        raise ValueError(f"Empty reference transcript: {path}")
    return text


def load_fern_reference_text(ref_txt: Path | None = None) -> str:
    path = ref_txt or FERN_QWEN_REF_TXT
    if not path.is_file():
        raise FileNotFoundError(
            f"Missing reference transcript: {path}\n"
            "Run: python prepare_fern_qwen_ref.py"
        )
    text = path.read_text(encoding="utf-8-sig").strip()
    if not text:
        raise ValueError(f"Empty reference transcript: {path}")
    return text


def load_stark_reference_text(ref_txt: Path | None = None) -> str:
    path = ref_txt or STARK_QWEN_REF_TXT
    if not path.is_file():
        raise FileNotFoundError(
            f"Missing reference transcript: {path}\n"
            "Run: python prepare_frieren_qwen_ref.py --source ..\\voice_refs\\starksource_vocals.wav "
            "--skip-demucs --out-wav \"..\\Voice Reference\\Japanese\\Stark\\stark_jp_qwen_ref.wav\" "
            "--out-txt \"..\\Voice Reference\\Japanese\\Stark\\stark_jp_qwen_ref.txt\" "
            "--out-meta \"..\\Voice Reference\\Japanese\\Stark\\stark_jp_qwen_ref.json\""
        )
    text = path.read_text(encoding="utf-8-sig").strip()
    if not text:
        raise ValueError(f"Empty reference transcript: {path}")
    return text


def load_denken_reference_text(ref_txt: Path | None = None) -> str:
    path = ref_txt or DENKEN_QWEN_REF_TXT
    if not path.is_file():
        raise FileNotFoundError(
            f"Missing reference transcript: {path}\n"
            "Run: python isolate_vocals_fal.py ..\\voice_refs\\denkensource.mp4 "
            "--out ..\\voice_refs\\denken_vocals.wav\n"
            "Then: python prepare_frieren_qwen_ref.py --source ..\\voice_refs\\denken_vocals.wav "
            "--skip-demucs --out-wav \"..\\Voice Reference\\Japanese\\Denken\\denken_jp_qwen_ref.wav\" "
            "--out-txt \"..\\Voice Reference\\Japanese\\Denken\\denken_jp_qwen_ref.txt\" "
            "--out-meta \"..\\Voice Reference\\Japanese\\Denken\\denken_jp_qwen_ref.json\""
        )
    text = path.read_text(encoding="utf-8-sig").strip()
    if not text:
        raise ValueError(f"Empty reference transcript: {path}")
    return text


def extract_eng_dub_ref(
    dest: Path,
    *,
    seconds: float,
    skip: float,
    source: Path | None = None,
) -> Path:
    src = source or (
        ROOT / "video source" / "Dub Frieren being for 2 minutes and 15 seconds [IkZiiuI-NTM].webm"
    )
    if not src.is_file():
        raise FileNotFoundError(f"Missing dub source: {src}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            str(skip),
            "-i",
            str(src),
            "-t",
            str(seconds),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "44100",
            str(dest),
        ],
        check=True,
        capture_output=True,
    )
    return dest


def append_trailing_silence(ref_wav: Path, *, silence_sec: float = REF_ICL_TRAILING_SILENCE_SEC) -> Path:
    """Pad ref tail so Qwen ICL does not end on った / た and bleed into TTS starts."""
    if silence_sec <= 0:
        return ref_wav
    out = ref_wav.with_name(f"{ref_wav.stem}_icl_pad{ref_wav.suffix}")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(ref_wav),
            "-f",
            "lavfi",
            "-i",
            f"anullsrc=r=44100:cl=mono,atrim=duration={silence_sec:.3f}",
            "-filter_complex",
            "[0:a][1:a]concat=n=2:v=0:a=1[out]",
            "-map",
            "[out]",
            str(out),
        ],
        check=True,
        capture_output=True,
    )
    return out


def embedding_url_from_clone_result(clone: dict) -> str:
    emb = clone.get("speaker_embedding") or clone.get("speaker_voice_embedding")
    if isinstance(emb, dict) and emb.get("url"):
        return str(emb["url"])
    raise RuntimeError(f"Qwen clone failed: {clone}")


def clone_voice(
    ref_wav: Path,
    reference_text: str | None = None,
    *,
    icl_trailing_silence_sec: float = REF_ICL_TRAILING_SILENCE_SEC,
) -> str:
    upload_path = append_trailing_silence(ref_wav, silence_sec=icl_trailing_silence_sec)
    ref_url = fal_client.upload_file(str(upload_path))
    args: dict = {"audio_url": ref_url}
    if reference_text:
        args["reference_text"] = reference_text
    clone = fal_client.subscribe(QWEN_CLONE, arguments=args, with_logs=True)
    if not isinstance(clone, dict):
        raise RuntimeError(f"Qwen clone failed: {clone}")
    return embedding_url_from_clone_result(clone)


def synthesize(
    text: str,
    embedding_url: str,
    out: Path,
    *,
    language: str = "English",
    prompt: str = DEFAULT_PROMPT,
    reference_text: str | None = None,
    use_reference_text_on_tts: bool = False,
) -> Path:
    args: dict = {
        "text": text,
        "language": language,
        "speaker_voice_embedding_file_url": embedding_url,
        "prompt": prompt,
    }
    # Re-sending reference_text on every phrase re-triggers ICL tail spill ("ta" prefix).
    if reference_text and use_reference_text_on_tts:
        args["reference_text"] = reference_text
    tts = fal_client.subscribe(QWEN_TTS, arguments=args, with_logs=True)
    if not isinstance(tts, dict):
        raise RuntimeError(f"Qwen TTS failed: {tts}")
    return save_audio_from_result(tts, "audio", out)


def _probe_sample_rate(path: Path) -> int:
    r = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=sample_rate",
            "-of",
            "csv=p=0",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return int(float(r.stdout.strip()))


def _normalize_audio_label(
    index: int,
    *,
    fade_in_sec: float = 0.0,
    fade_out_sec: float = 0.0,
) -> str:
    """Decode to mono PCM with optional micro-fades at clip edges."""
    chain = (
        f"[{index}:a]aresample=24000,aformat=sample_fmts=fltp:channel_layouts=mono,"
        f"asetpts=PTS-STARTPTS"
    )
    if fade_in_sec > 0:
        chain += f",afade=t=in:st=0:d={fade_in_sec:.3f}"
    if fade_out_sec > 0:
        chain += f",areverse,afade=t=in:st=0:d={fade_out_sec:.3f},areverse"
    return chain + f"[a{index}]"


def export_dialogue_wav(src: Path, wav: Path) -> Path:
    """Decode TTS stem to mono PCM WAV (same resample path as concat_with_pauses)."""
    wav.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-af",
            "aresample=24000,aformat=sample_fmts=fltp:channel_layouts=mono",
            "-ar",
            "44100",
            "-c:a",
            "pcm_s16le",
            str(wav),
        ],
        check=True,
        capture_output=True,
    )
    return wav


def concat_with_pauses(parts: list[Path], pause_sec: float, out: Path) -> Path:
    """Join audio clips with fixed silence gaps (ffmpeg PCM, no anullsrc clicks)."""
    if not parts:
        raise ValueError("concat_with_pauses: no parts")
    if len(parts) == 1:
        if parts[0].resolve() != out.resolve():
            out.write_bytes(parts[0].read_bytes())
        return out

    out.parent.mkdir(parents=True, exist_ok=True)
    # Fade-in on phrase 2+ can sound like a click; ICL spill is fixed at ref/TTS layer.
    fade = 0.015
    inputs: list[str] = []
    for p in parts:
        inputs.extend(["-i", str(p)])

    chain: list[str] = []
    for i in range(len(parts)):
        fin = fade if i > 0 else 0.0
        fout = fade if i < len(parts) - 1 else 0.0
        chain.append(_normalize_audio_label(i, fade_in_sec=fin, fade_out_sec=fout))

    # Pad silence onto each clip except the last (avoids anullsrc boundary clicks).
    padded_labels: list[str] = []
    for i in range(len(parts) - 1):
        chain.append(f"[a{i}]apad=pad_dur={pause_sec:.3f}[p{i}]")
        padded_labels.append(f"[p{i}]")
    padded_labels.append(f"[a{len(parts) - 1}]")

    n = len(padded_labels)
    chain.append(f"{''.join(padded_labels)}concat=n={n}:v=0:a=1[out]")
    filt = ";".join(chain)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            *inputs,
            "-filter_complex",
            filt,
            "-map",
            "[out]",
            "-c:a",
            "libmp3lame",
            "-q:a",
            "2",
            str(out),
        ],
        check=True,
        capture_output=True,
    )
    return out


def synthesize_frieren_phrases(
    embedding_url: str,
    out: Path,
    *,
    phrases: tuple[str, ...],
    prompts: tuple[str, ...],
    reference_text: str | None = None,
    pause_sec: float = 0.55,
    language: str = FRIEREN_S008_LANGUAGE,
) -> Path:
    """Multi-phrase Frieren line with explicit inter-phrase pauses."""
    if len(phrases) != len(prompts):
        raise ValueError("phrases and prompts must have the same length")
    tmp_dir = out.parent
    stem = out.stem
    parts: list[Path] = []
    for i, (text, prompt) in enumerate(zip(phrases, prompts)):
        part = tmp_dir / f"{stem}_p{i}.mp3"
        synthesize(
            text,
            embedding_url,
            part,
            prompt=prompt,
            reference_text=reference_text,
            language=language,
            use_reference_text_on_tts=False,
        )
        parts.append(part)
    return concat_with_pauses(parts, pause_sec, out)


def synthesize_fern_phrases(
    embedding_url: str,
    out: Path,
    *,
    phrases: tuple[str, ...],
    prompts: tuple[str, ...],
    pause_sec: float = 0.5,
    language: str = FERN_S004_LANGUAGE,
) -> Path:
    """Multi-phrase Fern line with inter-phrase pauses (no reference_text on TTS)."""
    if len(phrases) != len(prompts):
        raise ValueError("phrases and prompts must have the same length")
    tmp_dir = out.parent
    stem = out.stem
    parts: list[Path] = []
    for i, (text, prompt) in enumerate(zip(phrases, prompts)):
        part = tmp_dir / f"{stem}_p{i}.mp3"
        synthesize(
            text,
            embedding_url,
            part,
            prompt=prompt,
            reference_text=None,
            language=language,
            use_reference_text_on_tts=False,
        )
        parts.append(part)
    return concat_with_pauses(parts, pause_sec, out)


def synthesize_s004_fern(
    embedding_url: str,
    out_mp3: Path,
    wav_out: Path,
    *,
    prompt: str = FERN_S004_PROMPT,
    phrase: str = FERN_S004_PHRASES[0],
    language: str = FERN_S004_LANGUAGE,
) -> Path:
    """S004 Fern honorific — clone-only reference_text; clean PCM WAV export."""
    synthesize(
        phrase,
        embedding_url,
        out_mp3,
        prompt=prompt,
        reference_text=None,
        language=language,
        use_reference_text_on_tts=False,
    )
    return export_dialogue_wav(out_mp3, wav_out)


def synthesize_s005_fern(
    embedding_url: str,
    out_mp3: Path,
    wav_out: Path,
    *,
    phrases: tuple[str, ...] = FERN_S005_PHRASES,
    prompts: tuple[str, ...] = FERN_S005_PROMPTS,
    pause_sec: float = FERN_S005_PAUSE_SEC,
    language: str = FERN_S005_LANGUAGE,
) -> Path:
    """S005 letter read — split JP phrases + PCM WAV export."""
    synthesize_fern_phrases(
        embedding_url,
        out_mp3,
        phrases=phrases,
        prompts=prompts,
        pause_sec=pause_sec,
        language=language,
    )
    return export_dialogue_wav(out_mp3, wav_out)


def synthesize_s006_fern(
    embedding_url: str,
    out_mp3: Path,
    wav_out: Path,
    *,
    prompt: str = FERN_S006_PROMPT,
    phrase: str = FERN_S006_PHRASES[0],
    language: str = FERN_S006_LANGUAGE,
) -> Path:
    """S006 camp unease — single JP balloon; PCM WAV export."""
    synthesize(
        phrase,
        embedding_url,
        out_mp3,
        prompt=prompt,
        reference_text=None,
        language=language,
        use_reference_text_on_tts=False,
    )
    return export_dialogue_wav(out_mp3, wav_out)


def synthesize_s004_frieren(
    embedding_url: str,
    out_mp3: Path,
    wav_out: Path,
    *,
    prompt: str = FRIEREN_S004_PROMPT,
    phrase: str = FRIEREN_S004_PHRASES[0],
    language: str = FRIEREN_S004_LANGUAGE,
) -> Path:
    """S004 single balloon — clone-only reference_text; clean PCM WAV export."""
    synthesize(
        phrase,
        embedding_url,
        out_mp3,
        prompt=prompt,
        reference_text=None,
        language=language,
        use_reference_text_on_tts=False,
    )
    return export_dialogue_wav(out_mp3, wav_out)


def synthesize_s016_frieren(
    embedding_url: str,
    out_mp3: Path,
    wav_out: Path,
    *,
    prompt: str = FRIEREN_S016_PROMPT,
    phrase: str = FRIEREN_S016_PHRASES[0],
    language: str = FRIEREN_S016_LANGUAGE,
) -> Path:
    """S016 single balloon — Denken meet; clone-only reference_text; clean PCM WAV export."""
    synthesize(
        phrase,
        embedding_url,
        out_mp3,
        prompt=prompt,
        reference_text=None,
        language=language,
        use_reference_text_on_tts=False,
    )
    return export_dialogue_wav(out_mp3, wav_out)


def synthesize_s013_frieren(
    embedding_url: str,
    out_mp3: Path,
    wav_out: Path,
    *,
    prompt: str = FRIEREN_S013_PROMPT,
    phrase: str = FRIEREN_S013_PHRASES[0],
    language: str = FRIEREN_S013_LANGUAGE,
) -> Path:
    """S013 single balloon — great barrier / Macht sealed?; clone-only reference_text; clean PCM WAV."""
    synthesize(
        phrase,
        embedding_url,
        out_mp3,
        prompt=prompt,
        reference_text=None,
        language=language,
        use_reference_text_on_tts=False,
    )
    return export_dialogue_wav(out_mp3, wav_out)


def synthesize_s014_frieren(
    embedding_url: str,
    out: Path,
    *,
    reference_text: str | None = None,
    pause_sec: float = FRIEREN_S014_PAUSE_SEC,
    prompts: tuple[str, ...] = FRIEREN_S014_PROMPTS,
    phrases: tuple[str, ...] = FRIEREN_S014_PHRASES,
    language: str = FRIEREN_S014_LANGUAGE,
) -> Path:
    """S014 two-beat MCU — mild surprise + request/warden explanation."""
    return synthesize_frieren_phrases(
        embedding_url,
        out,
        phrases=phrases,
        prompts=prompts,
        reference_text=reference_text,
        pause_sec=pause_sec,
        language=language,
    )


def synthesize_s008_frieren(
    embedding_url: str,
    out: Path,
    *,
    reference_text: str | None = None,
    pause_sec: float = FRIEREN_S008_PAUSE_SEC,
    prompt_part1: str = FRIEREN_S008_PROMPT_PART1,
    prompt_part2: str = FRIEREN_S008_PROMPT_PART2,
    phrases: tuple[str, ...] = FRIEREN_S008_PHRASES,
    language: str = FRIEREN_S008_LANGUAGE,
) -> Path:
    """Two-beat S008 line with an explicit inter-phrase pause."""
    return synthesize_frieren_phrases(
        embedding_url,
        out,
        phrases=phrases,
        prompts=(prompt_part1, prompt_part2),
        reference_text=reference_text,
        pause_sec=pause_sec,
        language=language,
    )


def synthesize_s012_frieren(
    embedding_url: str,
    out: Path,
    *,
    reference_text: str | None = None,
    pause_sec: float = FRIEREN_S012_PAUSE_SEC,
    prompts: tuple[str, ...] = FRIEREN_S012_PROMPTS,
    phrases: tuple[str, ...] = FRIEREN_S012_PHRASES,
    language: str = FRIEREN_S012_LANGUAGE,
) -> Path:
    """S012 Weise overlook — full Frieren monologue (4 phrases, panel tails)."""
    return synthesize_frieren_phrases(
        embedding_url,
        out,
        phrases=phrases,
        prompts=prompts,
        reference_text=reference_text,
        pause_sec=pause_sec,
        language=language,
    )


def synthesize_s011_stark(
    embedding_url: str,
    out: Path,
    *,
    reference_text: str | None = None,
    pause_sec: float = STARK_S011_PAUSE_SEC,
    prompts: tuple[str, ...] = STARK_S011_PROMPTS,
    phrases: tuple[str, ...] = STARK_S011_PHRASES,
    language: str = STARK_S011_LANGUAGE,
) -> Path:
    """S011 MCU — panel_s011Jap: すごいな… + 見渡す限りの黄金だ。"""
    return synthesize_frieren_phrases(
        embedding_url,
        out,
        phrases=phrases,
        prompts=prompts,
        reference_text=reference_text,
        pause_sec=pause_sec,
        language=language,
    )


def synthesize_s012_stark(
    embedding_url: str,
    out: Path,
    *,
    reference_text: str | None = None,
    pause_sec: float = STARK_S012_PAUSE_SEC,
    prompts: tuple[str, ...] = STARK_S012_PROMPTS,
    phrases: tuple[str, ...] = STARK_S012_PHRASES,
    language: str = STARK_S012_LANGUAGE,
) -> Path:
    """S012 backs — optional stem (no Stark balloon; see personality guide)."""
    return synthesize_frieren_phrases(
        embedding_url,
        out,
        phrases=phrases,
        prompts=prompts,
        reference_text=reference_text,
        pause_sec=pause_sec,
        language=language,
    )


def synthesize_s016_denken(
    embedding_url: str,
    out: Path,
    *,
    reference_text: str | None = None,
    pause_sec: float = DENKEN_S016_PAUSE_SEC,
    prompts: tuple[str, ...] = DENKEN_S016_PROMPTS,
    phrases: tuple[str, ...] = DENKEN_S016_PHRASES,
    language: str = DENKEN_S016_LANGUAGE,
) -> Path:
    """S016 Denken CU — panel_s016jap: Serie plea + barrier warden."""
    return synthesize_frieren_phrases(
        embedding_url,
        out,
        phrases=phrases,
        prompts=prompts,
        reference_text=reference_text,
        pause_sec=pause_sec,
        language=language,
    )


def synthesize_s006_frieren(
    embedding_url: str,
    out: Path,
    *,
    reference_text: str | None = None,
    pause_sec: float = FRIEREN_S006_PAUSE_SEC,
    prompt_part1: str = FRIEREN_S006_PROMPT_PART1,
    prompt_part2: str = FRIEREN_S006_PROMPT_PART2,
    phrases: tuple[str, ...] = FRIEREN_S006_PHRASES,
    language: str = FRIEREN_S006_LANGUAGE,
) -> Path:
    """S006 camp debate — two Frieren balloons with pause between."""
    return synthesize_frieren_phrases(
        embedding_url,
        out,
        phrases=phrases,
        prompts=(prompt_part1, prompt_part2),
        reference_text=reference_text,
        pause_sec=pause_sec,
        language=language,
    )


def load_registry() -> dict:
    if REGISTRY_PATH.is_file():
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return {}


def save_registry(data: dict) -> None:
    REGISTRY_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _ref_duration(ref_wav: Path) -> float:
    if FRIEREN_QWEN_REF_META.is_file() and ref_wav == FRIEREN_QWEN_REF_WAV:
        meta = json.loads(FRIEREN_QWEN_REF_META.read_text(encoding="utf-8"))
        return float(meta.get("duration_sec", 12.0))
    if STARK_QWEN_REF_META.is_file() and ref_wav == STARK_QWEN_REF_WAV:
        meta = json.loads(STARK_QWEN_REF_META.read_text(encoding="utf-8"))
        return float(meta.get("duration_sec", 12.0))
    if DENKEN_QWEN_REF_META.is_file() and ref_wav == DENKEN_QWEN_REF_WAV:
        meta = json.loads(DENKEN_QWEN_REF_META.read_text(encoding="utf-8"))
        return float(meta.get("duration_sec", 12.0))
    if FERN_QWEN_REF_META.is_file() and ref_wav == FERN_QWEN_REF_WAV:
        meta = json.loads(FERN_QWEN_REF_META.read_text(encoding="utf-8"))
        return float(meta.get("duration_sec", 12.0))
    try:
        import soundfile as sf

        return float(sf.info(str(ref_wav)).duration)
    except Exception:
        return 12.0


def resolve_frieren_embedding(force_reclone: bool = False) -> tuple[str, dict]:
    """Curated ref + reference_text (v6 default)."""
    ref_text = load_reference_text()
    return resolve_character_embedding(
        "Frieren",
        ref_wav=FRIEREN_QWEN_REF_WAV,
        ref_seconds=_ref_duration(FRIEREN_QWEN_REF_WAV),
        ref_skip=0.0,
        force_reclone=force_reclone,
        reference_text=ref_text,
    )


def resolve_fern_embedding(force_reclone: bool = False) -> tuple[str, dict]:
    ref_text = load_fern_reference_text()
    return resolve_character_embedding(
        "Fern",
        ref_wav=FERN_QWEN_REF_WAV,
        ref_seconds=_ref_duration(FERN_QWEN_REF_WAV),
        ref_skip=0.0,
        force_reclone=force_reclone,
        reference_text=ref_text,
        prompt_note=FERN_S004_PROMPT,
    )


def resolve_stark_embedding(force_reclone: bool = False) -> tuple[str, dict]:
    ref_text = load_stark_reference_text()
    return resolve_character_embedding(
        "Stark",
        ref_wav=STARK_QWEN_REF_WAV,
        ref_seconds=_ref_duration(STARK_QWEN_REF_WAV),
        ref_skip=0.0,
        force_reclone=force_reclone,
        reference_text=ref_text,
        prompt_note=STARK_S012_PROMPT,
    )


def resolve_denken_embedding(force_reclone: bool = False) -> tuple[str, dict]:
    ref_text = load_denken_reference_text()
    return resolve_character_embedding(
        "Denken",
        ref_wav=DENKEN_QWEN_REF_WAV,
        ref_seconds=_ref_duration(DENKEN_QWEN_REF_WAV),
        ref_skip=0.0,
        force_reclone=force_reclone,
        reference_text=ref_text,
        prompt_note=DENKEN_S016_PROMPT,
    )


def resolve_character_embedding(
    character: str,
    *,
    ref_wav: Path,
    ref_seconds: float,
    ref_skip: float,
    force_reclone: bool = False,
    prompt_note: str = DEFAULT_PROMPT,
    reference_text: str | None = None,
) -> tuple[str, dict]:
    reg = load_registry()
    qwen = reg.setdefault("qwen_speaker_embeddings", {})
    entry = qwen.get(character)
    ref_key = str(ref_wav.relative_to(ROOT))
    ref_text_key = (reference_text or "").strip()
    if (
        entry
        and entry.get("url")
        and not force_reclone
        and entry.get("ref_wav") == ref_key
        and float(entry.get("ref_seconds", 0)) == ref_seconds
        and float(entry.get("ref_skip", 0)) == ref_skip
        and (entry.get("reference_text") or "").strip() == ref_text_key
    ):
        return str(entry["url"]), entry

    if not ref_wav.is_file():
        if ref_wav == FRIEREN_QWEN_REF_WAV:
            raise FileNotFoundError(
                f"Missing {ref_wav}. Run: python prepare_frieren_qwen_ref.py"
            )
        extract_eng_dub_ref(ref_wav, seconds=ref_seconds, skip=ref_skip)

    emb_url = clone_voice(ref_wav, reference_text=reference_text)
    meta = {
        "url": emb_url,
        "ref_wav": ref_key,
        "ref_seconds": ref_seconds,
        "ref_skip": ref_skip,
        "reference_text": ref_text_key,
        "prompt_default": prompt_note,
        "demucs": ref_wav == FRIEREN_QWEN_REF_WAV,
        "cloned_at": datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"),
    }
    qwen[character] = meta
    reg.setdefault("voice_ref_notes", {})[character] = ref_key
    save_registry(reg)
    print(f"Qwen clone {character} from {ref_key} ({ref_seconds:.1f}s)", flush=True)
    return emb_url, meta


def main() -> int:
    if not read_fal_key():
        print("Missing FAL_KEY in .env", file=sys.stderr)
        return 1

    parser = argparse.ArgumentParser(description="Qwen3 TTS with cloned voice")
    parser.add_argument("--character", default="Frieren")
    parser.add_argument("--text", required=True)
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--reclone", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    ref_text = load_reference_text()
    emb, _ = resolve_frieren_embedding(force_reclone=args.reclone)
    if args.out:
        out = args.out.resolve()
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out = ROOT / "outputs" / "voice" / f"{args.character.lower()}_{ts}.mp3"

    path = synthesize(args.text, emb, out, prompt=args.prompt, reference_text=ref_text)
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
