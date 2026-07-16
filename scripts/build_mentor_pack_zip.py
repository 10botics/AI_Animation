"""
Build a confidential mentor pack ZIP for offline handout (USB / secure share).

Extract into the AI_Animation project ROOT so paths match scripts and skills:
  Comic Source/Chapter-81/   manga pages + stage story files
  Voice Reference/             Qwen voice timbre clips (mentor-provided)
  docs/reference/       character portrait refs (e.g. Macht) when present
  .env                  FAL_KEY= empty — each student/mentor adds their own key

NOT included — students create these during the lesson:
  panels/               panel crops (Step 3+)
  shots/                per-shot stills, voice, video, lip-sync (see README)
  outputs/              Fal API logs, SFX, analysis

NOT included — copyright / too large / per-machine:
  voice_refs/, video source/, *.mp4, .env, voice_registry.local.json

Usage:
  python scripts/build_mentor_pack_zip.py
  python scripts/build_mentor_pack_zip.py --out dist/AI_Animation-mentor-pack.zip
"""

from __future__ import annotations

import argparse
import zipfile
from datetime import date
from pathlib import Path

from chapter_paths import COMIC_SOURCE_DIR, is_chapter_dir

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "AI_Animation-mentor-pack.zip"
ENV_EXAMPLE = ROOT / ".env.example"

CHAPTER_PACK_NAME = "Chapter-81"
PACK_CHAPTER_ARC = f"Comic Source/{CHAPTER_PACK_NAME}"

# Mentor-only assets at project root (merge on extract).
PACK_DIRS = (
    "Voice Reference",
)

# Optional — included when folder exists (character portrait PNGs for Fal multi-ref).
OPTIONAL_PACK_DIRS = (
    "docs/reference",
)

README_NAME = "MENTOR_PACK_README.txt"
README_BODY = """10botics AI_Animation — Mentor pack (confidential)
=====================================================

Extract this ZIP into your AI_Animation project ROOT (merge folders).

  Example: C:\\AI_Animation\\

Included (mentor handout only):
  Comic Source\\Chapter-81\\   manga JPGs + stage_01–03 story files
  Voice Reference\\              Qwen voice timbre (.wav + .txt) for Frieren, Fern, Stark
  docs\\reference\\      character portrait refs when shipped (e.g. Macht)
  .env                   template with FAL_KEY= blank — paste your key after extract

NOT in this ZIP — students build these in class with Cursor Agent:
  panels\\eng\\ and panels\\jap\\     panel crops from full manga pages
  shots\\S###\\                       per-shot WIP + approved still/voice/video/lipsync
  outputs\\fal\\                      API logs (optional)

Legacy folders (still supported by scanner fallbacks):
  Tests\\Final\\                      old still layout
  outputs\\voice\\, outputs\\video\\   old voice/video layout

Do NOT upload this ZIP or its contents to public GitHub.

Still required on each PC:
  FAL_KEY in .env       get a key at https://fal.ai/dashboard/keys and paste after FAL_KEY=
  .venv\\                python -m venv .venv && pip install -r requirements.txt

Rebuild pack: python scripts\\build_mentor_pack_zip.py
Pack date: {pack_date}
"""


def _mentor_env_bytes() -> bytes:
    """Safe .env for the pack: same layout as .env.example, FAL_KEY always empty."""
    if ENV_EXAMPLE.is_file():
        lines = ENV_EXAMPLE.read_text(encoding="utf-8").splitlines()
    else:
        lines = [
            "# Fal.ai API key — paste your key after FAL_KEY=",
            "# https://fal.ai/dashboard/keys",
            "",
            "FAL_KEY=",
        ]
    out: list[str] = []
    for line in lines:
        if line.strip().upper().startswith("FAL_KEY") and "=" in line:
            out.append("FAL_KEY=")
        else:
            out.append(line)
    if not any(l.strip().upper().startswith("FAL_KEY") for l in out):
        out.append("FAL_KEY=")
    text = "\n".join(out).rstrip() + "\n"
    return text.encode("utf-8")


def _iter_files(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    return sorted(p for p in folder.rglob("*") if p.is_file())


def _add_tree(zf: zipfile.ZipFile, src_dir: Path, *, arc_prefix: str) -> tuple[int, int]:
    files = _iter_files(src_dir)
    total_bytes = 0
    for path in files:
        rel = path.relative_to(src_dir).as_posix()
        arc = f"{arc_prefix}/{rel}" if arc_prefix else rel
        zf.write(path, arc)
        total_bytes += path.stat().st_size
    return len(files), total_bytes


def _chapter_source_for_pack() -> Path:
    candidate = COMIC_SOURCE_DIR / CHAPTER_PACK_NAME
    if is_chapter_dir(candidate):
        return candidate
    raise FileNotFoundError(
        f"Chapter source not found — need `{PACK_CHAPTER_ARC}/` with stage_02_shot_list.md"
    )


def build_mentor_pack(*, out_path: Path) -> Path:
    missing = [d for d in PACK_DIRS if not (ROOT / d).is_dir()]
    chapter_src = _chapter_source_for_pack()
    if missing:
        raise FileNotFoundError(
            "Missing required mentor folders at project root: "
            + ", ".join(missing)
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    pack_date = date.today().isoformat()

    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.writestr(README_NAME, README_BODY.format(pack_date=pack_date))
        zf.writestr(".env", _mentor_env_bytes())
        print("  + .env: FAL_KEY= (empty)", flush=True)

        count, nbytes = _add_tree(zf, chapter_src, arc_prefix=PACK_CHAPTER_ARC)
        print(
            f"  + {PACK_CHAPTER_ARC} (from {chapter_src.relative_to(ROOT)}): "
            f"{count} files, {nbytes / (1024 * 1024):.2f} MB",
            flush=True,
        )

        for name in PACK_DIRS:
            src = ROOT / name
            count, nbytes = _add_tree(zf, src, arc_prefix=name.replace("\\", "/"))
            print(f"  + {name}: {count} files, {nbytes / (1024 * 1024):.2f} MB", flush=True)

        for name in OPTIONAL_PACK_DIRS:
            src = ROOT / name
            if not src.is_dir():
                print(f"  ~ {name}: skipped (folder not present)", flush=True)
                continue
            count, nbytes = _add_tree(zf, src, arc_prefix=name.replace("\\", "/"))
            print(f"  + {name}: {count} files, {nbytes / (1024 * 1024):.2f} MB", flush=True)

    total_mb = out_path.stat().st_size / (1024 * 1024)
    print(f"\nWrote: {out_path} ({total_mb:.2f} MB compressed)", flush=True)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build confidential mentor pack ZIP.")
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Output zip path (default: {DEFAULT_OUT.name} at repo root)",
    )
    args = parser.parse_args()
    out = args.out if args.out.is_absolute() else ROOT / args.out
    print("Building mentor pack (chapter + Voice Reference only)...", flush=True)
    build_mentor_pack(out_path=out)


if __name__ == "__main__":
    main()
