"""Tone sliders -> explicit prompt directives (docs/HANDOFF.md §7.1). Pure function, no I/O,
so it's trivially unit-testable — the policy logic that's easy to get subtly wrong lives here,
not buried inside prompt string concatenation elsewhere.
"""

from __future__ import annotations

from callmate_contracts.rest import ToneSettings

_CONCISENESS_DIRECTIVES = {
    1: "Reply in one short sentence, no more.",
    2: "Keep replies to one or two short sentences.",
    3: "Keep replies brief: one to two sentences.",
    4: "You may give a fuller explanation in two to three sentences if needed.",
    5: "Give a complete, helpful explanation, but still speak naturally — no lists.",
}

_EMPATHY_DIRECTIVES = {
    1: "Be neutral and efficient; don't comment on the caller's emotional state.",
    2: "Stay mostly neutral; a brief acknowledgement is fine if clearly warranted.",
    3: "If the caller sounds upset, briefly acknowledge it before answering.",
    4: "If the caller sounds worried or upset, acknowledge it warmly before anything else.",
    5: (
        "If the caller sounds worried or upset, acknowledge it in a few words before "
        "anything else, with warmth."
    ),
}


def build_tone_directives(
    tone: ToneSettings, *, caller_is_known: bool, caller_is_elder: bool = False
) -> list[str]:
    directives = [_CONCISENESS_DIRECTIVES[tone.conciseness], _EMPATHY_DIRECTIVES[tone.empathy]]

    formal_by_default = not caller_is_known or caller_is_elder
    if tone.formality == "formal" or (tone.formality == "auto" and formal_by_default):
        directives.append("Speak formally and respectfully.")
    elif tone.formality == "casual":
        directives.append("Speak casually, like talking to a friend.")

    if tone.code_mixing and len(tone.languages) > 1:
        directives.append(
            f"The user is comfortable code-mixing between {', '.join(tone.languages)}; "
            "match the caller's language choice naturally."
        )
    return directives
