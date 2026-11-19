"""Voice activity detection for barge-in. `BargeInDetector` is the testable, provider-agnostic
part (docs/HANDOFF.md §6.1.5: >=250ms of speech while SPEAKING triggers barge-in) — it depends
on the `VoiceActivityDetector` protocol, not on any specific detector implementation.
"""

from __future__ import annotations

import audioop
from abc import ABC, abstractmethod


class VoiceActivityDetector(ABC):
    @abstractmethod
    def is_speech(self, pcm16_chunk: bytes) -> bool: ...


class EnergyThresholdVAD(VoiceActivityDetector):
    """RMS-energy VAD stopgap.
    TODO (docs/HANDOFF.md §6.1.5): replace with Silero VAD (local, torch-based) for real
    barge-in detection; add `silero-vad` + `torch` as pipeline dependencies when implemented.
    """

    def __init__(self, threshold: int = 500) -> None:
        self._threshold = threshold

    def is_speech(self, pcm16_chunk: bytes) -> bool:
        return audioop.rms(pcm16_chunk, 2) > self._threshold


class BargeInDetector:
    """Wraps any VoiceActivityDetector, requiring `min_speech_ms` of *consecutive* speech
    frames before reporting barge-in, so a single noise spike doesn't cut off playback.
    """

    def __init__(
        self,
        vad: VoiceActivityDetector,
        frame_ms: float = 20.0,
        min_speech_ms: float = 250.0,
    ) -> None:
        self._vad = vad
        self._min_frames = max(1, round(min_speech_ms / frame_ms))
        self._consecutive_speech_frames = 0

    def feed(self, pcm16_chunk: bytes) -> bool:
        """Returns True exactly once per barge-in, the frame where the threshold is crossed."""
        if not self._vad.is_speech(pcm16_chunk):
            self._consecutive_speech_frames = 0
            return False
        self._consecutive_speech_frames += 1
        return self._consecutive_speech_frames == self._min_frames

    def reset(self) -> None:
        self._consecutive_speech_frames = 0
