"""Twilio SMS/WhatsApp fallback notification, used if Telegram delivery fails.
TODO (docs/HANDOFF.md §1.2): implement against the Twilio REST API (`twilio` SDK or raw
httpx + basic auth) once Telegram-only is proven insufficient in testing.
"""

from __future__ import annotations

from callmate_contracts.messages import SessionResult


async def send_sms_summary(
    *, caller_number: str, caller_name: str | None, result: SessionResult, duration_s: float
) -> None:
    raise NotImplementedError("send_sms_summary: see TODO at top of module")
