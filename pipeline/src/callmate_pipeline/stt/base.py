"""STT provider protocol. Every provider (Deepgram Flux/Nova, Google V2, mock) implements this
and only this — callers (media/stream_ws.py, session/call_session.py) depend on `STTProvider`,
never on a concrete SDK client.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass(frozen=True)
class STTResult:
    text: str
    confidence: float
    is_final: bool


class STTProvider(ABC):
    """Streaming speech-to-text. One instance per call."""

    @abstractmethod
    async def start(self, *, language_hint: str, keyterms: list[str] | None = None) -> None:
        """Open the provider's stream for this call."""

    @abstractmethod
    async def send_audio(self, chunk: bytes) -> None:
        """Feed one frame of mu-law 8kHz audio."""

    @abstractmethod
    def results(self) -> AsyncIterator[STTResult]:
        """Yield partial and final transcription results as they arrive."""

    @abstractmethod
    async def close(self) -> None:
        """Flush and close the provider stream."""
