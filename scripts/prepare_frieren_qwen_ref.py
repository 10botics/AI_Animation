"""
Prepare curated Frieren Qwen3 reference: VAD window pick, Demucs vocals, Fal Whisper transcript.

Outputs (default: voice_refs/ experiments; production refs → Voice Reference/<lang>/<Character>/):
  voice_refs/frieren_qwen_ref_15s.wav
  voice_refs/frieren_qwen_ref_15s.txt   (reference_text for clone + TTS)

Usage:
  cd scripts
  python prepare_frieren_qwen_ref.py
  python prepare_frieren_qwen_ref.py --skip-demucs
  python prepare_frieren_qwen_ref.py --skip 0 --scan-seconds 45 --target-seconds 12
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import fal_client
import soundfile as sf
import torch
from silero_vad import get_speech_timestamps, load_silero_vad

from fal_common import ROOT, read_fal_key

VAD_SR = 16_000
OUT_WAV = ROOT / "voice_refs" / "frieren_qwen_ref_15s.wav"
OUT_TXT = ROOT / "voice_refs" / "frieren_qwen_ref_15s.txt"
META_JSON = ROOT / "voice_refs" / "frieren_qwen_ref_15s.json"
DEFAULT_SOURCE = (
    ROOT / "video source" / "Dub Frieren being for 2 minutes and 15 seconds [IkZiiuI-NTM].webm"
)
WHISPER_MODEL = "fal-ai/whisper"


def _ffmpeg_mono(path_in: Path, path_out: Path, *, skip: float, duration: float, sr: int) -> None:
    path_out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            str(skip),
            "-i",
            str(path_in),
            "-t",
            str(duration),
            "-vn",
            "-ac",
            "1",
            "-ar",
            str(sr),
            str(path_out),
        ],
        check=True,
        capture_output=True,
    )


def _ffmpeg_denoise_vocals(src: Path, dest: Path) -> Path:
    """Light vocal cleanup when Demucs cannot save (torchcodec on Windows)."""
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-af",
            "highpass=f=90,lowpass=f=9000,afftdn=nf=-22",
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


def _demucs_vocals(wav_in: Path, work_dir: Path) -> Path:
    out_root = work_dir / "demucs_out"
    out_root.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "demucs",
                "-d",
                "cpu",
                "--two-stems",
                "vocals",
                "-n",
                "htdemucs",
                "-o",
                str(out_root),
                str(wav_in),
            ],
            check=True,
            capture_output=True,
        )
        vocals = out_root / "htdemucs" / wav_in.stem / "vocals.wav"
        if not vocals.is_file():
            raise FileNotFoundError(f"Demucs vocals not found: {vocals}")
        return vocals
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        fallback = work_dir / f"{wav_in.stem}_denoised.wav"
        print(f"Demucs unavailable ({e}); using ffmpeg denoise fallback", flush=True)
        return _ffmpeg_denoise_vocals(wav_in, fallback)


def _resample_to_44100(src: Path, dest: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-ac",
            "1",
            "-ar",
            "44100",
            str(dest),
        ],
        check=True,
        capture_output=True,
    )


def _best_speech_window(
    wav_path: Path,
    *,
    target_sec: float,
    min_sec: float,
    max_sec: float,
) -> tuple[float, float]:
    """Return (start_sec, end_sec) within wav_path for the densest speech window."""
    audio, sr = sf.read(str(wav_path), dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    wav_t = torch.from_numpy(audio)
    model = load_silero_vad()
    segments = get_speech_timestamps(
        wav_t,
        model,
        sampling_rate=sr,
        min_speech_duration_ms=250,
        min_silence_duration_ms=200,
    )
    if not segments:
        dur = len(audio) / sr
        end = min(dur, target_sec)
        return 0.0, end

    spans = [(s["start"] / sr, s["end"] / sr) for s in segments]
    target = max(min_sec, min(max_sec, target_sec))
    total_dur = len(audio) / sr
    best_start = 0.0
    best_score = -1.0

    step = 0.25
    t = 0.0
    while t + target <= total_dur + 1e-6:
        win_end = min(t + target, total_dur)
        win_len = win_end - t
        if win_len < min_sec:
            t += step
            continue
        speech = sum(max(0.0, min(end, win_end) - max(start, t)) for start, end in spans)
        score = speech / win_len
        if score > best_score:
            best_score = score
            best_start = t
        t += step

    end = min(best_start + target, total_dur)
    if end - best_start < min_sec:
        end = min(total_dur, best_start + min_sec)
    return best_start, end


def _transcribe_whisper(wav: Path, *, language: str = "en") -> str:
    url = fal_client.upload_file(str(wav))
    result = fal_client.subscribe(
        WHISPER_MODEL,
        arguments={
            "audio_url": url,
            "task": "transcribe",
            "language": language,
            "chunk_level": "none",
        },
        with_logs=True,
    )
    if not isinstance(result, dict):
        raise RuntimeError(f"Whisper failed: {result}")
    text = result.get("text")
    if not isinstance(text, str) or not text.strip():
        raise RuntimeError(f"No transcript in Whisper result: {result}")
    return text.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Curated Frieren Qwen ref (VAD + Demucs + transcript)")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--skip", type=float, default=0.0, help="Start scan in source video (seconds)")
    parser.add_argument("--scan-seconds", type=float, default=45.0, help="Region to scan for best window")
    parser.add_argument("--target-seconds", type=float, default=12.0)
    parser.add_argument("--min-seconds", type=float, default=10.0)
    parser.add_argument("--max-seconds", type=float, default=15.0)
    parser.add_argument("--skip-demucs", action="store_true")
    parser.add_argument("--skip-whisper", action="store_true", help="Keep existing .txt if present")
    parser.add_argument("--reference-text", type=str, default=None, help="Override transcript manually")
    parser.add_argument("--out-wav", type=Path, default=OUT_WAV)
    parser.add_argument("--out-txt", type=Path, default=OUT_TXT)
    parser.add_argument("--out-meta", type=Path, default=META_JSON)
    parser.add_argument(
        "--whisper-language",
        default="en",
        help="Whisper language code (e.g. en, ja for Fern JP source)",
    )
    args = parser.parse_args()

    out_wav = args.out_wav.resolve()
    out_txt = args.out_txt.resolve()
    out_meta = args.out_meta.resolve()

    if not args.skip_whisper and not read_fal_key():
        print("Missing FAL_KEY for Whisper transcript", file=sys.stderr)
        return 1
    if not args.skip_whisper:
        os.environ["FAL_KEY"] = read_fal_key() or ""

    src = args.source.resolve()
    if not src.is_file():
        print(f"Missing source: {src}", file=sys.stderr)
        return 1

    is_wav = src.suffix.lower() == ".wav"
    scan_seconds = args.scan_seconds
    if is_wav and args.scan_seconds == 45.0:
        scan_seconds = float(sf.info(str(src)).duration)

    work = ROOT / "outputs" / "voice" / "ref_prep"
    work.mkdir(parents=True, exist_ok=True)
    scan_wav = work / "scan_16k.wav"
    _ffmpeg_mono(src, scan_wav, skip=args.skip, duration=scan_seconds, sr=VAD_SR)

    rel_start, rel_end = _best_speech_window(
        scan_wav,
        target_sec=args.target_seconds,
        min_sec=args.min_seconds,
        max_sec=args.max_seconds,
    )
    abs_start = args.skip + rel_start
    clip_len = rel_end - rel_start
    print(f"Best window: {abs_start:.2f}s + {clip_len:.2f}s (speech density pick)", flush=True)

    raw_clip = work / "clip_raw.wav"
    if is_wav:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-ss",
                str(abs_start),
                "-i",
                str(src),
                "-t",
                str(clip_len),
                "-ac",
                "1",
                "-ar",
                "44100",
                str(raw_clip),
            ],
            check=True,
            capture_output=True,
        )
    else:
        _ffmpeg_mono(src, raw_clip, skip=abs_start, duration=clip_len, sr=44100)

    already_vocals = args.skip_demucs or is_wav and "vocals" in src.stem
    demucs_ok = False
    if already_vocals:
        isolated = raw_clip
        print("Skipping demucs (source already vocal stem)", flush=True)
    else:
        print("Demucs vocal isolation...", flush=True)
        isolated = _demucs_vocals(raw_clip, work)
        demucs_ok = "denoised" not in isolated.name
        if not demucs_ok:
            print("Used ffmpeg denoise fallback (Demucs save failed on this machine)", flush=True)

    out_wav.parent.mkdir(parents=True, exist_ok=True)
    _resample_to_44100(isolated, out_wav)

    if args.reference_text:
        reference_text = args.reference_text.strip()
    elif args.skip_whisper and out_txt.is_file():
        reference_text = out_txt.read_text(encoding="utf-8").strip()
    else:
        print("Whisper transcript...", flush=True)
        reference_text = _transcribe_whisper(out_wav, language=args.whisper_language)

    out_txt.write_text(reference_text + "\n", encoding="utf-8")

    dur = sf.info(str(out_wav)).duration
    meta = {
        "source": str(src.relative_to(ROOT)) if src.is_relative_to(ROOT) else str(src),
        "abs_start_sec": abs_start,
        "duration_sec": dur,
        "demucs": not already_vocals and not args.skip_demucs,
        "demucs_ok": demucs_ok,
        "reference_text": reference_text,
        "out_wav": str(out_wav.relative_to(ROOT)) if out_wav.is_relative_to(ROOT) else str(out_wav),
        "out_txt": str(out_txt.relative_to(ROOT)) if out_txt.is_relative_to(ROOT) else str(out_txt),
    }
    out_meta.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {out_wav} ({dur:.1f}s)", flush=True)
    print(f"Wrote {out_txt}", flush=True)
    preview = reference_text[:120] + ("..." if len(reference_text) > 120 else "")
    print(f"Transcript ({len(reference_text)} chars): {preview!r}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
