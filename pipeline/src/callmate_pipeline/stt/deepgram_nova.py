"""Deepgram Nova-3 streaming STT (Telugu `language=te`, or `en-IN`).
TODO (Week 5, docs/HANDOFF.md §6.1.3): implement against `deepgram-sdk` using
`endpointing` + `utterance_end` events for turn-taking (Nova-3 has no native turn detection).
Add the dependency to pipeline/pyproject.toml when this is implemented.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from ..config import settings
from .base import STTProvider, STTResult


class DeepgramNovaProvider(STTProvider):
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or settings.deepgram_api_key

    async def start(self, *, language_hint: str, keyterms: list[str] | None = None) -> None:
        raise NotImplementedError("DeepgramNovaProvider: see TODO at top of module")

    async def send_audio(self, chunk: bytes) -> None:
        raise NotImplementedError

    async def results(self) -> AsyncIterator[STTResult]:
        raise NotImplementedError
        yield  # pragma: no cover

    async def close(self) -> None:
        raise NotImplementedError
