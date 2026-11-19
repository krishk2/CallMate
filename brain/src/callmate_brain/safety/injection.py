"""Caller prompt-injection detection (docs/HANDOFF.md §8). Caller speech is always fenced as
data (reasoning/prompt_builder.py's `fence_caller_text`) — this is the extra check for when
the caller tries to talk the model out of treating it that way.
"""

from __future__ import annotations

import re

_INJECTION_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"ignore (your|all|previous) instructions",
        r"you are now",
        r"system prompt",
        r"disregard (the|your) (rules|guidelines|instructions)",
        r"new instructions",
        r"reveal (your|the) (prompt|instructions)",
        r"pretend (you|to)\b",
    )
]

SAFE_REFUSAL_REPLY = (
    "I can't do that, but I can take a message for them. What would you like me to pass on?"
)


def is_injection_attempt(caller_text: str) -> bool:
    return any(pattern.search(caller_text) for pattern in _INJECTION_PATTERNS)
