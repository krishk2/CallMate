"""Silent-audio TTS stand-in: yields mu-law silence frames sized to the input text, so the
rest of the pipeline can be developed and tested with zero TTS provider/API key.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from .base import TTSChunk, TTSProvider

_MU_LAW_SILENCE_BYTE = 0xFF
_SAMPLE_RATE = 8000
_FRAME_MS = 20
_FRAME_SAMPLES = _SAMPLE_RATE * _FRAME_MS // 1000


class MockTTSProvider(TTSProvider):
    def __init__(self) -> None:
        self._cancelled = False

    async def synthesize(self, text: str) -> AsyncIterator[TTSChunk]:
        self._cancelled = False
        frame = bytes([_MU_LAW_SILENCE_BYTE]) * _FRAME_SAMPLES
        frame_count = max(1, len(text) // 10)
        for i in range(frame_count):
            if self._cancelled:
                return
            yield TTSChunk(audio=frame, is_final=(i == frame_count - 1))
            await asyncio.sleep(0)

    async def cancel(self) -> None:
        self._cancelled = True
