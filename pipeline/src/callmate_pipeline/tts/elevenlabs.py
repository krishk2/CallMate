"""ElevenLabs streaming TTS (Flash-class model, `ulaw_8000` output — no resampling needed),
using an Instant Voice Clone made only from the user's own consented samples
(docs/HANDOFF.md §8 — never clone a caller's voice).
TODO (Week 3, docs/HANDOFF.md §6.1.6): implement against the ElevenLabs streaming API.
Add the dependency to pipeline/pyproject.toml when this is implemented.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from ..config import settings
from .base import TTSChunk, TTSProvider


class ElevenLabsProvider(TTSProvider):
    def __init__(self, api_key: str | None = None, voice_id: str | None = None) -> None:
        self._api_key = api_key or settings.elevenlabs_api_key
        self._voice_id = voice_id or settings.elevenlabs_voice_id

    async def synthesize(self, text: str) -> AsyncIterator[TTSChunk]:
        raise NotImplementedError("ElevenLabsProvider: see TODO at top of module")
        yield  # pragma: no cover

    async def cancel(self) -> None:
        raise NotImplementedError
