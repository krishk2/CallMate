"""Escalation: puts the caller on hold, dials the user's real number with a whispered
context line, and bridges them in (docs/HANDOFF.md §6.1.8). Builds TwiML only — the actual
<Dial> call to Twilio's REST API happens where the call's live CallSid is held
(telephony/twilio_webhooks.py), since redirecting an in-progress call needs that CallSid.
"""

from __future__ import annotations

from xml.sax.saxutils import escape

ESCALATION_HOLD_MESSAGE = "One moment, I'll see if they're available to take this directly."
ESCALATION_NO_ANSWER_TIMEOUT_S = 20


def build_whisper_twiml(whisper_text: str) -> str:
    """TwiML played to the *user* (not the caller) before the bridge connects, so they know
    why their phone is ringing and can press 1 to accept."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f"<Response><Say>{escape(whisper_text)} Press 1 to take this call.</Say>"
        '<Gather numDigits="1" timeout="10" /></Response>'
    )


def build_hold_twiml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f"<Response><Say>{escape(ESCALATION_HOLD_MESSAGE)}</Say><Pause length=\"20\" /></Response>"
    )
