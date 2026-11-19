"""Deterministic STT stand-in: emits scripted utterances as audio frames arrive, so the rest
of the pipeline can be developed and tested with zero STT provider/API key.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from .base import STTProvider, STTResult

_FRAMES_PER_UTTERANCE = 50  # ~1s of 20ms frames before each scripted line "lands"


class MockSTTProvider(STTProvider):
    def __init__(self, scripted_utterances: list[str] | None = None) -> None:
        self._pending = list(scripted_utterances or ["This is a mock transcript."])
        self._queue: asyncio.Queue[STTResult] = asyncio.Queue()
        self._frames_received = 0

    async def start(self, *, language_hint: str, keyterms: list[str] | None = None) -> None:
        self._frames_received = 0

    async def send_audio(self, chunk: bytes) -> None:
        self._frames_received += 1
        if self._pending and self._frames_received % _FRAMES_PER_UTTERANCE == 0:
            text = self._pending.pop(0)
            await self._queue.put(STTResult(text=text, confidence=0.95, is_final=True))

    async def results(self) -> AsyncIterator[STTResult]:
        while True:
            yield await self._queue.get()

    async def close(self) -> None:
        return None
