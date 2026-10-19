"""Text-to-speech adapters.

TTS runs only from a *reviewed* script (a script change regenerates the audio),
so the draft pipeline never calls it. Only the stub exists until an
Indian-English voice is wired behind this interface; it reuses the existing
`upload_topic_audio.py` Supabase-storage pattern when added.
"""
from __future__ import annotations

from app.pipeline.adapters.base import AudioResult


class StubTTSAdapter:
    name = "stub"

    def synthesize(self, script: str) -> AudioResult:
        return AudioResult(script=script, audio=None, placeholder=True)
