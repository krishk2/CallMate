"""Deepgram Flux streaming STT (default for English/Hindi — native turn detection).
TODO (Week 2, docs/HANDOFF.md §6.1.3): implement against `deepgram-sdk`, model
`flux-general-en` / `flux-general-multi`. Add the dependency to pipeline/pyproject.toml
when this is implemented — don't pull it in before it's used.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from ..config import settings
from .base import STTProvider, STTResult


class DeepgramFluxProvider(STTProvider):
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or settings.deepgram_api_key

    async def start(self, *, language_hint: str, keyterms: list[str] | None = None) -> None:
        raise NotImplementedError("DeepgramFluxProvider: see TODO at top of module")

    async def send_audio(self, chunk: bytes) -> None:
        raise NotImplementedError

    async def results(self) -> AsyncIterator[STTResult]:
        raise NotImplementedError
        yield  # pragma: no cover - makes this an async generator for type-checking

    async def close(self) -> None:
        raise NotImplementedError
