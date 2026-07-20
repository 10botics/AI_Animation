"""
Launch AI Animation Studio (Streamlit) on a configurable port and chapter.

Default port 8501. Second instance example:
  python scripts/start_studio.py --port 8502 --chapter Chapter-82

Or in .env:
  STUDIO_PORT=8502
  STUDIO_CHAPTER=Chapter-82

Used by Start-Studio.bat / Start-Studio.ps1 at project root.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DASHBOARD = ROOT / "scripts" / "beginner_dashboard.py"
DEFAULT_PORT = 8501


def _load_env() -> None:
    load_dotenv(ROOT / ".env", override=False)
    load_dotenv(ROOT / ".env.local", override=True)


def resolve_port(cli_port: int | None) -> int:
    _load_env()
    if cli_port is not None:
        return cli_port
    from_env = os.environ.get("STUDIO_PORT", "").strip()
    if from_env:
        return int(from_env)
    return DEFAULT_PORT


def resolve_chapter(cli_chapter: str | None) -> str:
    _load_env()
    if cli_chapter is not None and cli_chapter.strip():
        return cli_chapter.strip()
    return os.environ.get("STUDIO_CHAPTER", "").strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Start AI Animation Studio (Streamlit)")
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help=f"Server port (default: STUDIO_PORT in .env, else {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--chapter",
        type=str,
        default=None,
        help="Default comic chapter folder name under Comic Source/ (STUDIO_CHAPTER in .env)",
    )
    args = parser.parse_args()
    port = resolve_port(args.port)
    chapter = resolve_chapter(args.chapter)
    if not (1024 <= port <= 65535):
        print(f"Invalid port {port} — use 1024–65535", file=sys.stderr)
        return 1
    if not DASHBOARD.is_file():
        print(f"Dashboard not found: {DASHBOARD}", file=sys.stderr)
        return 1

    env = os.environ.copy()
    if chapter:
        env["STUDIO_CHAPTER"] = chapter

    url = f"http://localhost:{port}"
    if chapter:
        url += f"?chapter={chapter.replace(' ', '%20')}"
    print(f"Starting AI Animation Studio at {url}", flush=True)
    if chapter:
        print(f"Default chapter: {chapter}", flush=True)
    print("Press Ctrl+C to stop.", flush=True)
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(DASHBOARD),
        f"--server.port={port}",
        "--server.headless=true",
    ]
    return subprocess.call(cmd, cwd=str(ROOT), env=env)


if __name__ == "__main__":
    raise SystemExit(main())
