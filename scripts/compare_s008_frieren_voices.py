"""
S008 Frieren line — compare 3 voice-cloning TTS backends from the same English dub ref.

Models (all Fal, same ref audio + line text):
  1. MiniMax  — voice-clone (long sample) + speech-02-hd TTS
  2. F5-TTS   — zero-shot ref_audio_url + gen_text
  3. Qwen3    — clone-voice/1.7b embedding + text-to-speech/1.7b

Reference: `voice_refs/frieren_eng_dub_ref_90s.wav` cut from
`video source/Dub Frieren being for 2 minutes and 15 seconds [IkZiiuI-NTM].webm`

Usage:
  cd scripts
  python compare_s008_frieren_voices.py
  python compare_s008_frieren_voices.py --ref-seconds 90 --start-sec 2.0
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import fal_client

from fal_common import ROOT, download_file, read_fal_key

LINE_TEXT = "Now we're talking. Let's do it."
ENG_DUB_SOURCE = ROOT / "video source" / "Dub Frieren being for 2 minutes and 15 seconds [IkZiiuI-NTM].webm"
REF_WAV = ROOT / "voice_refs" / "frieren_eng_dub_ref_90s.wav"
OUT_DIR = ROOT / "outputs" / "voice" / "S008" / "compare"

MINIMAX_CLONE = "fal-ai/minimax/voice-clone"
MINIMAX_TTS = "fal-ai/minimax-tts/text-to-speech"
F5_TTS = "fal-ai/f5-tts"
QWEN_CLONE = "fal-ai/qwen-3-tts/clone-voice/1.7b"
QWEN_TTS = "fal-ai/qwen-3-tts/text-to-speech/1.7b"


def _ensure_ref(seconds: float, skip: float) -> Path:
    REF_WAV.parent.mkdir(parents=True, exist_ok=True)
    if not ENG_DUB_SOURCE.is_file():
        print(f"Missing: {ENG_DUB_SOURCE}", file=sys.stderr)
        sys.exit(1)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            str(skip),
            "-i",
            str(ENG_DUB_SOURCE),
            "-t",
            str(seconds),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "44100",
            str(REF_WAV),
        ],
        check=True,
        capture_output=True,
    )
    print(f"Ref {seconds}s: {REF_WAV}", flush=True)
    return REF_WAV


def _latest_s008_base() -> Path:
    candidates: list[Path] = []
    for d in (ROOT / "outputs" / "video" / "final", ROOT / "outputs" / "video"):
        if d.is_dir():
            for p in d.glob("S008_kling*.mp4"):
                if "_dialogue_" not in p.name and "_frieren_dialogue_" not in p.name:
                    if "compare_" not in p.name:
                        candidates.append(p)
    if not candidates:
        raise FileNotFoundError("No base S008 MP4 found")
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _probe_duration(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(r.stdout.strip())


def _audio_ext_from_url(url: str) -> str:
    low = url.split("?", 1)[0].lower()
    for ext in (".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"):
        if low.endswith(ext):
            return ext
    return ".mp3"


def _save_audio(result: dict, key: str, dest: Path) -> Path:
    block = result.get(key)
    url = None
    if isinstance(block, dict):
        url = block.get("url")
    elif isinstance(block, str):
        url = block
    if not url:
        raise RuntimeError(f"No audio URL at {key}: {result}")
    ext = _audio_ext_from_url(url)
    out = dest.with_suffix(ext)
    download_file(url, out)
    print(f"Saved {out.name}", flush=True)
    return out


def _gen_minimax(ref_url: str, stem: Path) -> tuple[Path, dict]:
    clone = fal_client.subscribe(
        MINIMAX_CLONE,
        arguments={
            "audio_url": ref_url,
            "noise_reduction": True,
            "need_volume_normalization": True,
            "text": LINE_TEXT,
            "model": "speech-02-hd",
        },
        with_logs=True,
    )
    vid = clone.get("custom_voice_id") if isinstance(clone, dict) else None
    if not vid:
        raise RuntimeError(f"MiniMax clone failed: {clone}")
    tts = fal_client.subscribe(
        MINIMAX_TTS,
        arguments={
            "text": LINE_TEXT,
            "voice_setting": {
                "custom_voice_id": vid,
                "emotion": "neutral",
                "speed": 0.95,
            },
            "language_boost": "English",
        },
        with_logs=True,
    )
    audio = _save_audio(tts, "audio", stem)
    return audio, {"custom_voice_id": vid}


def _gen_f5(ref_url: str, stem: Path) -> tuple[Path, dict]:
    result = fal_client.subscribe(
        F5_TTS,
        arguments={
            "gen_text": LINE_TEXT,
            "ref_audio_url": ref_url,
            "model_type": "F5-TTS",
            "remove_silence": True,
        },
        with_logs=True,
    )
    audio = _save_audio(result, "audio_url", stem)
    return audio, {}


def _gen_qwen(ref_url: str, stem: Path) -> tuple[Path, dict]:
    clone = fal_client.subscribe(
        QWEN_CLONE,
        arguments={"audio_url": ref_url},
        with_logs=True,
    )
    emb_url = None
    if isinstance(clone, dict):
        emb = clone.get("speaker_embedding") or clone.get("speaker_voice_embedding")
        if isinstance(emb, dict):
            emb_url = emb.get("url")
    if not emb_url:
        raise RuntimeError(f"Qwen clone failed: {clone}")
    tts = fal_client.subscribe(
        QWEN_TTS,
        arguments={
            "text": LINE_TEXT,
            "language": "English",
            "speaker_voice_embedding_file_url": emb_url,
            "prompt": "Calm, understated, slightly interested.",
        },
        with_logs=True,
    )
    audio = _save_audio(tts, "audio", stem)
    return audio, {"embedding_url": emb_url}


def _mux(video: Path, audio: Path, out: Path, start_sec: float, duck: float) -> None:
    dur = _probe_duration(video)
    ms = int(start_sec * 1000)
    fc = (
        f"[1:a]adelay={ms}|{ms},apad=whole_dur={dur}[dlg];"
        f"[0:a]volume={duck}[bg];"
        f"[bg][dlg]amix=inputs=2:duration=first:dropout_transition=0[aout]"
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video),
            "-i",
            str(audio),
            "-filter_complex",
            fc,
            "-map",
            "0:v",
            "-map",
            "[aout]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            str(out),
        ],
        check=True,
    )
    print(f"Muxed {out.name}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare Frieren TTS models on S008")
    parser.add_argument("--ref-seconds", type=float, default=90.0)
    parser.add_argument("--ref-skip", type=float, default=5.0, help="Skip intro in dub comp")
    parser.add_argument("--start-sec", type=float, default=2.0, help="Dialogue start on 5s clip")
    parser.add_argument("--duck", type=float, default=0.35)
    parser.add_argument("--video", type=Path, default=None)
    parser.add_argument("--models", nargs="+", default=["minimax", "f5", "qwen"])
    args = parser.parse_args()

    key = read_fal_key()
    if not key:
        print("Missing FAL_KEY", file=sys.stderr)
        return 1
    os.environ["FAL_KEY"] = key

    ref_path = _ensure_ref(args.ref_seconds, args.ref_skip)
    ref_url = fal_client.upload_file(str(ref_path))
    print(f"Uploaded ref: {ref_url}", flush=True)

    video = args.video.resolve() if args.video else _latest_s008_base()
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    generators = {
        "minimax": _gen_minimax,
        "f5": _gen_f5,
        "qwen": _gen_qwen,
    }

    report: dict = {
        "line": LINE_TEXT,
        "ref_wav": str(REF_WAV.relative_to(ROOT)),
        "ref_seconds": args.ref_seconds,
        "ref_skip": args.ref_skip,
        "ref_url": ref_url,
        "video_in": str(video),
        "models": {},
    }

    for name in args.models:
        if name not in generators:
            print(f"Unknown model: {name}", file=sys.stderr)
            return 1
        print(f"\n=== {name} ===", flush=True)
        stem = OUT_DIR / f"s008_frieren_{name}_{ts}"
        try:
            audio_path, meta = generators[name](ref_url, stem)
            mux_out = OUT_DIR / f"S008_frieren_{name}_{ts}.mp4"
            _mux(video, audio_path, mux_out, args.start_sec, args.duck)
            report["models"][name] = {
                "audio": str(audio_path.relative_to(ROOT)),
                "video": str(mux_out.relative_to(ROOT)),
                "meta": meta,
                "status": "ok",
            }
        except Exception as e:
            report["models"][name] = {"status": "error", "error": str(e)}
            print(f"ERROR {name}: {e}", file=sys.stderr)

    report_path = OUT_DIR / f"compare_report_{ts}.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nReport: {report_path}", flush=True)
    return 0 if all(m.get("status") == "ok" for m in report["models"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
