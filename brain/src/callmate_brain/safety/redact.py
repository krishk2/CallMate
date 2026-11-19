"""Regex PII redaction before anything is stored (docs/HANDOFF.md §7.1.4, §8). Deepgram's
upstream `redact` option handles some of this before it ever reaches us; this is the backstop
for whatever reaches storage anyway (summaries, memory writer).

TODO: these patterns are intentionally broad and will over-redact (e.g. a 4-8 digit quantity
or year). Microsoft Presidio is the documented fallback (docs/HANDOFF.md §1.3) if/when
precision matters more than always erring toward redacting.
"""

from __future__ import annotations

import re

# Order matters: longer/more-specific digit runs must be redacted before shorter patterns
# get a chance to partially match a prefix of them (e.g. a 16-digit card number's first 12
# digits otherwise look like an Aadhaar number to that narrower pattern).
_PATTERNS: dict[str, re.Pattern[str]] = {
    "card": re.compile(r"\b(?:\d[ -]?){13,19}\b"),
    "aadhaar": re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"),
    "phone": re.compile(r"\b(?:\+?91[-\s]?)?[6-9]\d{9}\b"),
    "otp_or_pin": re.compile(r"\b\d{4,8}\b"),
}


def redact(text: str) -> str:
    redacted = text
    for label, pattern in _PATTERNS.items():
        redacted = pattern.sub(f"[REDACTED_{label.upper()}]", redacted)
    return redacted
