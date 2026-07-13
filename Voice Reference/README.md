# Voice Reference

Production **~12s Qwen clone** clips used for AI dialogue (timbre + `reference_text`).

## Layout

```
Voice Reference/
├── Japanese/
│   ├── Frieren/     frieren_jp_qwen_ref.{wav,txt,json}
│   ├── Stark/       stark_jp_qwen_ref.{wav,txt,json}
│   ├── Fern/        fern_jp_qwen_ref.{wav,txt,json}
│   └── Denken/      denken_jp_qwen_ref.{wav,txt,json}
└── English/
    └── Frieren/     frieren_1min_qwen_ref.{wav,txt,json}  (EN dub timbre)
```

| Path | Character | Production TTS |
|------|-----------|----------------|
| `Japanese/Frieren/` | Frieren | Japanese (S004, S006, S008, S012, S016…) |
| `Japanese/Stark/` | Stark | Japanese (S011 canon, optional S012) |
| `Japanese/Fern/` | Fern | Japanese (S004, S005, S006) |
| `Japanese/Denken/` | Denken | Japanese (S016 warden; EN-dub timbre until JP Saito ref) |
| `English/Frieren/` | Frieren | English iterations / legacy |

**Processing chain** (full video, Demucs, VAD scans): [`voice_refs/`](../voice_refs/) — e.g. `starksource.mp4`, `starksource_vocals.wav`.

**Registry:** `voice_registry.local.json` → `qwen_speaker_embeddings`
