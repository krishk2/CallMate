"""Builds the TwiML that connects an inbound call to our media WebSocket. Two modes
(docs/HANDOFF.md §6.1.12): `media_streams` (full control, built Week 2+) and
`conversation_relay` (Twilio does STT/TTS/interruptions, Week 1 baseline and failover).
"""

from __future__ import annotations

from xml.sax.saxutils import escape

from ..config import settings


def _ws_base_url() -> str:
    return settings.public_base_url.replace("http", "ws", 1)


def build_media_stream_twiml(call_id: str) -> str:
    url = escape(f"{_ws_base_url()}/media/{call_id}")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f"<Response><Connect><Stream url=\"{url}\" /></Connect></Response>"
    )


def build_conversation_relay_twiml(call_id: str) -> str:
    url = escape(f"{_ws_base_url()}/relay/{call_id}")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<Response><Connect><ConversationRelay url="{url}" /></Connect></Response>'
    )


def build_twiml_for_call(call_id: str) -> str:
    if settings.telephony_mode == "conversation_relay":
        return build_conversation_relay_twiml(call_id)
    return build_media_stream_twiml(call_id)
