"""TTS provider protocol. Every provider (ElevenLabs, Google, mock) implements this and only
this — callers depend on `TTSProvider`, never on a concrete SDK client.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass(frozen=True)
class TTSChunk:
    audio: bytes  # mu-law 8kHz
    is_final: bool


class TTSProvider(ABC):
    """Streaming text-to-speech. One instance per call."""

    @abstractmethod
    def synthesize(self, text: str) -> AsyncIterator[TTSChunk]:
        """Stream synthesized mu-law 8kHz audio for one sentence/clause of text."""

    @abstractmethod
    async def cancel(self) -> None:
        """Stop any in-flight synthesis immediately (barge-in)."""
