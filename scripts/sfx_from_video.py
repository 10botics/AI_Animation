"""
Video-conditioned SFX on Fal (same FAL_KEY as the rest of the repo).

Backends:
  thinksound      fal-ai/thinksound
  kling-v2a       fal-ai/kling-video/video-to-audio
  cassette-video  cassetteai/video-sound-effects-generator

Batch (ThinkSound + Kling on finals):
  python sfx_from_video.py --shots S001 S002 --video-dir "..\\outputs\\video\\final"

Single file:
  python sfx_from_video.py --model thinksound --video "..\\....mp4"

See docs/sfx-models-fal.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import fal_client

from fal_common import ROOT, download_file, extension_from_url, read_fal_key, video_url_from_result

MODEL_THINKSOUND = "fal-ai/thinksound"
MODEL_KLING_V2A = "fal-ai/kling-video/video-to-audio"
MODEL_CASSETTE_VIDEO = "cassetteai/video-sound-effects-generator"

OUT_VIDEO_DIR = ROOT / "outputs" / "video" / "sfx"
OUT_META_DIR = ROOT / "outputs" / "fal"
DEFAULT_VIDEO_DIR = ROOT / "outputs" / "video" / "final"

# Shot-tuned hints (avoid voices; align with stage_01/02 beats).
SHOT_THINKSOUND_HINTS: dict[str, str] = {
    "S001": (
        "Fantasy anime cold open on a quiet plaza: soft air and distant hush, faint breeze, wooden bench subtle creak, "
        "warm gentle ambience, solitary mood, no speech, no crowd, no footsteps rush"
    ),
    "S002": (
        "Northern forest camp daytime: small campfire crackle at low level, trees and leaves in soft wind, "
        "travelers resting, canvas and fabric micro-rustle, no voices, no animals loud"
    ),
}

SHOT_KLING_SFX: dict[str, str] = {
    "S001": (
        "Anime El Dorado cold open foley: quiet plaza air, soft wind, bench wood metal settle, distant ambience, "
        "no voices no dialogue"
    )[:200],
    "S002": (
        "Anime forest camp foley: gentle wind leaves, distant small fire crackle, fabric gear subtle, "
        "no voices no dialogue"
    )[:200],
}

SHOT_KLING_BGM: dict[str, str] = {
    "S001": "Almost silent air tone only, no melody, no rhythm",
    "S002": "Barely audible outdoor air pad, no melody, no drums",
}

DEFAULT_KLING_SFX = (
    "Anime fantasy outdoor foley: soft wind, leaf rustle, fabric motion, no voices, no dialogue"
)[:200]
DEFAULT_KLING_BGM = "Near-silent air and distant tone only, no melody, no rhythm, no drums"


def _unwrap(result: object) -> dict:
    if not isinstance(result, dict):
        return {}
    data = result.get("data")
    return data if isinstance(data, dict) else result


def _file_url(payload: dict, key: str) -> str | None:
    f = payload.get(key)
    if isinstance(f, dict) and isinstance(f.get("url"), str):
        return f["url"]
    return None


def find_shot_video(video_dir: Path, shot: str) -> Path | None:
    if not video_dir.is_dir():
        return None
    token = re.escape(shot.casefold())
    pat = re.compile(rf"{token}", re.IGNORECASE)
    vids: list[Path] = []
    for p in sorted(video_dir.iterdir()):
        if not p.is_file():
            continue
        if p.suffix.lower() not in (".mp4", ".webm", ".mov", ".mkv", ".m4v"):
            continue
        if pat.search(p.name):
            vids.append(p)
    return vids[0] if vids else None


def _run_thinksound(
    video_url: str,
    out_stem: str,
    ts: str,
    *,
    prompt: str,
    seed: int | None,
) -> tuple[dict, int]:
    arguments: dict = {"video_url": video_url}
    if prompt.strip():
        arguments["prompt"] = prompt.strip()
    if seed is not None:
        arguments["seed"] = seed
    print(f"  [{out_stem}] ThinkSound ...", flush=True)
    result = fal_client.subscribe(MODEL_THINKSOUND, arguments=arguments, with_logs=True)
    pay = _unwrap(result)
    vout = _file_url(pay, "video") or video_url_from_result(result)
    if not vout:
        print(f"ThinkSound failed: {result}", file=sys.stderr)
        return {}, 1
    ext = extension_from_url(vout)
    if ext not in (".mp4", ".webm", ".mov"):
        ext = ".mp4"
    dest = OUT_VIDEO_DIR / f"{out_stem}_thinksound_{ts}{ext}"
    download_file(vout, dest)
    print(f"    saved: {dest}", flush=True)
    meta: dict = {
        "backend": "thinksound",
        "arguments": arguments,
        "output_video": str(dest),
    }
    if pay.get("prompt"):
        meta["resolved_prompt"] = pay.get("prompt")
    return meta, 0


def _run_kling(
    video_url: str,
    out_stem: str,
    ts: str,
    *,
    kling_sfx: str,
    kling_bgm: str,
    asmr: bool,
) -> tuple[dict, int]:
    sfx = kling_sfx.strip()[:200]
    bgm = kling_bgm.strip()[:200]
    arguments = {
        "video_url": video_url,
        "sound_effect_prompt": sfx,
        "background_music_prompt": bgm,
        "asmr_mode": asmr,
    }
    print(f"  [{out_stem}] Kling video-to-audio ...", flush=True)
    result = fal_client.subscribe(MODEL_KLING_V2A, arguments=arguments, with_logs=True)
    pay = _unwrap(result)
    vout = _file_url(pay, "video") or video_url_from_result(result)
    aout = _file_url(pay, "audio")
    if not vout:
        print(f"Kling failed: {result}", file=sys.stderr)
        return {}, 1
    vext = extension_from_url(vout)
    if vext not in (".mp4", ".mov", ".webm"):
        vext = ".mp4"
    vdest = OUT_VIDEO_DIR / f"{out_stem}_kling_v2a_{ts}{vext}"
    download_file(vout, vdest)
    print(f"    saved video: {vdest}", flush=True)
    meta: dict = {
        "backend": "kling-v2a",
        "arguments": arguments,
        "output_video": str(vdest),
    }
    if aout:
        aext = extension_from_url(aout)
        if aext not in (".mp3", ".wav"):
            aext = ".mp3"
        adest = OUT_VIDEO_DIR / f"{out_stem}_kling_v2a_{ts}_audio{aext}"
        download_file(aout, adest)
        print(f"    saved audio: {adest}", flush=True)
        meta["output_audio"] = str(adest)
    return meta, 0


def _run_cassette_video(video_url: str, out_stem: str, ts: str) -> tuple[dict, int]:
    arguments = {"video_url": video_url}
    print(f"  [{out_stem}] Cassette video SFX ...", flush=True)
    result = fal_client.subscribe(MODEL_CASSETTE_VIDEO, arguments=arguments, with_logs=True)
    pay = _unwrap(result)
    vout = _file_url(pay, "video") or video_url_from_result(result)
    if not vout:
        print(f"Cassette video failed: {result}", file=sys.stderr)
        return {}, 1
    ext = extension_from_url(vout)
    if ext not in (".mp4", ".webm", ".mov"):
        ext = ".mp4"
    dest = OUT_VIDEO_DIR / f"{out_stem}_cassette_video_{ts}{ext}"
    download_file(vout, dest)
    print(f"    saved: {dest}", flush=True)
    return {"backend": "cassette-video", "arguments": arguments, "output_video": str(dest)}, 0


def main() -> int:
    if not read_fal_key():
        print("Missing FAL_KEY in .env at repo root.", file=sys.stderr)
        return 1

    parser = argparse.ArgumentParser(description="Video → SFX / dubbed audio (Fal)")
    parser.add_argument(
        "--shots",
        nargs="+",
        metavar="S00N",
        help="Batch: shot ids — runs --models on each match under --video-dir",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        choices=("thinksound", "kling-v2a", "cassette-video"),
        default=["thinksound", "kling-v2a"],
        help="With --shots: which backends per clip (default: thinksound kling-v2a)",
    )
    parser.add_argument("--video-dir", type=Path, default=DEFAULT_VIDEO_DIR)
    parser.add_argument("--model", choices=("thinksound", "kling-v2a", "cassette-video"))
    parser.add_argument("--video", type=Path, help="Single file (requires --model)")
    parser.add_argument("--prompt", default="", help="ThinkSound override (single) or extra hint (batch adds to shot hint)")
    parser.add_argument("--kling-sfx", default="", help="Override Kling SFX line (single); batch uses per-shot map if empty")
    parser.add_argument("--kling-bgm", default="", help="Override Kling BGM (single and batch default fallback)")
    parser.add_argument("--asmr", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    OUT_VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    OUT_META_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    if args.shots:
        video_dir = args.video_dir.resolve()
        batch_report: dict = {
            "mode": "batch",
            "timestamp_utc": ts,
            "video_dir": str(video_dir),
            "models": args.models,
            "shots": [],
        }
        for raw in args.shots:
            shot = raw.strip().upper()
            vpath = find_shot_video(video_dir, shot)
            if not vpath:
                print(f"{shot}: no video in {video_dir}", file=sys.stderr)
                batch_report["shots"].append({"shot": shot, "error": "no_input_video"})
                continue
            print(f"{shot}: {vpath}", flush=True)
            video_url = fal_client.upload_file(str(vpath.resolve()))
            out_stem = vpath.stem
            think_hint = SHOT_THINKSOUND_HINTS.get(shot, SHOT_THINKSOUND_HINTS.get("S002", ""))
            if args.prompt.strip():
                think_hint = f"{think_hint} {args.prompt.strip()}".strip()
            k_sfx = args.kling_sfx.strip() if args.kling_sfx.strip() else SHOT_KLING_SFX.get(shot, DEFAULT_KLING_SFX)
            k_bgm = args.kling_bgm.strip() if args.kling_bgm.strip() else SHOT_KLING_BGM.get(shot, DEFAULT_KLING_BGM)
            shot_entry: dict = {
                "shot": shot,
                "source": str(vpath),
                "video_url": video_url,
                "runs": [],
            }
            for m in args.models:
                if m == "thinksound":
                    meta, code = _run_thinksound(
                        video_url, out_stem, ts, prompt=think_hint, seed=args.seed
                    )
                    if code != 0:
                        return 1
                    shot_entry["runs"].append(meta)
                elif m == "kling-v2a":
                    meta, code = _run_kling(
                        video_url,
                        out_stem,
                        ts,
                        kling_sfx=k_sfx,
                        kling_bgm=k_bgm,
                        asmr=args.asmr,
                    )
                    if code != 0:
                        return 1
                    shot_entry["runs"].append(meta)
                elif m == "cassette-video":
                    meta, code = _run_cassette_video(video_url, out_stem, ts)
                    if code != 0:
                        return 1
                    shot_entry["runs"].append(meta)
            batch_report["shots"].append(shot_entry)
        meta_path = OUT_META_DIR / f"sfx_from_video_batch_{ts}.json"
        meta_path.write_text(json.dumps(batch_report, indent=2), encoding="utf-8")
        print(f"Meta: {meta_path}", flush=True)
        return 0

    if not args.model or not args.video:
        print("Provide both --model and --video, or use --shots.", file=sys.stderr)
        return 1

    vpath = args.video.resolve()
    if not vpath.is_file():
        print(f"Not a file: {vpath}", file=sys.stderr)
        return 1
    suffix = vpath.suffix.lower()
    if suffix not in (".mp4", ".mov", ".webm", ".mkv"):
        print(f"Note: Fal Kling expects mp4/mov; got {suffix!r}", file=sys.stderr)

    print(f"Uploading {vpath} ...", flush=True)
    video_url = fal_client.upload_file(str(vpath))
    tag = args.model.replace("-", "_")
    out_stem = vpath.stem

    meta: dict = {
        "backend": args.model,
        "source_local": str(vpath),
        "video_url": video_url,
        "timestamp_utc": ts,
    }

    if args.model == "thinksound":
        arguments: dict = {"video_url": video_url}
        if args.prompt.strip():
            arguments["prompt"] = args.prompt.strip()
        if args.seed is not None:
            arguments["seed"] = args.seed
        meta["arguments"] = arguments
        print(f"Calling {MODEL_THINKSOUND} ...", flush=True)
        result = fal_client.subscribe(MODEL_THINKSOUND, arguments=arguments, with_logs=True)
        pay = _unwrap(result)
        vout = _file_url(pay, "video") or video_url_from_result(result)
        if not vout:
            print(f"No output video URL: {result}", file=sys.stderr)
            return 1
        ext = extension_from_url(vout)
        if ext not in (".mp4", ".webm", ".mov"):
            ext = ".mp4"
        dest = OUT_VIDEO_DIR / f"{out_stem}_{tag}_{ts}{ext}"
        download_file(vout, dest)
        print(f"Saved: {dest}", flush=True)
        meta["output_video"] = str(dest)
        if pay.get("prompt"):
            meta["resolved_prompt"] = pay.get("prompt")

    elif args.model == "kling-v2a":
        sfx = (args.kling_sfx.strip() or DEFAULT_KLING_SFX)[:200]
        bgm = (args.kling_bgm.strip() or DEFAULT_KLING_BGM)[:200]
        arguments = {
            "video_url": video_url,
            "sound_effect_prompt": sfx,
            "background_music_prompt": bgm,
            "asmr_mode": args.asmr,
        }
        meta["arguments"] = arguments
        print(f"Calling {MODEL_KLING_V2A} ...", flush=True)
        result = fal_client.subscribe(MODEL_KLING_V2A, arguments=arguments, with_logs=True)
        pay = _unwrap(result)
        vout = _file_url(pay, "video") or video_url_from_result(result)
        aout = _file_url(pay, "audio")
        if not vout:
            print(f"No output video URL: {result}", file=sys.stderr)
            return 1
        vext = extension_from_url(vout)
        if vext not in (".mp4", ".mov", ".webm"):
            vext = ".mp4"
        vdest = OUT_VIDEO_DIR / f"{out_stem}_{tag}_{ts}{vext}"
        download_file(vout, vdest)
        print(f"Saved video: {vdest}", flush=True)
        meta["output_video"] = str(vdest)
        if aout:
            aext = extension_from_url(aout)
            if aext not in (".mp3", ".wav"):
                aext = ".mp3"
            adest = OUT_VIDEO_DIR / f"{out_stem}_{tag}_{ts}_audio{aext}"
            download_file(aout, adest)
            print(f"Saved audio: {adest}", flush=True)
            meta["output_audio"] = str(adest)

    else:
        arguments = {"video_url": video_url}
        meta["arguments"] = arguments
        print(f"Calling {MODEL_CASSETTE_VIDEO} ...", flush=True)
        result = fal_client.subscribe(MODEL_CASSETTE_VIDEO, arguments=arguments, with_logs=True)
        pay = _unwrap(result)
        vout = _file_url(pay, "video") or video_url_from_result(result)
        if not vout:
            print(f"No output video URL: {result}", file=sys.stderr)
            return 1
        ext = extension_from_url(vout)
        if ext not in (".mp4", ".webm", ".mov"):
            ext = ".mp4"
        dest = OUT_VIDEO_DIR / f"{out_stem}_{tag}_{ts}{ext}"
        download_file(vout, dest)
        print(f"Saved: {dest}", flush=True)
        meta["output_video"] = str(dest)

    meta_path = OUT_META_DIR / f"sfx_from_video_{tag}_{ts}.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Meta: {meta_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
