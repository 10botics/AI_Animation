"""Canonical paths for production voice references and processing workspace."""

from __future__ import annotations

from fal_common import ROOT

# Curated ~12s Qwen clone refs (language → character)
VOICE_REFERENCE = ROOT / "Voice Reference"
VR_JP_FRIEREN = VOICE_REFERENCE / "Japanese" / "Frieren"
VR_JP_FERN = VOICE_REFERENCE / "Japanese" / "Fern"
VR_JP_STARK = VOICE_REFERENCE / "Japanese" / "Stark"
VR_EN_FRIEREN = VOICE_REFERENCE / "English" / "Frieren"

# Demucs / VAD / full extracts (not production refs)
VOICE_REFS_WORK = ROOT / "voice_refs"
