"""Google Cloud TTS (Chirp 3 HD / Neural2 `en-IN`, `te-IN`) — generic-voice fallback behind
the same TTSProvider interface as ElevenLabs.
TODO (fallback priority, docs/HANDOFF.md §1.2): implement against `google-cloud-texttospeech`.
Add the dependency to pipeline/pyproject.toml when this is implemented.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from ..config import settings
from .base import TTSChunk, TTSProvider


class GoogleTTSProvider(TTSProvider):
    def __init__(self, credentials_path: str | None = None) -> None:
        self._credentials_path = credentials_path or settings.google_application_credentials

    async def synthesize(self, text: str) -> AsyncIterator[TTSChunk]:
        raise NotImplementedError("GoogleTTSProvider: see TODO at top of module")
        yield  # pragma: no cover

    async def cancel(self) -> None:
        raise NotImplementedError
