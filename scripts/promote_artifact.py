"""
Promote a WIP artifact into the shot's approved/ folder (keeps the source filename).

Usage:
  python promote_artifact.py still S006 --from shots/S006/still/wip/nano-banana-2/20260330_035743.png
  python promote_artifact.py video S014 --from shots/S014/video/wip/kling-v26-pro/20260710_100541.mp4
  python promote_artifact.py lipsync S008 --from shots/S008/lipsync/wip/pixverse/20260604_045309.mp4
  python promote_artifact.py voice S006 --from shots/S006/voice/wip/qwen/fern_20260710_091920.wav --speaker fern
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from artifact_paths import (
    ensure_shot_layout,
    normalize_shot_id,
    promote_file,
    promote_to_approved,
    voice_approved_path,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote WIP file into approved/ folder")
    parser.add_argument("kind", choices=("still", "video", "lipsync", "voice"))
    parser.add_argument("shot_id", type=str)
    parser.add_argument("--from", dest="src", type=Path, required=True)
    parser.add_argument("--speaker", type=str, default="", help="Required for voice (e.g. fern, frieren)")
    args = parser.parse_args()

    sid = normalize_shot_id(args.shot_id)
    src = args.src.resolve()
    if not src.is_file():
        print(f"Source not found: {src}", file=sys.stderr)
        return 1

    ensure_shot_layout(sid)

    if args.kind == "voice":
        if not args.speaker:
            print("--speaker required for voice promote", file=sys.stderr)
            return 1
        dest = voice_approved_path(sid, args.speaker, src.suffix)
        promote_file(src, dest)
    else:
        dest = promote_to_approved(src, sid, args.kind)

    print(f"Promoted -> {dest}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
