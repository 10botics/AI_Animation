"""

S009 — Kling 2.6 Pro **image-to-video** from an approved Stage 4 still.



**WS** path: **Stark**, **Frieren** (rectangular case), **Fern** — `panels/panel_s009.png` / **`Tests/Final/`**.



Modes: **`--experiment 1`** handheld + push-in; **`2`** dolly + parallax; **`3`** combined 1+2; **`4`** **TV-anime limited animation** — subtle / slow, **Fern** extra soft, **near-locked camera** (less 3D glide).

Default **`duration` \"5\"**.



Requires: `FAL_KEY` in project `.env`, package `fal-client`.

"""



from __future__ import annotations



import argparse

import json

import os

import sys

from datetime import datetime, timezone

from pathlib import Path



import fal_client



from fal_common import (

    ROOT,

    assert_model_allowed,

    download_file,

    extension_from_url,

    read_fal_key,

    video_url_from_result,

)



SHOT_ID = "S009"

MODEL_ID = "fal-ai/kling-video/v2.6/pro/image-to-video"



DEFAULT_START = (

    ROOT / "Tests" / "Final" / "S009_nano-banana-2-edit_20260330T043403Z.png"

)



NEGATIVE = (

    "blur, distort, low quality, manga panel, speech bubble, halftone, "

    "extra limbs, morphing face, fourth person, duplicate, text, watermark, "

    "wrong left-right order, mirrored composition, teleport, sprint running, "

    "Fern carrying hero trunk, Frieren without case, facing away from path, "

    "whip zoom, nausea spin, roller coaster camera, "

    "robotic march, lockstep soldiers, stiff toy walk, moonwalk, sliding feet, ice skating, "

    "perfectly synchronized steps, mechanical bobbing, marching band, wind-up toy gait, "

    "smooth cg camera orbit, video game walk cycle, mocap glide, heavy volumetric god-ray sweep, "

    "continuous 3d parallax tour, gimbal float, hyperreal motion smear"

)



# Experiment 1: very slow casual hike + intimate documentary handheld (creative but grounded).

MOTION_PROMPT_EXP1 = (

    "Fantasy anime television, **bright sun-flecked** forest path — **preserve the exact reference layout**: "

    "**Stark** left, **Frieren** center with **rectangular travel case**, **Fern** right, trio on the dirt trail **toward camera**. **Do not** mirror or swap order. "

    "**Walk — slow, casual, alive:** a **lazy hiking conversation** pace — steps **land soft** with **unhurried** weight transfer, **heel-to-toe roll** like **real people** on an easy day hike, **not** anime jog cycles, **not** parade marching. "

    "**Desync deliberately:** each traveler is **half a beat different** — Fern **lingers** a half-step once then eases forward; Frieren takes **smaller** relaxed steps; Stark has a **slightly longer** lazy stride — **never** three identical footfalls. "

    "**Arms:** **low, loose** opposite-leg swings — **small** radius, **fluid**, like talking while walking. "

    "**Micro-story beats (subtle):** Stark **rolls** one shoulder or **tugs** his strap between steps; Frieren **rebalances** the case with a **tiny** wrist adjustment; Fern **tucks** hair or **adjusts** scarf mid-stride — **no** big acting. "

    "**Fabric & hair:** coats, **purple hair**, and **blue scarf** **drag and catch up** with each step, plus a **gentle** woodland breeze overlay. "

    "**Camera — creative but gentle:** **slow documentary handheld** — **breathing** micro-float, **organic** micro sway, paired with a **very gradual** intimate **push-in** over the shot (like leaning into the conversation). **No** whip pan, **no** rollercoaster. "

    "**Environment:** dappled sunlight **slides** across path and bark; **depth** in the trees **shimmers** slightly. "

    "One continuous take, **no cuts**, **no manga**, **no text**, **no new characters**."

)



# Experiment 2: same walk philosophy + more cinematic camera — dolly + feathery lateral arc + slow vertical creep.

MOTION_PROMPT_EXP2 = (

    "Fantasy anime television, **epic yet intimate** Northern path — **same hero framing as the reference**: "

    "**Stark**, **Frieren** with **rectangular case**, **Fern** — **left to right**, walking **along** the sunlit trail **toward camera**, **do not** reorder, **do not** mirror. "

    "**Walk — natural and slow:** **casual trail pace**, **lighter than a march**, **heavier than a saunter** — each figure has **their own** relaxed step **timing** and **hip roll**; "

    "**knees** flex naturally; **no** stiff vertical piston bounce, **no** toy-like repetition. "

    "**Overlapping motion:** scarf tails and coat hems **follow through** after each step; Frieren's case **swings** on a **natural pendulum** tied to her gait. "

    "**Camera — dynamic cinematic (keep trio readable):** combine a **smooth slow dolly forward** along the path with a **feather-light lateral arc** around the group's center so **tree trunks** in background **parallax** and depth **opens**; "

    "add an optional **very slow upward drift** (inches only) toward canopy light — **all motion elegant and continuous**, **never** hectic. **Heroes stay** the **dominant** read — **no** framing that loses their faces or bodies. "

    "**Light:** warm **dapple** drifts; leaves whisper. "

    "One flowing beat, **no cuts**, **no halftone**, **no on-screen text**, **no extra people**."

)



