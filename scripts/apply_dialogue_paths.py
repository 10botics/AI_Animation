"""Point dialogue generators at shots/S###/voice/ layout."""

from __future__ import annotations

import re
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
IMPORT = "from artifact_paths import ensure_parent, promote_voice_wip, voice_wip_path\n"
SPEAKERS = ("frieren", "fern", "stark", "denken", "lernen")


def speaker_from_path(path_expr: str) -> str:
    for sp in SPEAKERS:
        if sp in path_expr.lower():
            return sp
    return "voice"


def fix(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    orig = text
    m = re.search(r'SHOT_ID = "(S\d{3}[A-Z]?)"', text)
    if not m:
        return False
    sid = m.group(1)
    sid_l = sid.lower()

    if "voice_wip_path" not in text and "from fal_common import" in text:
        text = text.replace("from fal_common import", IMPORT + "from fal_common import", 1)

    text = text.replace(
        f'    out_dir = ROOT / "outputs" / "voice" / "{sid}"\n    out_dir.mkdir(parents=True, exist_ok=True)\n',
        "",
    )

    for sp in SPEAKERS:
        text = text.replace(
            f'    stem = out_dir / f"{sid_l}_{sp}_{{ts}}.mp3"',
            f'    stem = voice_wip_path(SHOT_ID, ts, ".mp3", tag="{sp}")\n    ensure_parent(stem)',
        )
        text = text.replace(
            f'    wav_path = out_dir / f"{sid_l}_{sp}_{{tag}}_{{ts}}.wav"',
            f'    wav_path = voice_wip_path(SHOT_ID, ts, ".wav", tag=f"{sp}_{{tag}}")\n    ensure_parent(wav_path)',
        )
        text = text.replace(
            f'    wav_path = out_dir / f"{sid_l}_{sp}_{{ts}}.wav"',
            f'    wav_path = voice_wip_path(SHOT_ID, ts, ".wav", tag="{sp}")\n    ensure_parent(wav_path)',
        )

    text = text.replace(
        '        stem = out_dir / f"s008_{line[\'speaker\'].lower()}_{ts}.mp3"',
        '        stem = voice_wip_path(SHOT_ID, ts, ".mp3", tag=line["speaker"].lower())\n        ensure_parent(stem)',
    )
    text = text.replace(
        '            wav_path = out_dir / f"s008_{speaker}_{tag}_{ts}.wav"',
        '            wav_path = voice_wip_path(SHOT_ID, ts, ".wav", tag=f"{speaker}_{tag}")\n            ensure_parent(wav_path)',
    )

    final_block = (
        f'        final_dir = ROOT / "outputs" / "voice" / "final" / "{sid}"\n'
        f"        final_dir.mkdir(parents=True, exist_ok=True)\n"
    )
    text = text.replace(final_block, "")

    text = text.replace(
        "        final_wav = final_dir / wav_path.name\n"
        "        final_wav.write_bytes(wav_path.read_bytes())\n"
        '        print(f"Final: {final_wav}", flush=True)\n',
        '        approved = promote_voice_wip(wav_path, SHOT_ID, "' + sid_l + '")\n'
        '        print(f"Approved: {approved}", flush=True)\n',
    )
    text = text.replace(
        "        shutil.copy2(wav_path, final_dir / wav_path.name)\n",
        "",
    )

    # per-speaker promote — fix placeholder sid with actual speaker from wav_path line above
    for sp in SPEAKERS:
        text = text.replace(
            f'    wav_path = voice_wip_path(SHOT_ID, ts, ".wav", tag=f"{sp}_{{tag}}")\n    ensure_parent(wav_path)\n    if not args.mux:\n        _mp3_to_wav(audio, wav_path)\n        print(f"WAV: {{wav_path}}", flush=True)\n        approved = promote_voice_wip(wav_path, SHOT_ID, "{sid_l}")',
            f'    wav_path = voice_wip_path(SHOT_ID, ts, ".wav", tag=f"{sp}_{{tag}}")\n    ensure_parent(wav_path)\n    if not args.mux:\n        _mp3_to_wav(audio, wav_path)\n        print(f"WAV: {{wav_path}}", flush=True)\n        approved = promote_voice_wip(wav_path, SHOT_ID, "{sp}")',
        )
        text = text.replace(
            f'    wav_path = voice_wip_path(SHOT_ID, ts, ".wav", tag="{sp}")\n    ensure_parent(wav_path)\n    if not args.mux:\n        _mp3_to_wav(audio, wav_path)\n        print(f"WAV: {{wav_path}}", flush=True)\n        approved = promote_voice_wip(wav_path, SHOT_ID, "{sid_l}")',
            f'    wav_path = voice_wip_path(SHOT_ID, ts, ".wav", tag="{sp}")\n    ensure_parent(wav_path)\n    if not args.mux:\n        _mp3_to_wav(audio, wav_path)\n        print(f"WAV: {{wav_path}}", flush=True)\n        approved = promote_voice_wip(wav_path, SHOT_ID, "{sp}")',
        )

    if 'print(f"WAV: {wav_path}", flush=True)\n    if not args.mux:' not in text:
        text = text.replace(
            '        print(f"WAV: {wav_path}", flush=True)\n',
            '        print(f"WAV: {wav_path}", flush=True)\n        approved = promote_voice_wip(wav_path, SHOT_ID, "frieren")\n        print(f"Approved: {approved}", flush=True)\n',
            1,
        )

    text = text.replace(
        f'meta_payload["wav_final"] = str(ROOT / "outputs" / "voice" / "final" / "{sid}" / wav_path.name)',
        'meta_payload["wav_final"] = str(voice_wip_path(SHOT_ID, ts, ".wav"))  # updated below',
    )

    text = re.sub(
        rf'    meta = out_dir / f"{sid_l}_([^"]+\.json)"',
        rf'    meta = ROOT / "outputs" / "fal" / f"{sid}_\1"',
        text,
    )

    if text != orig:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> None:
    n = sum(fix(p) for p in SCRIPTS.glob("generate_*dialogue*.py"))
    print(f"Fixed {n} dialogue scripts")


if __name__ == "__main__":
    main()
