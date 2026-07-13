"""Backward-compatible entry — prefer normalize_artifacts.py."""

from normalize_artifacts import main

if __name__ == "__main__":
    raise SystemExit(main())