# Experiment 3: merge exp1 walk + fabric + environment with exp2 camera (handheld micro-float + dolly + lateral arc + creep).

MOTION_PROMPT_COMBINED = (

    "Fantasy anime television, **bright sun-flecked** Northern forest path — **preserve the exact reference layout**: "

    "**Stark** left, **Frieren** center with **rectangular travel case**, **Fern** right, trio on the dirt trail **toward camera**. **Do not** mirror or swap order. "

    "**Walk — slow, casual, alive:** **lazy hiking conversation** pace — steps **land soft** with **unhurried** weight transfer, **heel-to-toe** like **real people** on an easy day hike; **casual trail pace**, **lighter than a march** — each figure has **their own** relaxed step **timing** and **hip roll**; **desync deliberately:** half a beat apart — Fern **lingers** a half-step once then eases forward; Frieren **smaller** relaxed steps; Stark a **slightly longer** lazy stride — **never** three identical footfalls; **knees** flex naturally; **no** stiff vertical piston bounce, **no** toy-like repetition. "

    "**Arms:** **low, loose** opposite-leg swings — **small** radius, **fluid**; **micro-story beats:** Stark **rolls** a shoulder or **tugs** strap; Frieren **rebalances** the case; Fern **tucks** hair or **adjusts** scarf — **no** big acting. "

    "**Fabric & hair:** coats, **purple hair**, **blue scarf** **drag and catch up**; case **swings** on a **natural pendulum**; **gentle** woodland breeze. "

    "**Camera — hybrid intimate + cinematic:** combine **slow documentary handheld** — **breathing** micro-float, **organic** micro sway — with a **very gradual intimate push-in**; **also** weave a **smooth slow dolly forward** along the path and a **feather-light lateral arc** around the group center so **tree trunks** **parallax** and depth **opens**; add an optional **very slow upward drift** (inches only) toward canopy light — **all motion elegant, continuous, and slow** — **no** whip pan, **no** rollercoaster; **heroes stay** the **dominant** read. "

    "**Environment:** dappled sunlight **slides** across path and bark; **depth** in the trees **shimmers** slightly; warm **dapple** drifts. "

    "One continuous take, **no cuts**, **no manga**, **no halftone**, **no on-screen text**, **no new characters**."

)



# Experiment 4: subtle TV-anime limited-animation feel — soft Fern, choppy/discrete step beats, near-flat camera (avoid 3D cinematic glide).

MOTION_PROMPT_EXP4_ANIME_SUBTLE = (

    "Fantasy **broadcast anime television** — **cel-shaded**, **limited-animation** timing — **bright sun-flecked** forest path; **preserve the exact reference layout**: "

    "**Stark** left, **Frieren** center with **rectangular travel case**, **Fern** right, walking the trail **toward camera**. **Do not** mirror or swap order. "

    "**Motion grammar — anime, not 3D:** favor **short holds** and **discrete** in-between poses — a **gentle staccato** walk rhythm like **hand-drawn** TV cuts, **not** silky continuous mocap or video-game interpolation glide. **Keep all movement small** and **slow**. "

    "**Walk — very understated:** trio advances at a **barely-there** trail pace with **micro** timing offsets — **Fern is quietest**: **tiny** steps, **softest** hip sway, **minimal** head turn, eyes mostly forward; scarf and hair move in **whispers**, not big arcs. **Stark** and **Frieren** only **slightly** more — **small** strap or case micro-shift, **no** swagger. "

    "**Arms:** **close to body**, **low amplitude** swings; **no** broad gestures. "

    "**Camera — almost locked 2D frame:** treat the shot like a **stable anime plate** — **nearly static**; at most a **hairline** handheld tremor or an **imperceptible** slow creep — **no** orbital arc, **no** lateral dolly swing, **no** crane rise, **no** deep parallax tour; background reads **layered painting**, not **3D** fly-through. "

    "**Light:** dapple shifts as **simple** bright patches — **subtle** flicker only. "

    "One continuous take, **no cuts**, **no manga**, **no text**, **no new characters**."

)



