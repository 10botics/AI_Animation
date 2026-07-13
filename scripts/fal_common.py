"""Shared Fal.ai helpers: project root, API key, downloads, shot prompt strings (S001–S018, S075, S076, …).

When adding or changing any *_PROMPT_FLUX string, follow .cursor/skills/nano-banana-2-prompting/SKILL.md and docs/flux-2-pro-prompting-guide.md (Nano Banana 2 is the default edit backend; strings are shared).
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.request import Request, urlopen

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
_ENV_PATH = ROOT / ".env"
load_dotenv(_ENV_PATH, override=False)

# Do not subscribe to these endpoints (confirmed poor fit for this project).
BLACKLISTED_FAL_MODEL_IDS: frozenset[str] = frozenset(
    {
        "fal-ai/stable-cascade/sote-diffusion",
    }
)


def assert_model_allowed(model_id: str) -> None:
    if model_id in BLACKLISTED_FAL_MODEL_IDS:
        raise ValueError(f"Model blocked for this project: {model_id}")


# S001 — **cold_open** MS–WS: chapter title splash `001.jpg` — **Denken** alone on bench (ref: `panels/eng/panel_s001.png`; full-page single panel).
# Story (Stages 1–3): chapter **“El Dorado”** — **gilded / gold-textured world** is the arc (B3+ golden Weise, **S064–S065** gold ground). Cold open **foreshadows** that palette: **warm gilt environment**, not icy neutral only; still **not** full **S010** ridge hero shot.
# Material locks align with **docs/manga-greyscale-to-color.md** (matte vs specular, iron/glass/snow reads).
# Bookends **S059** empty bench; same character as present-timeline Denken (monocle, beard, dark robes).
S001_PROMPT_FLUX = (
    "Fantasy anime television cold open, soft cel shading, painterly background, cinematic medium-to-wide framing — no manga halftone, panel border, or on-screen typography. "
    "**Chapter mood — El Dorado:** light and environment carry a **golden cast** that **foreshadows** the **gilt, metallized** realm tied to **Macht** (see **golden Weise** / **gold-textured town** later in chapter) — "
    "**warm honey and pale-gold bounce** on architecture, **soft amber-peach sky** or **ochre atmospheric haze**, **subtle specular highlights** on woodgrain and bench iron as if dusted with **fine gold pollen**; "
    "**not** the full orange nuclear sunset, **not** a completely naturalistic grey snow read — **restrained fairy-tale gilding** matching the Continuity lock **golden El Dorado = coherent metallic look** when the story turns goldward. "
    "Subject: **one** elderly human mage **Denken** seated **centered** on an **ornate park bench** — **dark wrought-iron** legs with decorative curls (**hard rim speculars** tinted **peach-amber** from sky), **horizontal warm honey-brown wooden** slats with readable grain; "
    "he sits **upright but weary**, hands **clasped in his lap**, gaze **slightly downward** or toward the viewer with **patient gravity**, **not** an action pose. "
    "Denken: **magnificent full beard and mustache** and **short neat scalp hair** — **all warm medium-to-dark brown**, **one consistent brown** on beard, mustache, brows, and scalp beneath the hatless crown; "
    "clear **glass** monocle with **gold** frame **on a fine chain** over one eye, visible when his face reads; **thick brows** in **brown**; **fair** skin with **peachy** warmth where **amber** key hits; "
    "**heavy dark formal coat or robe** — **matte charcoal or blue-black thick wool** or heavy fabric, **fold highlights soft and diffuse**, **not** patent leather or vinyl shine; "
    "**horizontal toggles or frogging** across the chest, **high structured collar** in **ivory or warm white**, dark gloves optional; dignified **barrier-warden** bearing, stocky elder proportions. "
    "**No duplicate Denken**, **no second figure**. "
    "Setting: **wooden clapboard building** directly behind him — **large multi-pane window** with simple muntins; **warm greige** vertical siding; **window glass** shows **amber-peach sky** reflection with subtle vertical streaks, **not** cold steel-blue fill; siding may catch **warm gilt rim light**; trim readable but **not** neon. "
    "Ground: **bright snow or pale plaza** — **soft blue-violet** shadows under **bench and feet**; **sunlit** granules and sparkles pick up **pale champagne-to-gold** glints — still a **quiet** pause space, **not** a busy street; connects visually to **S065**-style **El Dorado ground texture** without copying a full city vista. "
    "Atmosphere: still air, **gilded** ambient fill, shallow depth so bench and figure sit crisply — solitary prologue that **bookends** **S059** **empty bench** in the same **gold-tinged** story world. "
    "**Strip every manga chapter title, logo, stylized series wordmark, English/Japanese lettering, and publisher marks** from the source — "
    "**finished environment and character only**; if a title is needed, add **in post**, not in the model render. "
    "Avoid: chibi, modern street props, crowd, second person, wrong ethnicity swap, watermark, readable text, halftone dots, **cold steel-blue** grading that **erases** the **golden El Dorado** chapter identity, **plastic or patent shine** on the coat that contradicts **matte wool**, **ash or silver hair** on Denken."
)


# S010 — golden ridge wide (ref: `panels/eng/panel_s010.png`, from `003.jpg` wide tier): Fern | Frieren+trunk | Stark.
# Camera: **behind** trio — they face the **gold vista**, **backs** to viewer; refs are rear silhouettes, not frontal hero faces.
S010_PROMPT_FLUX = (
    "Fantasy anime TV production quality, cinematic **wide ridge overlook**, soft daylight, clear depth, soft cel shading, "
    "melancholic fantasy adventure color grade, no manga halftone or panel borders. "
    "**Camera / orientation — match `panel_s010.png`:** viewpoint **behind** the party on a **grassy wooded overlook**; "
    "**all three figures face AWAY from the camera** toward the **distant golden fortress and valley** — **backs and shoulders** to the viewer, "
    "**gazing out** at the gilt landscape; **do not** rotate them **toward** the camera, **no** frontal trio pose, **no** direct faces or eyes to lens. "
    "Exactly THREE people — no fourth, no child, no duplicate twins, no second red-haired warrior. "
    "Figures SMALL in frame; epic scale to distant city. "
    "LEFT-TO-RIGHT (viewer's frame, backs to us): (1) Fern, (2) Frieren center, (3) Stark right. "
    "Heights from behind: Stark tallest and broad; Fern mid; Frieren shortest between them — elf top of head **well below** Fern's crown, modest gap. "
    "(1) Fern — left: **seen from behind** — waist-length straight **purple** hair falling down back, **butterfly hair ornament** ONLY at **back of head**; "
    "light-gray winter jacket, thick braided **blue** scarf visible at shoulders/back, dark blue long dress hem, black boots; hands empty. "
    "(2) Frieren — center: **seen from behind** — **silver-white low twin pigtails**, long **elf ears** may **angle outward** past hair; "
    "**white** cape / coat with **gold** trim read on back; she carries **ONE large RECTANGULAR brown traveling trunk** at her **side** in one hand — "
    "**hero prop**; **no** mage staff on her back, **no** orb staff. "
    "(3) Stark — right: **seen from behind** — **spiky red** hair silhouette, muscular shoulders; "
    "**red** coat, **cream** collar/lapels peeking at neck/shoulder; **massive double-bitted battle AXE** strapped **on his back** — ONLY he has the axe; "
    "crossbody strap; **no** staff in hands. "
    "Environment: valley, forest, and **Fortified City of Weise** all **POLISHED GOLD** — trees, terrain, roofs, walls gilt; "
    "specular gold reflections; soft natural blue sky; readable path toward citadel. "
    "Avoid: figures **facing** or **walking toward** the viewer, five people, two elves, butterfly on white hair, "
    "wrong left-right order, green non-gold city only, chibi, watermark, text."
)


# S002 — **present** WS EST: Northern Weise **forest camp** on `002.jpg` B2 — trio + campfire + axe/packs.
# Structure per BFL prompting_guide_flux2: subject → action → style → context; positive costume locks (cold-travel continuity).
S002_PROMPT_FLUX = (
    "Fantasy anime television wide establishing shot, soft cel shading, painterly forest depth, quiet Northern travel day. "
    "Subject: exactly THREE travelers in one forest clearing — **Fern**, **Frieren**, and **Stark** only; "
    "match their poses, spacing, and depth order from the uploaded reference. "
    "**Preserve horizontal layout, campfire placement, tree masses, and figure scale from the reference** — "
    "translate ink manga to full anime color; **do not mirror** the scene left-right. "
    "Action: **small campfire** alive at the group center; **Stark** sits near the fire on the **viewer's left**, relaxed inward toward the flame; "
    "**Fern** sits with **her back to the camera** in the **foreground**, long straight **purple** hair falling down her back; "
    "**Frieren** sits **against a large tree trunk** deeper in the frame, **reading an open book** in her hands; "
    "she is the **only elf**: **silver-white low twin pigtails**, long horizontal ears, teal-green eyes when her face reads toward the book; "
    "travel packs and bedrolls on the ground; **Stark's massive double-bitted battle axe** rests on the earth beside him — **only Stark** has that axe. "
    "Environment: cool temperate forest clearing, textured trunks and undergrowth, earth and sparse grass, **soft daylight** with a little warm bounce from the flames on nearby fabric and bark — Weise-region camp, not a city or golden vista. "
    "Costume locks: **Fern** — butterfly-style ornament at back of head, cropped **light-gray** winter jacket, **thick braided blue scarf**, **dark blue** long dress, black boots; "
    "**Frieren** — **white** capelet and tunic, **gold** trim, black-and-white **striped inner collar** at neck, dark leggings, brown boots, small **red teardrop** earrings; "
    "**Stark** — spiky **red** hair with darker roots, orange eyes, **red** winter coat with **cream** lapels and cuffs, black fingerless gloves, muscular build. "
    "Mood: calm pause between journeys, faint melancholy; finished illustration only — no speech balloons, panel borders, halftone, or lettering."
)


# S003 — **present** MCU / profile: `002.jpg` row 2 (viewer’s right): **Fern** + **squirrel-like messenger** with bag (ref: `panels/eng/panel_s003.png`).
# BFL order: subject → action → style → context; costume locks align **S002** travel Fern, not Frieren.
S003_PROMPT_FLUX = (
    "Fantasy anime television, medium close profile shot, soft cel shading, cool Northern forest daylight, painterly ground detail. "
    "Subject: young woman **Fern** and one small **squirrel-like forest messenger** — **match `panel_s003.png` staging exactly**, **do not mirror**. "
    "**Facing in image space:** **LEFT-facing profile** — Fern’s **nose, eyes, and chest point toward the LEFT edge of the frame** (never right-facing). "
    "**Seating:** Fern **sits on the forest floor**, hips low, **weight on the ground** — skirt hem and coat touch leaves and dirt, **not standing**, not perched in air. "
    "**Satchel + squirrel** remain in the **RIGHT half** of the frame on the ground; squirrel **also looks toward frame left**, same as Fern. "
    "Fern: long straight **purple** hair with **butterfly-style ornament at the back of the head**; purple eyes if the face reads; "
    "cropped **light-gray** winter jacket, **thick braided blue scarf**, **dark blue** long skirt or dress, black boots; "
    "**profile toward frame left**, gaze toward the satchel; "
    "**wrists and hands visible**, resting on lap or skirt hem, **coat cuffs above the knuckles** so fingers read. "
    "Messenger — **copy `panel_s003.png` silhouette**: **one small slender squirrel**, **rounded head**, **small neat ears**, **upright on hind legs** **inside** an open **tan leather travel satchel** on the ground in the **lower foreground**; "
    "**only head, shoulders, and upper torso rise above the bag rim**; **front paws high on chest** folded like the ink panel; **modest narrow tail** mostly **hidden inside the satchel** opening, **same petite scale** versus Fern as the manga. "
    "Fur **warm gray to pale gray**; gentle TV-anime line, **no human face, no talking cat**. "
    "Action: quiet beat before a letter — Fern and squirrel **both oriented like the manga panel**, calm mutual attention. "
    "Context: forest floor with earth, sparse grass, leaves; dense shrubs and vertical tree trunks behind with soft bokeh; cool daylight. "
    "Mood: gentle stillness; finished illustration only — no speech balloons, panel borders, halftone, or lettering."
)


# S004 — **present** MS (reframed vs manga): **Frieren** **side/profile** foreground + **open grimoire**; **Fern** **deeper in background** + envelope (ref: `panels/eng/panel_s004.png` for identity/locale).
# Intentional **camera change** from the flat panel: upload informs **who / where / what**, not 1:1 lens match.
S004_PROMPT_FLUX = (
    "Fantasy anime television, soft cel shading, cool Northern forest daylight, painterly trees and leaf litter. "
    "**Camera / staging (intentional reframe):** **not** the manga panel’s **flat two-shot angle** — **recompose** from `panel_s004.png` so **Frieren** is shown in a **clear side view / profile**: "
    "**camera sits lateral** — **nose and jaw read in profile**, **long horizontal elf ears** silhouette cleanly, **twin pigtails** fall along the correct depth side; "
    "she remains **foreground** and **dominates the frame**; **open grimoire** held so **page block and spine read edge-on** from this angle. "
    "**Frieren:** petite elf **seated on the ground**, **tree trunk** may **frame her back** or sit **just behind** her shoulder; **silver-white low twin pigtails**, **teal-green eyes** if a sliver of face shows; small **red teardrop earrings**. "
    "**Winter clothing (Frieren):** **heavy Northern travel layers** — **substantial white or cream winter coat / cape**, **warm lining**, **high collar** or **thick wrap scarf**; **gold trim**; **striped inner collar** may **peek**; **dark leggings or trousers**, **sturdy brown winter boots**. "
    "**Grimoire:** **thick bound spellbook**, **spine and boards** visible, **paired pages** with **subtle rule lines / sigils / margins** — **not** loose paper; **Continental Magic Association** beat = official **mage tome**. "
    "**Fern:** **only one Fern** — place her **behind Frieren in depth** (**background / midground plane**), **smaller scale**, **slightly softer** than Frieren, **still readable**; "
    "she **faces toward Frieren’s profile**, long straight **purple** hair, **butterfly-style ornament** at back of head, **light-gray** winter jacket, **thick braided blue scarf**, **dark blue** dress or skirt, black boots; "
    "**sealed envelope** in hand **aimed toward** Frieren as if continuing the beat. **Do not** place Fern **side-by-side** at the same depth as a flat duo shot — **depth separation** is required. "
    "**Global continuity — do not mirror** the whole scene horizontally; keep **forest camp** identity of **S002**/**S003** — trunks, leaf litter, cool light. "
    "**No squirrel**, **no messenger satchel**, **no third traveler** — **Stark** off-panel. "
    "Mood: quiet official request; finished illustration only — no speech balloons, panel borders, halftone, or lettering."
)


# S005 — **present** CU: **Fern** with letter + faded **Lernen** memory telegraph (`002.jpg` bottom tier, read-first panel; ref `panels/eng/panel_s005.png`).
S005_PROMPT_FLUX = (
    "Fantasy anime television, soft cel shading, cinematic close shot, cool Northern forest ambience with **shallow depth** — painterly bokeh. "
    "**Subject:** young mage **Fern** in **foreground** — **three-quarter or profile** read, eyes lowered toward a **folded letter or paper** in her hands; "
    "long straight **purple** hair, **blunt bangs**, **butterfly-style hair ornament** at **back of head**; "
    "cropped **light-gray** winter jacket, **thick braided blue scarf**, **dark blue** skirt or dress visible; composed, serious. "
    "**Memory telegraph (background):** **soft translucent portrait** of elderly human mage **Lernen** — **stern dignified profile**, **short pale grey-white hair**, high **formal collar** and layered robes, **ghostly** and **out of focus** like a **flashback tint** behind Fern — **not** a second solid figure in the room, **not** Denken; **only one live Fern** in sharp focus. "
    "**Lighting:** gentle key on Fern’s face and letter; Lernen read stays **muted** and **dreamlike**. "
    "Mood: quiet weight — **personal request from a First-Class mage** beat; finished illustration only — **no speech balloons**, panel borders, halftone, publisher marks, or readable lettering."
)


# S006 — **present** MS: **Weise camp** — **Frieren** at tree, **Fern** by fire. **Camera locked** to `panels/eng/panel_s006.png` (no pull-back / no S002 wide lens). **Stark** optional **frame-edge** only if **no** reframe.
S006_PROMPT_FLUX = (
    "Fantasy anime television, soft cel shading, cool Northern forest daylight, painterly trunks and leaf litter, **small campfire** warmth. "
    "**Camera / framing — sacred:** **`panel_s006.png` wins** — **keep** the **same lens, distance, camera height, and subject scale** as the upload for **Frieren** and **Fern**; **do not mirror** horizontally; "
    "**do not** pull back to a **wide establishing** view, **do not** zoom out to match **S002** WS, **do not** change hero framing — **stay the same medium shot** the panel implies. "
    "**Frieren:** petite elf **seated on the forest floor**, **back against a large tree trunk**, **open book or grimoire**, **calm flat** expression; **silver-white low twin pigtails**, long **elf ears**, **red teardrop earrings**; "
    "**white or cream winter cape / coat** with **gold trim**, **striped inner collar** may peek, **dark leggings**, **brown boots**; **rectangular travel trunk** may sit **near the tree on the ground**. "
    "**Fern:** young woman **on the forest floor** **near the small campfire**, **engaged toward Frieren**, **seated or low crouch** per reference; "
    "long **purple** hair, **butterfly ornament** at back of head, **light-gray** jacket, **thick braided blue scarf**, **dark blue** lower garments. "
    "**Seating:** **forest floor** — **hips on earth** among leaves; **not** on **logs** or **stumps**; only **Frieren** leans on the **vertical tree** behind her. "
    "**Stark (optional):** **only** if he fits **without** widening the frame — **small partial** at **frame edge**, **seated on ground** by fire, **red coat**, **cream lapels**, **battle axe** on **earth**; "
    "**if** including him **would** require **any** pull-back or **new** camera angle, **omit** (implied **off-panel**). "
    "**Campfire:** small **orange** flames, thin smoke, **warm bounce**. "
    "**Environment:** same trees and ground as the panel — **no** extra camp geography that implies a **wider** map. **No squirrel**, **no duplicate** Frieren or Fern. "
    "Mood: wary negotiation; finished illustration only — no speech balloons, halftone, panel borders, or lettering."
)


# S006A — **insert** MCU: **Fern** by **fire** addresses **Frieren** at tree — **lip-sync-friendly** face read; **same camp** as **S006**, **S005-like** closeness. **No manga panel**; multi-ref from approved **S006** + **S005** stills.
S006A_PROMPT_FLUX = (
    "Fantasy anime television, soft cel shading, cool Northern forest daylight with **warm campfire bounce** on chin and scarf, painterly trunks and leaf litter. "
    "**Camera / framing:** **medium close-up** on **Fern** — **face, eyes, and mouth clearly visible** for dialogue; **chest-up or tighter** than **S006** MS, **same camp geography** as the **S006** master ref; **do not mirror** horizontally. "
    "**Fern (hero):** young mage **foreground**, **seated on forest floor** beside the **small campfire** in the **same seat** as **S006**; "
    "**three-quarter face** turned toward **Frieren** at the **tree** (gaze **off toward frame left**); polite **concerned** expression — lips **neutral-to-speaking**, not obscured by scarf; "
    "long straight **purple** hair, **blunt bangs**, **butterfly-style hair ornament** at **back of head**; "
    "**light-gray** winter jacket, **thick braided blue scarf** (scarf **below** the jaw line), **dark blue** skirt or lower garments; "
    "**hands** may rest on lap or gesture lightly — **no letter**, **no Lernen memory portrait**. "
    "**Frieren (background):** petite elf **soft and smaller** at the **large tree** **left background** — **silver-white pigtails**, **elf ears**, **white or cream cape** with **gold trim**, **calm flat** read; **shallow depth**, **not** a second hero subject. "
    "**Campfire:** **small orange** flames at **frame edge** near Fern — **warm rim** only, **not** night key. "
    "**Seating:** **forest floor** — **not** logs or stumps. **No Stark** unless a **tiny** soft edge read without widening frame. "
    "**No squirrel**, **no duplicate** Fern or Frieren. Mood: **Fern presses** Frieren on enthusiasm — bridge after **S005** letter beat. "
    "Finished illustration only — no speech balloons, halftone, panel borders, or lettering."
)


# S007 — **layered composite** at camp (ref `panels/eng/panel_s007.png`): translucent **Frieren** upper field; **Stark** + **Fern** solid below; **daytime** forest / campfire accent.
S007_PROMPT_FLUX = (
    "Fantasy anime television, soft cel shading, **daytime** Northern forest camp, dramatic **layered composite** (TV memory / inner-thought grammar) — **soft clear daylight** and canopy bounce; **small campfire** may sit in a **lower corner** as a **mild warm accent** only — **not** night-keyed scene, **not** blue moon wash. "
    "**Composition:** match **`panel_s007.png` exactly** — **do not mirror**; **large soft translucent Frieren** bust or portrait **in the upper field** (memory echo), **solid** **Stark** and **Fern** **seated below** in the physical camp plane. "
    "**Frieren echo:** **silver-white low twin pigtails**, **elf ears**, calm **flat** or mildly **annoyed** expression; **ghostly** lowered opacity and soft edges — **not** a second fully opaque standing body overlapping them. "
    "**Stark:** **foreground / mid** seated, **spiky red** hair, **red winter coat** **cream lapels**, **black fingerless gloves**, **axe strap** across chest; somber **listening** posture, gaze low. "
    "**Fern:** **profile** beside him, long **purple** hair, **butterfly-style ornament** at back of head, **light-gray** jacket, **thick braided blue scarf**, **dark blue** skirt; **holds a thick bound grimoire** with **geometric or circular seal** read on the **cover** — **in this panel Fern holds the book**, not Frieren in the solid layer. "
    "**Optional:** abstract **shoulder wound** or **memory glint** in the echo field — **subtle**, not gore-forward. "
    "**No fourth person.** Finished illustration only — no speech balloons, halftone, panel borders, or readable text."
)


# S008 — **present** MS: **daytime** camp **grimoire excitement** (`003.jpg` top tier viewer-left; ref `panels/eng/panel_s008.png`) — **Fern** back to camera; **Frieren** holds **open** tome; **Stark** rear left.
S008_PROMPT_FLUX = (
    "Fantasy anime television, soft cel shading, **daytime** **Weise forest** — **cool Northern daylight** under trees, **sun-flecks**, soft shadows on bark and leaf litter; **primary key is daylight** — **not** night, **not** dusk-blue grading. **No obligatory campfire** unless the reference shows one. "
    "**Subject:** exactly **three** — **Fern**, **Frieren**, **Stark**; **match `panel_s008.png` staging**, **do not mirror**. "
    "**Fern:** **foreground center**, **back or three-quarter to camera**, long **purple** hair, **butterfly ornament**, **light-gray** jacket, **thick braided blue scarf**, **dark blue** skirt; **seated on forest floor**, turned toward **Frieren** — **she is not the one holding the open grimoire** (hands rest or gesture per reference). "
    "**Frieren:** **seated right**, facing Fern, **bright interested** expression — **holds the OPEN grimoire** in her hands; **thick mage tome**, **cover or back board** may show a **circular seal / emblem**; **white or cream coat** **gold trim**, **striped inner collar** may peek, **silver-white pigtails**, **elf ears**, **red teardrop earrings**. "
    "**Stark:** **background left**, **seated on ground**, **spiky red** hair, **red coat** **cream lapels**, strap for **axe**, mild **unenthused** or **confused** slouch — **only Stark** has the **battle axe** if visible. "
    "**All on forest floor** — **not** on log seats. Mood: **grimoire reward / now-we-are-talking** beat. "
    "Finished illustration only — no speech balloons, halftone, panel borders, or lettering."
)


# S009 — **present** WS: trio **walking forest path** toward camera (ref `panels/eng/panel_s009.png`) — **Stark** L, **Frieren** center with **rectangular case**, **Fern** R.
S009_PROMPT_FLUX = (
    "Fantasy anime television, **daylight** forest path, soft cel shading, **sun-flecked** trunks, **dappled** dirt path, bright sky slivers through canopy — **clear Northern travel day**. "
    "**Identity lock:** **Stark**, **Frieren**, **Fern** on the trail — **left-to-right** order **fixed** — **do not mirror** horizontally; same **Weise journey** wardrobe as **`panel_s009.png`**. "
    "**Camera — mild creative bias (I2V-friendly depth):** **avoid** perfectly flat **symmetrical** “mug shot” path staging. Use a **slightly lower** camera height with a **gentle upward** tilt toward the trio **or** a **soft three-quarter** view **along** the path so **foreground path** and **background trunks** show **parallax**; **subtle** off-center framing is **good** — **heroes remain** the **clear cluster**, **not** tiny in frame. **No** extreme Dutch angle, **no** bird’s-eye. "
    "**Staggered footing — asymmetric frozen stride:** **no** lockstep, **no** identical leg angles. **Stark** **left:** **half-step ahead** of the others — one boot **forward** mid-stride, one **pushing off** the dirt; optional **quick glance** toward **Fern** or the **tree line**, **shoulders** slightly **turned** off dead-forward. **Frieren** **center:** **shorter** stride **between** Stark and Fern — feet **offset** timing; **rectangular brown suitcase** in one or both hands with a **natural mid-swing** or **grip adjust**; **pigtails** and coat respond to **light breeze**. **Fern** **right:** **trailing** rhythm — one foot **planting** while the other **lifts**, **hips** **not** square to camera; **hands empty** at sides or **one** briefly **tucking** hair — **no wooden staff**, **no mage staff**, **no orb**; **only Stark** carries the **battle axe** on his back. "
    "**Height / proportions (critical):** **Stark** tallest and broad; **Fern** full **young-adult** woman height; **Frieren** **slender adult elf** — **shorter than Fern** by a **modest** gap (**chin-to-nose** band vs Fern); **not** child height, **not** chibi — preserve **reference** head spacing. "
    "**Stark:** **spiky red** hair, **red winter coat** with **cream lapels** (**no** fluffy fur collar), **black fingerless gloves**, harness strap, **massive double-bitted battle axe** on back. "
    "**Frieren:** **silver-white low twin pigtails**, **white coat** **gold trim**, **striped inner collar**, long ears — **ONE rectangular brown traveling suitcase** at her **side**. "
    "**Fern:** long **purple** hair, **butterfly ornament**, **light-gray** jacket, **thick braided blue scarf**, **dark blue** long skirt — **no large trunk**, **no staff**. "
    "**Exactly three people.** Path, grass, tree bases continuous with **Weise journey**. "
    "Finished illustration only — no speech balloons, halftone, panel borders, or lettering."
)


# S011 — **present** MCU/MS: **Stark** awe at endless **gold** (`003.jpg` tier; ref `panels/eng/panel_s011.png`) — **one** character; faces **gold vista** toward **frame LEFT**.
S011_PROMPT_FLUX = (
    "Fantasy anime television, soft cel shading, **bright daytime**, **cinematic depth**, melancholic fantasy adventure color. "
    "**Subject: only Stark** — **one** young warrior, **no** Fern, **no** Frieren, **no** second figure. "
    "**Match `panel_s011.png`:** **medium close** chest-up framing; Stark placed so he **occupies the right or center-right** of frame **per reference**, **eye level** camera. "
    "**Facing / chirality:** **three-quarter toward frame LEFT** — his **gaze, nose, and posture** aim **left** at an **off-screen golden horizon**; **do not mirror** horizontally. "
    "**Expression:** **awestruck** — **wide eyes**, **mouth slightly open**, soft wonder, **captivated** by scale (wow at gold-to-the-horizon). "
    "**Stark:** **messy spiky red** hair with darker roots, **orange** eyes; **muscular**; **red** winter coat with **cream** lapels and cuffs (no fluff collar), **thick high collar** with **horizontal buckle straps**; **black fingerless gloves**; **dark leather** harness strap **diagonally** across chest; **massive double-bitted battle AXE** on back — **curved axe head** may peek **behind** near shoulder — **only he** has the axe. "
    "**Environment:** background opens into **vast glittering landscape** — **forest, hills, and/or distant walled city** all reading as **polished metallic GOLD** under **clear blue sky**, **specular** glints, **soft atmospheric haze**; negative space **left** of Stark sells the vista he studies. "
    "Avoid: second person, elf ears, purple hair, butterfly clips, mage staff, wrong gaze **toward camera** instead of **left**, halftone, panel borders, watermark, readable text."
)


# S012 — **present** WS: **backs** toward **Fortified City of Weise** — full **gilt** realm (`003.jpg` bottom tier viewer-left; ref `panels/eng/panel_s012.png`).
S012_PROMPT_FLUX = (
    "Fantasy anime television, soft cel shading, **epic wide high-angle** from **behind** the party, **bright clear daytime**, **polished-gold** environment matching **S010** material read, faint melancholy. "
    "**Camera / orientation — match `panel_s012.png`:** all **three** face **away from camera** toward the **distant citadel** — **backs and shoulders** to viewer, **gazing** over a **sea of gold**. **Do not mirror** left-right order. "
    "**Order left-to-right (backs to us):** **Fern**, **Frieren** center, **Stark** right. "
    "**Fern:** long **purple** hair down back, **butterfly ornament** at **back of head**; **light-gray** winter jacket, **thick braided blue scarf**, **dark blue** skirt or dress. "
    "**Frieren:** **silver-white** twin pigtails from behind, **elf ears**; **white or cream coat** **gold trim**; **ONE rectangular brown traveling case** at her **side** in one visible hand — **shorter than Fern** by a **modest** adult gap, **not** child height. "
    "**Stark:** **spiky red** hair silhouette, broad shoulders, **red coat** **cream** lapels, **battle axe** strapped on back, harness strap. "
    "**Environment:** **valley, forest, and Fortified City of Weise** on the hill — **trees, ground, walls, roofs** all **transmuted to continuous POLISHED GOLD**, **specular** glints, readable **winding approach**; **soft blue sky**. "
    "Mood: lore weight — **Macht / El Dorado** gravity. Avoid: fourth figure, frontal faces, non-gold city only, halftone, panel borders, watermark, text. "
    "Finished illustration only — no speech balloons, halftone, panel borders, or lettering."
)


# S013 — **present** WS VFX: **great hemispherical barrier** over **El Dorado / Fortified City of Weise**
# (ref: `panels/eng/panel_s013.png` from `panels/jap/panel_s013jap.png` / page `004.jpg` barrier panel).
# Environment-only establishing plate — strip manga **speech balloon** + **chibi Frieren omake**.
# Stage 2 also tags this beat as **S015** barrier; crop filename **s013** is the working still ID here.
S013_PROMPT_FLUX = (
    "Fantasy anime television establishing shot, soft cel shading, painterly epic landscape, cinematic high-angle aerial, "
    "clear depth and atmospheric haze, finished key art — no manga halftone, panel borders, or lettering. "
    "**Subject: environment only** — **zero people**, **no faces**, **no chibi**, **no floating character heads**, **no mascot cut-ins**. "
    "**Camera — match `panel_s013.png`:** bird's-eye / high three-quarter view looking down on a **vast circular magical barrier dome** "
    "enclosing rolling hills and a **central fortified castle**; same dome scale, castle placement, and corner framing as the reference. "
    "**Barrier:** a **huge translucent hemispherical dome** of soft **pale cyan-to-silver magical energy**, thin luminous rim, "
    "**fine sparkling motes** and gentle refractive shimmer on the shell — readable as a **ward**, not solid glass or a metal sphere. "
    "**Interior landscape (El Dorado continuity with S010 gilt read):** hills, valleys, and forest canopy inside the dome read as "
    "**continuous polished GOLD and champagne metal texture** — trees, ground, and distant slopes **gilded**, soft specular glints, "
    "warm fairy-tale metallization under daylight; **not** plain grey rock, **not** ordinary green forest only. "
    "**Central fortress:** small but sharp **medieval castle / citadel** at the dome center — stone walls, pointed towers, courtyard — "
    "walls and roofs pick up **gold-dusted** highlights matching the gilt realm. "
    "**Exterior:** dark cool forest and rugged terrain **outside** the circle in the frame corners — shadowed greens and deep browns, "
    "clearly **outside** the ward so the dome edge reads. "
    "**Sky / light:** soft daylight above the dome, cool ambient fill on the barrier shell, warm gilt bounce inside. "
    "Mood: awe at the sealed golden homeland — pure VFX landscape plate. "
    "Finished illustration only — no speech balloons, SFX, omake chibi, panel gutters, watermarks, or readable text."
)


# S014 — **present** MCU: Frieren alone after barrier reveal (`004.jpg` row 1; ref `panels/eng/panel_s014.png`).
# stage_02: calm/surprised — barrier job / assist warden request. PREFIX_PRESENT Northern forest.
S014_PROMPT_FLUX = (
    "Fantasy anime television, medium close-up, soft cel shading, cool Northern forest daylight, "
    "painterly tree depth, clear atmospheric perspective, finished key art — no manga halftone, panel borders, or lettering. "
    "**Subject: one person only** — adult elf mage **Frieren** — **no** second figure, **no** chibi insert. "
    "**Camera / facing — three-quarter look LEFT (must not face camera):** MCU head-and-shoulders, forest behind; "
    "head turned **toward frame LEFT**; **gaze locked off-camera left**; **pupils and irises aim left**; "
    "**no** direct eye contact with the lens; **no** frontal portrait stare; "
    "three-quarter cheek and nose silhouette readable; **do not mirror** to face right. "
    "**Expression (wary / on edge — match manga panel_s014jap):** **suspicious alert** read — "
    "**slightly narrowed sharp teal-green eyes** glancing aside, **tense small open mouth**, "
    "chin nestled guarded in the high scarf, brows lightly raised; "
    "**not** soft blank neutral, **not** gentle curiosity only, **not** shocked yell, **not** smiling; "
    "emotional restraint but clearly **uneasy / on guard**. "
    "**Frieren locks:** petite adult elf; **silver-white low twin pigtails** with dark ribbon ties; "
    "**long horizontal elf ears**; thick short rounded brows; large **teal-green** eyes; fair skin; "
    "small **red teardrop earrings** on gold studs. "
    "**Winter travel (present Northern arc):** **thick pale cream scarf** wrapped **high** under the chin; "
    "**white or cream winter coat / capelet** with **gold trim** at collar; striped inner collar may peek; "
    "scarf and coat read **matte soft fabric**, not plastic shine. "
    "**Environment:** dense temperate forest behind her — vertical trunks, layered foliage, soft cool daylight through canopy; "
    "**present** journey beat near the barrier meet, **not** golden city vista, **not** snowfield, **not** campfire. "
    "Mood: quiet reaction looking aside after the great barrier — finished illustration only — "
    "no speech balloons, SFX, panel gutters, watermarks, or readable text."
)


# S034 — **fb_macht** WS: Macht defeat memory (`007.jpg` bottom-right tier; ref `panels/eng/panel_s034.png`).
# Macht costume/color: docs/macht-appearance-reference.md — default run also uploads macht_portrait_three-quarter.png.
# stage_02 B7: younger Frieren kneeling before Macht — aligns **S050** antagonist styling; **not** present-path Stark (S036).
S034_PROMPT_FLUX = (
    "Fantasy anime television, soft cel shading, **flashback memory** palette — **cool desaturated** daylight with **vertical rain**, "
    "softer contrast than present beat, painterly stone depth, subtle vignette. "
    "**Subject: two figures only** — **young Frieren** kneeling or collapsed **on wet stone floor** (small frame, **white twin pigtails**, **light hooded cloak**, seen **from behind or three-quarter back only**) "
    "**and** towering **Macht of El Dorado** standing over her. "
    "**Match panel composition (image 1):** **wide shot** in **stone hall / arcaded courtyard** — **tall fluted columns**, **rounded arches**, **wet flagstone**; "
    "**vertical rain** streaks; Macht **center-right standing**, young Frieren **lower-left kneeling**; **do not mirror** horizontally. "
    "**Macht of El Dorado — anime-accurate locks (image 2 when provided):** **very tall** slender demon lord; "
    "**long slicked-back deep burgundy / magenta hair** (**not** silver-white, **not** pale blonde, **not** black hair); "
    "**exactly two** long **curved pale-beige ridged horns** from **temples** (**not** short stubs, **not** three horns); "
    "**pointed ears**; **pale blue narrow eyes** with **heavy dark eyebags** (tired sleepless look); "
    "**dark forest-green high-collared knee-length tunic** with **gold trim** at standing collar (**not** black military jacket, **not** red coat); "
    "**golden-yellow diagonal chest sash** from **left shoulder** across chest with **white-tipped tassel fringe**; "
    "**three stacked golden arm braces** on **right upper arm** with **long yellow tassels** hanging down; "
    "**red maroon gloves**; **large voluminous dark navy-blue coat** draped **only on left shoulder** — asymmetric, floor-length, heavy fabric (**not** symmetric double-breasted cape, **not** fur-trimmed red mantle); "
    "**dark polished boots**; coat **normal blue fabric** in this beat (**not** mid gold-transform sword); "
    "**regal cold menace**, head tilted **down** at defeated Frieren. "
    "**Young Frieren:** child elf **back to camera** — **low white pigtails**, **hooded travel cloak**, knees on stone — "
    "**not** adult present-timeline scarf Frieren, **not** facing camera. "
    "**Environment:** interior **palace courtyard** arcaded hall — **no** forest, **no** golden Weise vista, **no** present-party Stark or Fern. "
    "Avoid on Macht: medals-only generic officer uniform, silver hair, missing horns, cheerful smirk. "
    "Mood: **defeat memory** after B7 refusal. Finished illustration only — "
    "no speech balloons, halftone, panel borders, watermark, or readable text."
)


# S036 — **present** MCU: **Stark** skeptical on forest path (`007.jpg` left-column lower tier; ref `panels/eng/panel_s036.png`).
# stage_02 B7: dismissive “big deal?” reaction — **not** awe (S011), **not** Macht flashback (S034).
S036_PROMPT_FLUX = (
    "Fantasy anime television, soft cel shading, **cool Northern forest daylight**, cinematic depth, present-journey palette. "
    "**Subject: only Stark** — **one** young warrior, **no** Fern, **no** Frieren, **no** second figure. "
    "**Match `panel_s036.png`:** **medium close-up** chest-up; Stark occupies **right or center-right** of frame **per reference**; **eye-level** camera; **do not mirror** horizontally. "
    "**Facing / chirality:** **three-quarter toward frame LEFT** — **gaze, nose, and posture** aim **left** at off-screen companions; **not** staring into the lens. "
    "**Expression (skeptical / doubtful — match manga):** **unimpressed pushback** — **one brow raised or knit**, **orange eyes** narrowed or side-glancing, "
    "**mouth open** mid retort (“…aren't you making a bit much of it?” / “big deal?” energy); **not** awestruck (S011), **not** furious shout, **not** soft smile. "
    "**Stark locks:** **messy spiky red** hair with darker roots; **muscular** neck and shoulders; **red** winter coat with **cream** lapels and cuffs (**no** fluffy fur collar), "
    "**thick high collar** with **horizontal buckle straps**; **black fingerless gloves** if hands show; **dark leather** harness strap **diagonally** across chest; "
    "**massive double-bitted battle AXE** strap on back may peek near shoulder — **only he** has the axe. "
    "**Environment:** **dense temperate forest** behind him — vertical trunks, layered foliage, soft cool daylight through canopy; "
    "**present** path beat after the Weise refusal — **not** polished **gold** city vista, **not** Macht hall, **not** stone courtyard, **not** campfire close-up. "
    "Mood: skeptical challenge on the trail. Finished illustration only — "
    "no speech balloons, SFX, panel borders, halftone, watermark, or readable text."
)


# S003 variant: same camp beat, **Fern only** — reference used to strip squirrel + satchel critter for a clean plate.
S003_PROMPT_FLUX_FERN_ONLY = (
    "Fantasy anime television, medium close profile shot, soft cel shading, cool Northern forest daylight, painterly ground detail. "
    "**Chirality locked to `panel_s003.png`:** **LEFT-facing profile only** — **Fern’s nose and torso aim toward the LEFT edge of the image** (never right-facing); "
    "cleared leaf-strewn ground fills the **right side** where the bag and animal were — **identical** tree column order left-to-right, **no mirror**. "
    "Subject: **only** young woman **Fern** — **one person** in frame. "
    "**Seating:** **sits directly on the forest floor** — seat and legs grounded, hem on leaves and dirt, **not standing**, not hovering knee pose. "
    "Fern: long straight **purple** hair with **butterfly-style ornament at the back of the head**; purple eyes if visible; "
    "cropped **light-gray** winter jacket with **sleeves tailored to the wrist**, **thick braided blue scarf**, **dark blue** long dress or skirt, black boots; "
    "**same screen position and left-facing profile** as the reference scan. "
    "Hands and arms: **both hands fully visible** resting naturally **on her lap** over the skirt, relaxed fingers, **five fingers each**; "
    "**coat cuffs sit at or just past the wrists** — never baggy tubes that hide the hands; soft fold of sleeve above the wrist is fine. "
    "Environment: **continuous forest ground** — grass, earth, scattered leaves — where the satchel and animal were in a manga source, "
    "blend believable ground and leaf litter; if the reference is already a color plate without squirrel, **extend** only what is needed for hands and cuffs. "
    "**No** squirrel, **no** messenger bag, **no** duplicate people. "
    "Background: same bush mass and tall tree trunks, atmospheric depth, soft daylight. "
    "Mood: quiet solitary pause; finished illustration only — no speech balloons, panel borders, halftone, or lettering."
)


# S003 — **extend camp** pass: keep fern-only **foreground Fern** from upload; add **S002**-consistent mid/background (Frieren, Stark, fire, packs).
# Use as second-stage edit on `S003_fernonly_*.png`, not on raw manga crop.
S003_PROMPT_FLUX_EXTEND_CAMP = (
    "Fantasy anime television, soft cel shading, cool Northern forest day with warm campfire accents, painterly depth, **16:9** framing. "
    "Foreground: **preserve** the uploaded **Fern** figure **unchanged** — same pose, profile direction, purple hair with **butterfly clip**, gray jacket, **blue scarf**, dark skirt, hands on lap, leaf-strewn ground at her knees; **no duplicate Fern**. "
    "Midground and background — **same camp as establishing shot S002**: a forest clearing **behind** Fern with **readable depth** between trunks; "
    "**Frieren** petite elf, **silver-white low twin pigtails**, long horizontal ears, **white capelet** with gold trim, **striped inner collar**, "
    "**leaning against a large tree**, **reading an open book** in her hands; "
    "**Stark** young man, **spiky red hair**, **red winter coat** with **cream lapels and cuffs**, **black fingerless gloves**, "
    "**seated near a small campfire** at the center of the glade, **massive double-bitted battle axe** resting on earth beside him; "
    "**rolled bedrolls** and **travel packs** near the fire ring. "
    "**Campfire** alive with small **orange flames**, thin pale smoke, subtle **warm light** on nearby bark and grass mixing with cool daylight. "
    "Staging: companions **smaller and farther** than Fern — she stays **closest to camera**; sight lines feel like **one continuous party camp** on page 002. "
    "No squirrel, no messenger satchel beat. Finished illustration only — no speech balloons, panel borders, halftone, or lettering."
)


# S003 — **extend camp + courier** pass: add **Frieren TV-style forest messenger squirrel** (upright, **wears** mini satchel + **letter**) on leaves **between Fern and fire**; **Fern looks at it**.
# Single-image /edit: prompt must fully specify critter so the model does not invent a generic squirrel.
S003_PROMPT_FLUX_EXTEND_CAMP_SQUIRREL = (
    "Fantasy anime television, Northern journey cel shading, soft edges, cool forest daylight with **warm campfire** rim light, **16:9**. "
    "**Context, hold upload:** **same** camp blocking **Frieren** at her tree with book, **Stark** by **campfire**, **travel axe**, **bedrolls**, **packs**, trunks and **leaf carpet**; **same** **Fern** body pose, coat, scarf, skirt, and screen direction. "
    "**Subject:** **one small forest post runner squirrel** stands on **open brown leaves** in the **gap between foreground **Fern** and the midground fire ring**, **upright on hind legs**, **small** next to Fern's knees. "
    "**Creature paint:** **rounded fluffy silhouette**, **cool pale grey fur** with a **faint violet-grey** wash on crown and back, **clean white** chest and belly; **wide round black eyes**, **pin dark nose**, **small round ears**; "
    "**full brushy tail** arcing **up** behind; **forepaws gathered high on the chest** in a **polite upright stance**. "
    "**Tiny travel pouch on the squirrel:** **off-white canvas body**, **tan leather flap**, **petite metal clasp**, **thin brown shoulder band**; **flat white paper** **stack** with **one corner lifted** visible **above** the flap like bundled **correspondence**. "
    "**Action:** squirrel **turns toward Fern**; **Fern** gets **only** a **light** eye-line and **brow** shift so she **watches** the **tiny animal** on the **near leaves**. "
    "**Lighting:** clear material read on **fur**, **paper edge**, **clasp**; soft ground shadow. "
    "Mood: quiet camp pause; finished illustration only **without** speech balloons, panel borders, halftone, or lettering."
)


# S003 — **two-reference composite** (`image_urls` = [camp master, squirrel ref]): critter look from upload 2, scene from upload 1.
# Works with `fal-ai/nano-banana-2/edit` and `fal-ai/flux-2-pro/edit` multi-reference inputs.
S003_PROMPT_FLUX_COMPOSITE_SQUIRREL = (
    "Fantasy anime television, **16:9**, Northern journey cel look. "
    "**First reference** = **camp master** — **keep** layout, **Fern**, **Frieren**, **Stark**, **fire**, **gear**. "
    "**Second reference** = **squirrel turnaround** — **transfer** fur (**cool grey**, **white bib**), **wide black eyes**, **bushy tail**, **cream canvas pouch**, **tan flap**, **white paper**, **upright paws-on-chest**. "
    "**Merge:** **courier squirrel** **on leaves** **between Fern and campfire**, **toward Fern**; **Fern** **watches** it. **Image 1** = **world**; **image 2** = **animal + pack** **look**. "
    "Finished illustration only **without** speech balloons, panel borders, halftone, or lettering."
)


# S075 — **present** MS OTS: Denken & adult Frieren; **snow + rock mountain vista** per `panels/eng/panel_s075.png` (**S074** scarf).
# v8: mirror lock. v9: full hair, not balding. v10: white hair (superseded). v11: Denken **brown** scalp hair (anime / wiki); wording positive-only (no “not silver” beside Denken).
S075_PROMPT_FLUX = (
    "Fantasy anime television, medium shot, soft cel shading, painterly background, present Northern arc emotional beat. "
    "Subject: exactly two people — **wide over-the-shoulder** as in the reference: **Frieren on the viewer's left**, **Denken nearer camera on the viewer's right** with **his back to the viewer**, Frieren oriented toward him; **present** journey. "
    "**Preserve left-right layout, pose, two-figure spacing, horizon placement, and scale from the uploaded reference** — same chirality as the panel; translate manga ink to anime paint; one man and one elf only. "
    "Environment (**match the panel, chapter-scale outdoor beat**): **wide snow-covered foreground** with gentle drift texture and pale cool shadows between rolls; "
    "beyond the figures, **layered rolling mountains or high hills** — **dark rock, scree, and cliff faces break through the snow** on slopes (rough stony read, not smooth white domes); "
    "ridgelines step smaller into cool atmospheric haze; **narrow sky band**: overcast grey with soft horizontal streaks, cold diffused light — highland winter, **not** flower meadow, **not** forest clearing, **not** golden city vista. "
    "Light: cold diffuse sun behind haze, soft aerial perspective into distant peaks, subtle blue-grey shadow in snow. "
    "Camera: medium **OTS**, expansive horizontal field, figure–ground separation as in reference. "
    "Frieren: petite adult elf; silver-white low twin tails; long horizontal ears; teal-green eyes; **cream winter coat** with darker trim; **thick pale scarf** wrapped high, chin nested in folds; small red teardrop earrings. "
    "Denken (**appearance from behind only — do not turn him to face camera**): **stocky elderly** silhouette; **back of head shows short neat human scalp hair, warm medium-brown**, even crown-to-nape fullness, well-groomed; "
    "**human ears**; **dark heavy formal overcoat**, **tall stiff collar** framing the back of the neck; **broad rounded shoulders**, dignified still posture; coat deep charcoal to black with subtle **horizontal toggle or frogging** detail if the reference suggests seams — **omit beard and monocle** because this shot does not show his face. "
    "Mood: quiet gravity between allies in the cold heights; finished illustration only, no captions, halftone, or panel borders."
)


# S076 — hero-party flashback meadow (ref: `panels/eng/panel_s076.png`, from `016.jpg` wide tier). **Panel fidelity first:** v2 cast wording; long hex wardrobe blocks removed (they overwrote ref layout).
# Color = light nudge only after matching reference silhouettes; edit lead-in stresses image in generate_s076_ref_edit.py.
S076_PROMPT_FLUX = (
    "Fantasy anime television key art, soft cel shading, painterly background, heroic party flashback memory. "
    "Subject: exactly four traveling heroes together in one spell-made wildflower meadow — Frieren, Himmel, Heiter, and Eisen as young adventuring versions only. "
    "Context and lighting: a forest-enclosed clearing ringed by tall trees; bright sky beyond; sunlight through canopy as soft dappled beams on the flower carpet and figures; "
    "thousands of petals and light blossoms carried on the wind through the whole frame, filling air and depth. "
    "The meadow floor is a continuous dense sheet of small cool-blue wildflowers with green stems, color accent near hex #6B8DC2, reading as one magical species like a single spell-made field — "
    "not a patchwork of unrelated rainbow flower colors. "
    "Camera: extreme wide high angle; all four bodies read small within the vast clearing for awe scale. "
    "Depth staging (critical): the scene must stay layered in depth — Frieren and Himmel share the nearer foreground volume of the meadow; "
    "Heiter and Eisen appear farther up the field, reduced by distance and partially separated, never rearranged into a flat symmetrical front row or studio lineup. "
    "**Preserve each character's pose, facing, and costume proportions from the uploaded reference** — translate ink to anime paint, do not invent a new lineup or new blocking. "
    "After layout matches the panel, gently color-grade costumes toward the series — **each garment keeps its own hue** (no blanket blue cast from the flower field onto cloaks or robes): "
    "Himmel **sky-blue tunic only**; **hero cloak and cape fabric stay pale cream or white**, never dyed blue; "
    "Frieren white mage layers with gold accents and dark leggings; "
    "Heiter **black or charcoal priest cassock and dark vestments only**; scalp hair is green, not the robes; "
    "Eisen **brick-red or deep red travel cape** over **dark brown** undertunic and leather — red stays on the dwarf's mantle only. "
    "Himmel — young human hero, **hair only**: even light-blue bowl-cut, neat rounded silhouette, **blue matched to his tunic**; "
    "**do not recolor his cloak to match hair or tunic** — cloak remains off-white or cream; not white/silver hair, not shaggy shoulder length, **rounded human ears**; "
    "kind eyes when seen, gentle smile; **white or cream hero's cloak** with gold trim hints at collar and shoulders; "
    "he is the calm focal hero beside Frieren at nearer depth. "
    "Young Frieren — petite elf maiden build: clearly shorter than Himmel yet young-adult proportions, never toddler or super-deform chibi; "
    "silver-white low twin pigtails with dark ribbon ties; long horizontal elf ears; thick short brows; large teal-green eyes; "
    "white tunic and capelet with gold trim, black-and-white striped inner collar, small red teardrop earrings. "
    "Heiter — human priest, mild warm expression, **short slicked-back seafoam to mint-green scalp hair only** near hex #8FD4B8, **comb-groomed**, optional **two fine forelock strands** over the brow; "
    "**robes and cassock stay jet black or deep charcoal with gold trim** — hair is green, fabric is dark, **not** white or pale clerical coat; traveling stole; visually distinct from Himmel, never a second blue-haired hero duplicate. "
    "Eisen — dwarf warrior: stocky wide torso, short stature with head height near the humans' waists or mid-chest only, short dark hair and neat beard stubble; "
    "**deep red or brick-red cape or mantle** over practical **dark** travel coat and leather belt; "
    "he must never match Himmel's eye level. "
    "Only these four people exist in frame — contemporary party members stay absent. "
    "Mood: quiet sacred calm, nostalgic courage, no on-image typography, signature, or comic panels."
)


# S016 — **present** WS: forest meet — **Denken** L, **Stark** mid, **Frieren** R (`004.jpg` row 2).
# Ref: `panels/eng/panel_s016.png` (from `panel_s015jap.png` crop); JP balloons: `panels/jap/panel_s015jap.png`.
S016_PROMPT_FLUX = (
    "Fantasy anime television, medium-wide forest encounter, soft cel shading, painterly woodland depth, "
    "cool-to-neutral Northern-country daylight, clear atmospheric perspective, emotional restraint in faces. "
    "Subject: exactly **three** people standing in a **dense forest clearing** — **left to right**: "
    "**Denken**, **Stark**, **Frieren** — **same spacing, scale, and waist-up framing** as the uploaded reference; "
    "**preserve horizontal layout** — **do not mirror** left-right. "
    "**Denken (left):** elderly human mage, **magnificent full brown beard and mustache**, **short neat brown scalp hair**, "
    "**gold monocle on chain** over one eye, **dark heavy formal robes** with **horizontal toggle closures**, "
    "**high structured collar**, dignified weary bearing, shorter than Stark. "
    "**Stark (center):** young warrior, **spiky vivid red hair** with darker roots, **orange eyes**, muscular tall build, "
    "**red winter coat** with **cream lapels and cuffs**, **black fingerless gloves**, **crossbody strap** for **battle axe** on back. "
    "**Frieren (right):** petite adult elf, **silver-white low twin pigtails**, long horizontal ears, **teal-green eyes**, "
    "calm **mild realization** expression; **white double-breasted winter coat**, **thick pale travel scarf** wrapped high, "
    "**gold trim** at collar, **red teardrop earrings**. "
    "Environment: vertical tree trunks, layered foliage, soft diffused forest light, leaf litter at their feet — "
    "**present** journey beat, **not** golden city vista, **not** snowfield. "
    "Mood: quiet first meeting with the barrier warden; finished illustration only — "
    "no speech balloons, panel borders, halftone, SFX, or lettering."
)


# S018 — **present** WS: four at **wood cliff fence** + wooden building (`panel_s018jap.png`).
# L→R: Stark, Fern, Denken, Frieren (rectangular travel trunk). Cliff drop in foreground; forest behind.
S018_PROMPT_FLUX = (
    "Fantasy anime television, wide cliffside encounter, soft cel shading, painterly forest depth, "
    "cool-to-neutral Northern-country daylight with soft sun through canopy, clear atmospheric perspective. "
    "Subject: exactly **four** travelers standing **behind a low wooden fence** — **left to right**: "
    "**Stark**, **Fern**, **Denken**, **Frieren** — **same spacing, scale, and waist-up framing** as the uploaded reference; "
    "**preserve horizontal layout** — **do not mirror** left-right. "
    "**Height / proportions (critical — match reference crown levels):** **Stark** tallest and broad; "
    "**Fern** second-tallest — her crown about **Stark's chin or lower jaw**; "
    "**Frieren** third — **standing taller than Denken** (top of **Frieren's head** clearly **above** top of **Denken's scalp** — beard volume does **not** count as height), still **shorter than Fern**; slender adult elf, **not** chibi; "
    "**Denken** **shortest** in the lineup — stocky elder, **lowest crown** of the four, **shorter than Frieren** despite long beard. "
    "**Stark (left):** young warrior, **spiky vivid red hair**, **red winter coat** with **cream lapels**, "
    "**battle axe** strapped on back with crossbody strap, muscular build. "
    "**Fern:** young human mage, waist-length **purple** hair, **butterfly ornament** at back of head, "
    "cropped **light-gray** winter jacket, **thick braided blue scarf**, **dark blue** long dress, black boots. "
    "**Denken:** elderly human mage, **magnificent full brown beard and mustache**, **short neat brown scalp hair**, "
    "**gold monocle on chain** when face reads, **dark heavy formal robes** with toggle closures, dignified stocky bearing. "
    "**Frieren (right):** petite adult elf, **silver-white low twin pigtails**, long horizontal ears, **teal-green eyes**, "
    "**white** capelet and winter coat with **gold trim**, **thick pale scarf**; carries **one large rectangular brown traveling trunk** in one hand. "
    "Foreground: **two-rail wooden fence** with vertical posts; **rocky cliff edge** visible below the fence line. "
    "Right side: **wooden clapboard building** — gabled roof, **large arched multi-pane window**, simple wooden door, warm honey-brown siding. "
    "Background: dense temperate forest, layered trunks and foliage, soft diffused light — **present** journey, **not** golden city vista. "
    "Mood: quiet pause at a barrier overlook; finished illustration only — "
    "no speech balloons, panel borders, halftone, SFX, or lettering."
)


def read_fal_key() -> str:
    if _ENV_PATH.is_file():
        text = _ENV_PATH.read_text(encoding="utf-8-sig")
        for line in text.splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            if s.upper().startswith("FAL_KEY") and "=" in s:
                _, _, rest = s.partition("=")
                v = rest.strip().strip('"').strip("'")
                if v:
                    return v
    return (os.environ.get("FAL_KEY") or "").strip().strip('"').strip("'")


def download_file(url: str, dest: Path, timeout_s: int = 120) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = Request(url, headers={"User-Agent": "AI_Animation/1.0"})
    with urlopen(req, timeout=timeout_s) as resp:
        dest.write_bytes(resp.read())


def video_url_from_result(result: object) -> str | None:
    """Extract MP4 URL from `fal-ai/kling-video/*/image-to-video` subscribe result."""
    if not isinstance(result, dict):
        return None
    payload = result
    inner = result.get("data")
    if isinstance(inner, dict) and "video" in inner:
        payload = inner
    video = payload.get("video")
    if isinstance(video, dict):
        url = video.get("url")
        if isinstance(url, str):
            return url
    return None


def image_url_from_result(result: object) -> str | None:
    if not isinstance(result, dict):
        return None
    payload = result
    if "images" not in result:
        inner = result.get("data")
        if isinstance(inner, dict) and "images" in inner:
            payload = inner
    images = payload.get("images")
    if not images or not isinstance(images[0], dict):
        return None
    url = images[0].get("url")
    return url if isinstance(url, str) else None


def extension_from_url(url: str) -> str:
    low = url.split("?", 1)[0].lower()
    if low.endswith(".webp"):
        return ".webp"
    if low.endswith(".jpeg") or low.endswith(".jpg"):
        return ".jpg"
    return ".png"


def flux_pro_edit_image_size_match_ref(
    ref_path: Path,
    *,
    max_long_edge: int = 2048,
    align: int = 8,
) -> dict[str, int]:
    """
    `{width, height}` for `fal-ai/flux-2-pro/edit` from the reference file's pixel size.

    Downscales if the long edge exceeds `max_long_edge` (cost + stability). Dimensions
    are snapped down to a multiple of `align` for predictability.

    Requires Pillow. Raises ImportError if Pillow is not installed.
    """
    try:
        from PIL import Image
    except ImportError as e:
        raise ImportError(
            "flux_pro_edit_image_size_match_ref requires Pillow (pip install Pillow)"
        ) from e

    with Image.open(ref_path) as im:
        w, h = im.size
    long_edge = max(w, h)
    if long_edge > max_long_edge:
        scale = max_long_edge / long_edge
        w = int(round(w * scale))
        h = int(round(h * scale))

    def snap(x: int) -> int:
        return max(align, (x // align) * align)

    return {"width": snap(w), "height": snap(h)}
