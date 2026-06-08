"""
Extract one character's dubbed voice from compilation videos (speaker clustering).

Pipeline per source file:
  1. ffmpeg → 16 kHz mono WAV
  2. (optional) Demucs two-stem vocals
  3. Silero VAD speech segments
  4. SpeechBrain ECAPA embeddings per segment
  5. Cluster embeddings across all inputs; keep the cluster with most speech time
     (or match --reference WAV)

Requires: ffmpeg, torch, soundfile, silero-vad, speechbrain, scikit-learn.
Optional: demucs (`pip install demucs`), HF_TOKEN for pyannote (not used here).

Usage (PowerShell):
  cd scripts
  python extract_character_voice.py --character Frieren --input-dir "..\\video source"
  python extract_character_voice.py --character Frieren --input-dir "..\\video source" --reference "..\\voice_refs\\frieren_ref.wav"
  python extract_character_voice.py --skip-demucs   # faster; more BGM bleed
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from silero_vad import get_speech_timestamps, load_silero_vad
from sklearn.cluster import AgglomerativeClustering
from speechbrain.inference.classifiers import EncoderClassifier

from fal_common import ROOT

SAMPLE_RATE = 16_000
MIN_SEGMENT_SEC = 0.45
CLUSTER_DISTANCE = 0.42
MERGE_CENTROID_COSINE = 0.68
EXPAND_MAIN_COSINE = 0.55


@dataclass
class Segment:
    source: str
    start: float
    end: float
    cluster: int = -1

    @property
    def duration(self) -> float:
        return self.end - self.start


def _load_speaker_encoder(model_dir: Path) -> EncoderClassifier:
    """Stable local copy (no Windows symlinks) for ECAPA embeddings."""
    hparams = model_dir / "hyperparams.yaml"
    if not hparams.is_file() or hparams.stat().st_size < 200:
        if model_dir.exists():
            shutil.rmtree(model_dir)
        from huggingface_hub import snapshot_download

        model_dir.mkdir(parents=True, exist_ok=True)
        snapshot_download(
            "speechbrain/spkrec-ecapa-voxceleb",
            local_dir=str(model_dir),
            local_dir_use_symlinks=False,
        )
    return EncoderClassifier.from_hparams(source=str(model_dir), savedir=str(model_dir))


def _slug(name: str) -> str:
    s = Path(name).stem
    s = re.sub(r"[^\w\-]+", "_", s, flags=re.UNICODE)
    return s.strip("_")[:80] or "source"


def _run(cmd: list[str], label: str) -> None:
    line = f"{label}: {' '.join(cmd)}"
    try:
        print(line, flush=True)
    except UnicodeEncodeError:
        print(f"{label}: (see output path in manifest)", flush=True)
    subprocess.run(cmd, check=True)


def _load_mono_16k(path: Path) -> torch.Tensor:
    data, sr = sf.read(str(path), dtype="float32")
    if data.ndim > 1:
        data = data.mean(axis=1)
    wav = torch.from_numpy(data)
    if sr != SAMPLE_RATE:
        import torchaudio

        wav = torchaudio.functional.resample(wav.unsqueeze(0), sr, SAMPLE_RATE).squeeze(0)
    return wav


def _extract_audio_from_video(video: Path, wav_out: Path) -> None:
    wav_out.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video),
            "-vn",
            "-ac",
            "1",
            "-ar",
            str(SAMPLE_RATE),
            str(wav_out),
        ],
        "ffmpeg",
    )


def _demucs_vocals(wav_in: Path, work_dir: Path) -> Path:
    out_root = work_dir / "demucs_out"
    out_root.mkdir(parents=True, exist_ok=True)
    _run(
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
        "demucs",
    )
    stem = wav_in.stem
    vocals = out_root / "htdemucs" / stem / "vocals.wav"
    if not vocals.is_file():
        raise FileNotFoundError(f"Demucs vocals not found: {vocals}")
    return vocals


def _vad_segments(wav: torch.Tensor, model) -> list[tuple[int, int]]:
    ts = get_speech_timestamps(
        wav,
        model,
        sampling_rate=SAMPLE_RATE,
        min_speech_duration_ms=300,
        min_silence_duration_ms=250,
    )
    return [(t["start"], t["end"]) for t in ts]


def _embed_segment(spk: EncoderClassifier, wav: torch.Tensor, start: int, end: int) -> np.ndarray | None:
    if end <= start or (end - start) / SAMPLE_RATE < MIN_SEGMENT_SEC:
        return None
    chunk = wav[start:end].unsqueeze(0)
    with torch.no_grad():
        emb = spk.encode_batch(chunk)
    vec = emb.squeeze().cpu().numpy()
    norm = np.linalg.norm(vec)
    if norm < 1e-8:
        return None
    return vec / norm


def _concat_segments(wav: torch.Tensor, segments: list[Segment], pad_ms: int = 40) -> torch.Tensor:
    pad = int(SAMPLE_RATE * pad_ms / 1000)
    parts: list[torch.Tensor] = []
    for seg in segments:
        s = int(seg.start * SAMPLE_RATE)
        e = int(seg.end * SAMPLE_RATE)
        parts.append(wav[s:e])
        if pad:
            parts.append(torch.zeros(pad))
    if not parts:
        return torch.zeros(0)
    return torch.cat(parts)


def _save_wav(path: Path, tensor: torch.Tensor) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), tensor.numpy(), SAMPLE_RATE)


def _merge_similar_clusters(
    labels: np.ndarray, embeddings: list[np.ndarray], threshold: float
) -> np.ndarray:
    """Merge clusters whose centroids are very similar (same dub VA split by VAD)."""
    unique = sorted(set(int(x) for x in labels))
    centroids: dict[int, np.ndarray] = {}
    for lab in unique:
        idx = [i for i, l in enumerate(labels) if int(l) == lab]
        centroids[lab] = np.mean([embeddings[i] for i in idx], axis=0)
        n = np.linalg.norm(centroids[lab])
        if n > 1e-8:
            centroids[lab] /= n

    parent = {lab: lab for lab in unique}

    def find(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    labs = list(unique)
    for i, a in enumerate(labs):
        for b in labs[i + 1 :]:
            sim = float(np.dot(centroids[a], centroids[b]))
            if sim >= threshold:
                union(a, b)

    remap = {lab: find(lab) for lab in unique}
    return np.array([remap[int(l)] for l in labels], dtype=int)


def _expand_around_main_cluster(
    labels: np.ndarray, embeddings: list[np.ndarray], segments: list[Segment], threshold: float
) -> np.ndarray:
    """Attach smaller clusters that sound like the dominant speaker (split VA shards)."""
    durs: dict[int, float] = {}
    for seg in segments:
        durs[seg.cluster] = durs.get(seg.cluster, 0.0) + seg.duration
    main = max(durs, key=durs.get)
    idx_main = [i for i, s in enumerate(segments) if s.cluster == main]
    main_c = np.mean([embeddings[i] for i in idx_main], axis=0)
    n = np.linalg.norm(main_c)
    if n > 1e-8:
        main_c /= n

    out = labels.copy()
    for lab in sorted(set(int(x) for x in labels)):
        if lab == main:
            continue
        idx = [i for i, s in enumerate(segments) if s.cluster == lab]
        c = np.mean([embeddings[i] for i in idx], axis=0)
        nc = np.linalg.norm(c)
        if nc > 1e-8:
            c /= nc
        if float(np.dot(main_c, c)) >= threshold:
            out[out == lab] = main
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract one dub character voice from videos")
    parser.add_argument("--character", default="Frieren", help="Label for outputs")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=ROOT / "video source",
        help="Folder of .webm/.mp4 sources",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "outputs" / "voice_extraction",
        help="Output root",
    )
    parser.add_argument("--reference", type=Path, default=None, help="Optional reference WAV for speaker match")
    parser.add_argument("--skip-demucs", action="store_true", help="Skip vocal separation (faster)")
    parser.add_argument("--cluster-distance", type=float, default=CLUSTER_DISTANCE)
    parser.add_argument(
        "--merge-cosine",
        type=float,
        default=MERGE_CENTROID_COSINE,
        help="Merge clusters with centroid cosine >= this (same actor)",
    )
    parser.add_argument(
        "--expand-main-cosine",
        type=float,
        default=EXPAND_MAIN_COSINE,
        help="Merge side clusters into main if similar to dominant speaker",
    )
    parser.add_argument("--max-files", type=int, default=0, help="Limit files (0 = all)")
    args = parser.parse_args()

    input_dir = args.input_dir.resolve()
    if not input_dir.is_dir():
        print(f"Input dir not found: {input_dir}", file=sys.stderr)
        return 1

    videos = sorted(
        p
        for p in input_dir.iterdir()
        if p.suffix.lower() in {".webm", ".mp4", ".mkv", ".mov", ".m4v"}
    )
    if args.max_files:
        videos = videos[: args.max_files]
    if not videos:
        print(f"No videos in {input_dir}", file=sys.stderr)
        return 1

    char_slug = re.sub(r"[^\w]+", "_", args.character.strip().lower())
    out_root = args.out_dir.resolve() / char_slug
    work = out_root / "_work"
    work.mkdir(parents=True, exist_ok=True)

    print("Loading Silero VAD + SpeechBrain ECAPA …", flush=True)
    vad_model = load_silero_vad()
    model_dir = ROOT / "outputs" / "voice_extraction" / "_models" / "spkrec"
    spk = _load_speaker_encoder(model_dir)

    ref_emb: np.ndarray | None = None
    if args.reference and args.reference.is_file():
        ref_wav = _load_mono_16k(args.reference.resolve())
        ref_emb = _embed_segment(spk, ref_wav, 0, len(ref_wav))
        if ref_emb is None:
            print("Reference too short or silent.", file=sys.stderr)
            return 1
        print(f"Using reference: {args.reference}", flush=True)

    all_segments: list[Segment] = []
    embeddings: list[np.ndarray] = []
    wav_by_source: dict[str, torch.Tensor] = {}

    for video in videos:
        slug = _slug(video.name)
        src_work = work / slug
        src_work.mkdir(parents=True, exist_ok=True)
        raw_wav = src_work / "full.wav"
        _extract_audio_from_video(video, raw_wav)
        audio_path = raw_wav
        if not args.skip_demucs:
            try:
                audio_path = _demucs_vocals(raw_wav, src_work)
            except subprocess.CalledProcessError as e:
                print(f"Demucs failed for {video.name}, using full mix: {e}", flush=True)
                audio_path = raw_wav

        wav = _load_mono_16k(audio_path)
        wav_by_source[slug] = wav
        for start_i, end_i in _vad_segments(wav, vad_model):
            emb = _embed_segment(spk, wav, start_i, end_i)
            if emb is None:
                continue
            seg = Segment(
                source=slug,
                start=start_i / SAMPLE_RATE,
                end=end_i / SAMPLE_RATE,
            )
            all_segments.append(seg)
            embeddings.append(emb)

    if not embeddings:
        print("No speech segments found.", file=sys.stderr)
        return 1

    X = np.stack(embeddings)
    clustering = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=args.cluster_distance,
        metric="cosine",
        linkage="average",
    )
    labels = clustering.fit_predict(X)
    labels = _merge_similar_clusters(labels, embeddings, args.merge_cosine)
    for seg, lab in zip(all_segments, labels):
        seg.cluster = int(lab)
    labels = _expand_around_main_cluster(labels, embeddings, all_segments, args.expand_main_cosine)
    for seg, lab in zip(all_segments, labels):
        seg.cluster = int(lab)

    cluster_dur: dict[int, float] = {}
    for seg in all_segments:
        cluster_dur[seg.cluster] = cluster_dur.get(seg.cluster, 0.0) + seg.duration

    if ref_emb is not None:
        scores = {
            c: float(np.mean([np.dot(ref_emb, embeddings[i]) for i, s in enumerate(all_segments) if s.cluster == c]))
            for c in cluster_dur
        }
        target_cluster = max(scores, key=scores.get)
        pick_reason = "reference_similarity"
    else:
        target_cluster = max(cluster_dur, key=cluster_dur.get)
        pick_reason = "most_speech_time"

    target_segments = [s for s in all_segments if s.cluster == target_cluster]
    print(
        f"Picked cluster {target_cluster} ({pick_reason}): "
        f"{len(target_segments)} segments, {sum(s.duration for s in target_segments):.1f}s",
        flush=True,
    )

    per_video_dir = out_root / "per_video"
    per_video_dir.mkdir(parents=True, exist_ok=True)
    for slug, wav in wav_by_source.items():
        segs = [s for s in target_segments if s.source == slug]
        out_v = per_video_dir / f"{slug}_{char_slug}_only.wav"
        _save_wav(out_v, _concat_segments(wav, segs))
        demucs_vocals = work / slug / "demucs_out" / "htdemucs" / "full" / "vocals.wav"
        stem_src = demucs_vocals if demucs_vocals.is_file() else (work / slug / "full.wav")
        if stem_src.is_file():
            qc = per_video_dir / f"{slug}_vocals_stem.wav"
            import shutil

            shutil.copy2(stem_src, qc)

    master_parts: list[torch.Tensor] = []
    gap = torch.zeros(int(SAMPLE_RATE * 0.12))
    for video in videos:
        slug = _slug(video.name)
        segs = sorted([s for s in target_segments if s.source == slug], key=lambda s: s.start)
        if not segs:
            continue
        master_parts.append(_concat_segments(wav_by_source[slug], segs))
        master_parts.append(gap)
    master = torch.cat(master_parts) if master_parts else torch.zeros(0)
    master_path = out_root / f"{char_slug}_all.wav"  # e.g. frieren_all.wav
    _save_wav(master_path, master)

    # All detected speech (every speaker) — useful for manual curation / clone refs
    all_speech_parts: list[torch.Tensor] = []
    gap = torch.zeros(int(SAMPLE_RATE * 0.08))
    for video in videos:
        slug = _slug(video.name)
        segs = sorted(all_segments, key=lambda s: (s.source, s.start))
        segs = [s for s in segs if s.source == slug]
        if segs:
            all_speech_parts.append(_concat_segments(wav_by_source[slug], segs))
            all_speech_parts.append(gap)
    all_speech_path = out_root / "all_dialogue_vad.wav"
    if all_speech_parts:
        _save_wav(all_speech_path, torch.cat(all_speech_parts))

    # Export other top clusters for manual QC (up to 2 alternates)
    alt_dir = out_root / "clusters_qc"
    alt_dir.mkdir(exist_ok=True)
    ranked = sorted(cluster_dur.items(), key=lambda x: -x[1])
    for rank, (cid, dur) in enumerate(ranked[:3]):
        if cid == target_cluster:
            continue
        alt_segs = [s for s in all_segments if s.cluster == cid]
        parts = []
        for slug in wav_by_source:
            parts.append(_concat_segments(wav_by_source[slug], [s for s in alt_segs if s.source == slug]))
        if parts:
            _save_wav(alt_dir / f"cluster_{cid}_rank{rank}.wav", torch.cat(parts) if len(parts) > 1 else parts[0])

    manifest = {
        "character": args.character,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "input_dir": str(input_dir),
        "sources": [v.name for v in videos],
        "skip_demucs": args.skip_demucs,
        "cluster_distance": args.cluster_distance,
        "merge_cosine": args.merge_cosine,
        "expand_main_cosine": args.expand_main_cosine,
        "pick_reason": pick_reason,
        "target_cluster": target_cluster,
        "cluster_durations_sec": {str(k): round(v, 2) for k, v in sorted(cluster_dur.items())},
        "target_segment_count": len(target_segments),
        "target_duration_sec": round(sum(s.duration for s in target_segments), 2),
        "master_wav": str(master_path.relative_to(ROOT)),
        "all_dialogue_vad_wav": str(all_speech_path.relative_to(ROOT)) if all_speech_parts else None,
        "all_dialogue_duration_sec": round(sum(s.duration for s in all_segments), 2),
        "segments": [asdict(s) for s in target_segments],
        "notes": (
            "Automated speaker clustering — not 100% Frieren-only. "
            "Other characters in compilations may leak in. "
            "Use clusters_qc/ alternates or --reference for tighter match. "
            "For best clone refs: add HF_TOKEN and pyannote, or hand-trim per_video outputs."
        ),
    }
    manifest_path = out_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {master_path}", flush=True)
    print(f"Manifest: {manifest_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
