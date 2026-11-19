"""Spoken fillers used while waiting on a slow brain (docs/HANDOFF.md §5.4: first reply.delta
within 600ms, filler after that, hard fallback to take_message after 4s)."""

from __future__ import annotations

import random

_FILLERS = (
    "One moment.",
    "Mm-hmm, just a second.",
    "Let me check on that.",
)


def pick_filler() -> str:
    return random.choice(_FILLERS)
