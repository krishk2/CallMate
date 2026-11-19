"""Last check before text leaves the brain (docs/HANDOFF.md §7.1.6, §8): every reply sentence
passes through here before becoming a reply.delta. Independent of the prompt-level guardrail
directive — this still catches a leak if the model ignores that directive.
"""

from __future__ import annotations

import re

_SENSITIVE_PATTERNS = (
    re.compile(r"\b\d{4,8}\b"),  # looks like an OTP/PIN being read back
    re.compile(r"\b(?:\d[ -]?){13,19}\b"),  # card-number-shaped
)


class OutputBlocked(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def check_reply_sentence(sentence: str) -> str:
    """Raises OutputBlocked if `sentence` looks like it leaks something on the never-share
    list. Callers should drop the fragment or substitute a safe one, never speak it."""
    for pattern in _SENSITIVE_PATTERNS:
        if pattern.search(sentence):
            raise OutputBlocked(f"sentence matched sensitive pattern: {pattern.pattern}")
    return sentence
