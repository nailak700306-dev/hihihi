# Default voice-over settings (approved)

Use these for every new video unless told otherwise:

- Provider: ElevenLabs API (`api.elevenlabs.io`, key stored as a network secret)
- Voice: Brian (`nPczCjzI2devNBz1zQrb`)
- Model: `eleven_multilingual_v2` (no `[tags]` in the text)
- voice_settings: stability 0.4, similarity_boost 0.8, style 0.35, use_speaker_boost true, speed 1.12
- Output: `mp3_44100_128`, one file per script line
- Post-processing: only trim leading/trailing silence. NO time-stretch, NO internal pause removal.
- Mix: gentle voice compression, music at 0.24 with ducking under the voice, final loudnorm -14 LUFS
- Reference implementation: `video/overthinking/audio_overthinking.py`