EXPERIMENTS: dict[str, tuple[str, str]] = {

    "1": ("exp1_slow_handheld", MOTION_PROMPT_EXP1),

    "2": ("exp2_dolly_parallax", MOTION_PROMPT_EXP2),

    "3": ("exp3_combined_handheld_dolly", MOTION_PROMPT_COMBINED),

    "4": ("exp4_anime_limited_subtle", MOTION_PROMPT_EXP4_ANIME_SUBTLE),

}





def main() -> int:

    parser = argparse.ArgumentParser(

        description="S009 → Kling 2.6 Pro I2V (WS path; experiments 1–4)"

    )

    parser.add_argument(

        "--experiment",

        choices=("1", "2", "3", "4"),

        default="1",

        help="1 = slow casual walk + documentary handheld / soft push-in. "

        "2 = same walk + dynamic dolly + lateral arc + slow vertical creep. "

        "3 = combined (1+2 camera grammar in one prompt). "

        "4 = TV-anime limited animation: subtle / slow, soft Fern, near-locked camera (less 3D glide).",

    )

    parser.add_argument(

        "--start-image",

        type=Path,

        default=DEFAULT_START,

        help=f"Hero still PNG (default: Tests/Final/{DEFAULT_START.name})",

    )

    parser.add_argument(

        "--duration",

        choices=("5", "10"),

        default="5",

        help='Kling duration (default "5" per user pipeline)',

    )

    parser.add_argument("--audio", action="store_true", help="generate_audio true (costlier)")

    parser.add_argument("--dry-run", action="store_true", help="Print args only")

    args = parser.parse_args()

    start_path = args.start_image.resolve()



    tag, motion_prompt = EXPERIMENTS[args.experiment]



    assert_model_allowed(MODEL_ID)



    key = read_fal_key()

    if not key:

        print("Missing FAL_KEY — set in .env at project root.", file=sys.stderr)

        return 1



    if not start_path.is_file():

        print(f"Start image not found: {start_path}", file=sys.stderr)

        return 1



    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    out_dir = ROOT / "outputs" / "fal"

    video_dir = ROOT / "outputs" / "video"

    out_dir.mkdir(parents=True, exist_ok=True)

    video_dir.mkdir(parents=True, exist_ok=True)



    os.environ["FAL_KEY"] = key



    print(f"Experiment {args.experiment} ({tag}), duration={args.duration}s", flush=True)

    print(f"Uploading start frame: {start_path}", flush=True)

    start_url = fal_client.upload_file(str(start_path))

    print(f"start_image_url: {start_url}", flush=True)



    arguments = {

        "prompt": motion_prompt,

        "start_image_url": start_url,

        "duration": args.duration,

        "generate_audio": args.audio,

        "negative_prompt": NEGATIVE,

    }



    meta_path = out_dir / f"{SHOT_ID}_kling_i2v_meta_{ts}_{tag}.json"

    meta_path.write_text(

        json.dumps(

            {

                "shot": SHOT_ID,

                "experiment": args.experiment,

                "experiment_tag": tag,

                "model_id": MODEL_ID,

                "start_image_local": str(start_path),

                "start_image_url": start_url,

                "arguments": arguments,

            },

            indent=2,

        ),

        encoding="utf-8",

    )

    print(f"Meta: {meta_path}", flush=True)



    if args.dry_run:

        print(json.dumps(arguments, indent=2))

        return 0



    print(f"Submitting {MODEL_ID} …", flush=True)

    try:

        result = fal_client.subscribe(

            MODEL_ID,

            arguments=arguments,

            with_logs=True,

        )

    except Exception as e:

        print(f"ERROR: {e}", file=sys.stderr)

        return 1



    log_path = out_dir / f"{SHOT_ID}_kling_i2v_{ts}_{tag}.json"

    log_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")

    print(f"Log: {log_path}", flush=True)



    vurl = video_url_from_result(result)

    if not vurl:

        print(

            f"No video URL in response keys: {list(result.keys()) if isinstance(result, dict) else type(result)}",

            file=sys.stderr,

        )

        return 1



    ext = extension_from_url(vurl)

    if ext not in (".mp4", ".webm", ".mov"):

        ext = ".mp4"

    dest = video_dir / f"{SHOT_ID}_kling-v26-pro_i2v_{ts}_{tag}{ext}"

    print(f"Downloading: {vurl}", flush=True)

    download_file(vurl, dest)

    print(f"Saved: {dest}", flush=True)

    return 0





if __name__ == "__main__":

    raise SystemExit(main())

