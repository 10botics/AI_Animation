# SFX on Fal.ai — alternatives to text-only CassetteAI

Cassette **`cassetteai/sound-effects-generator`** (text → WAV) is cheap but often **misaligned** with picture. Prefer **video-conditioned** models when the final clip exists, and **Beatoven / ElevenLabs** for text when you still need stems.

**Background music (whole-edit underscore):** Not covered here — use [`prototype-video-music-analysis-guideline.md`](prototype-video-music-analysis-guideline.md) and skill [`.cursor/skills/prototype-video-music-analysis/SKILL.md`](../.cursor/skills/prototype-video-music-analysis/SKILL.md) (`fal-ai/minimax-music/v2.6`, etc.).

## Video in → sound / dubbed MP4 out

| Model ID | Role | Pricing (Fal `llms.txt`) | Notes |
|----------|------|---------------------------|--------|
| [`cassetteai/video-sound-effects-generator`](https://fal.ai/models/cassetteai/video-sound-effects-generator) | Analyzes clip, adds SFX, returns **video + new mix** | **~$0.20 / minute** | Same family as the text SFX you used; **vision-grounded** — try if text-only was wrong. |
| [`fal-ai/thinksound`](https://fal.ai/models/fal-ai/thinksound) | **Video + optional `prompt`** → **video with audio** | **~$0.001 / compute second** | Good default to A/B vs Cassette video; optional prompt guides foley. |
| [`fal-ai/kling-video/video-to-audio`](https://fal.ai/models/fal-ai/kling-video/video-to-audio) | **Video URL** + optional **`sound_effect_prompt`** / **`background_music_prompt`** → **dubbed video + MP3** | **~$0.035 / video** | **3–20 s**, ≤100 MB, `.mp4`/`.mov`. Set **both** prompts explicitly or defaults skew toward demo SFX. **`asmr_mode`** for detail foley. |
| [`mirelo-ai/sfx-v1.5/video-to-audio`](https://fal.ai/models/mirelo-ai/sfx-v1.5/video-to-audio) | **Video URL** + optional **`text_prompt`** → **list of WAV samples** (synced SFX) | Per Fal pricing | Good when **Beatoven** (text-only) is unavailable; repo: `scripts/generate_s002_sfx_mirelo.py` for S002. |

## Text → SFX (no video)

| Model ID | Pricing (typical) | Notes |
|----------|-------------------|--------|
| [`beatoven/sound-effect-generation`](https://fal.ai/models/beatoven/sound-effect-generation) | **~$0.10 / request** | **`negative_prompt`**, duration, seed — good control. |
| [`fal-ai/elevenlabs/sound-effects`](https://fal.ai/models/fal-ai/elevenlabs/sound-effects) | **~$0.002 / second** | **`prompt_influence`**, `duration_seconds` — often cleaner than bare Cassette text. |

## Repo helper

```powershell
cd scripts
python sfx_from_video.py --model thinksound --video "..\outputs\video\final\S004_kling-v26-pro_i2v_....mp4"
python sfx_from_video.py --model kling-v2a --video "....mp4" --asmr
python sfx_from_video.py --model cassette-video --video "....mp4"
```

Outputs go under `outputs/video/sfx/` (+ sidecar JSON in `outputs/fal/`).

Recheck each model’s live API page before batching; pricing and limits change on Fal.
