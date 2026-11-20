"""Builds the TwiML that connects an inbound call to our media WebSocket. Two modes
(docs/HANDOFF.md §6.1.12): `media_streams` (full control, built Week 2+) and
`conversation_relay` (Twilio does STT/TTS/interruptions, Week 1 baseline and failover).

`<Stream>`/`<ConversationRelay>` carry `<Parameter>` children so `media/stream_ws.py` gets
`user_id`/`caller_number`/`mode`/`caller_name` back in `start.customParameters` — without
these, every call arrives with an empty CallSession (no caller_number to notify about, no
user_id to look up settings for).
"""

from __future__ import annotations

from xml.sax.saxutils import escape


def _ws_base_url(public_base_url: str) -> str:
    return public_base_url.replace("http", "ws", 1)


def _parameter_tags(params: dict[str, str]) -> str:
    return "".join(
        f'<Parameter name="{escape(name)}" value="{escape(value)}" />'
        for name, value in params.items()
        if value
    )


def build_media_stream_twiml(
    call_id: str,
    *,
    public_base_url: str,
    user_id: str,
    caller_number: str,
    mode: str,
    caller_name: str | None = None,
    language_hint: str = "auto",
) -> str:
    url = escape(f"{_ws_base_url(public_base_url)}/media/{call_id}")
    params = _parameter_tags(
        {
            "user_id": user_id,
            "caller_number": caller_number,
            "mode": mode,
            "caller_name": caller_name or "",
            "language_hint": language_hint,
        }
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<Response><Connect><Stream url="{url}">{params}</Stream></Connect></Response>'
    )


def build_conversation_relay_twiml(
    call_id: str,
    *,
    public_base_url: str,
    user_id: str,
    caller_number: str,
    mode: str,
    caller_name: str | None = None,
    language_hint: str = "auto",
) -> str:
    url = escape(f"{_ws_base_url(public_base_url)}/relay/{call_id}")
    params = _parameter_tags(
        {
            "user_id": user_id,
            "caller_number": caller_number,
            "mode": mode,
            "caller_name": caller_name or "",
            "language_hint": language_hint,
        }
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<Response><Connect><ConversationRelay url="{url}">{params}</ConversationRelay>'
        "</Connect></Response>"
    )


def build_twiml_for_call(
    call_id: str,
    *,
    public_base_url: str,
    user_id: str,
    caller_number: str,
    mode: str,
    caller_name: str | None = None,
    language_hint: str = "auto",
    telephony_mode: str = "media_streams",
) -> str:
    builder = (
        build_conversation_relay_twiml
        if telephony_mode == "conversation_relay"
        else build_media_stream_twiml
    )
    return builder(
        call_id,
        public_base_url=public_base_url,
        user_id=user_id,
        caller_number=caller_number,
        mode=mode,
        caller_name=caller_name,
        language_hint=language_hint,
    )
