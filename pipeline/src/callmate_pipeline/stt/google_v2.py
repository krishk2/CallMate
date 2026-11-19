"""Google Cloud Speech-to-Text V2 (telephony/Chirp models) — fallback behind the same
STTProvider interface as the Deepgram providers.
TODO (fallback priority, docs/HANDOFF.md §1.2): implement against `google-cloud-speech`.
Add the dependency to pipeline/pyproject.toml when this is implemented.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from ..config import settings
from .base import STTProvider, STTResult


class GoogleSTTProvider(STTProvider):
    def __init__(self, credentials_path: str | None = None) -> None:
        self._credentials_path = credentials_path or settings.google_application_credentials

    async def start(self, *, language_hint: str, keyterms: list[str] | None = None) -> None:
        raise NotImplementedError("GoogleSTTProvider: see TODO at top of module")

    async def send_audio(self, chunk: bytes) -> None:
        raise NotImplementedError

    async def results(self) -> AsyncIterator[STTResult]:
        raise NotImplementedError
        yield  # pragma: no cover

    async def close(self) -> None:
        raise NotImplementedError
