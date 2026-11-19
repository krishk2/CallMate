"""mu-law <-> PCM16 conversion. Uses `audioop-lts` (the maintained PyPI backport of stdlib
`audioop`, which is removed in Python 3.13+) so this keeps working across Python versions.
"""

from __future__ import annotations

import audioop

_SAMPLE_WIDTH = 2  # 16-bit PCM


def ulaw_to_pcm16(ulaw_bytes: bytes) -> bytes:
    return audioop.ulaw2lin(ulaw_bytes, _SAMPLE_WIDTH)


def pcm16_to_ulaw(pcm_bytes: bytes) -> bytes:
    return audioop.lin2ulaw(pcm_bytes, _SAMPLE_WIDTH)


def resample_pcm16(pcm_bytes: bytes, from_rate: int, to_rate: int) -> bytes:
    """Resample mono 16-bit PCM.
    TODO (docs/HANDOFF.md §1.2): swap to `soxr` for quality once a provider needs a rate other
    than 8kHz — audioop's linear resampler is a stopgap, fine for 8kHz telephony passthrough.
    """
    converted, _ = audioop.ratecv(pcm_bytes, _SAMPLE_WIDTH, 1, from_rate, to_rate, None)
    return converted
