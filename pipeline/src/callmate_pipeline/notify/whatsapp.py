"""Twilio WhatsApp notification channel — an alternative to Telegram
(docs/HANDOFF.md §6.1.11 names Telegram as primary, Twilio SMS/WhatsApp as the documented
fallback). Uses the Messages REST API directly with `whatsapp:` channel prefixes.

Requires the recipient to have joined the Twilio WhatsApp Sandbox (send the sandbox's join
code once from the destination number) or a verified WhatsApp Business sender — see
https://www.twilio.com/docs/whatsapp/sandbox. Outside an active 24h conversation window,
WhatsApp Business policy only allows pre-approved template messages, not this free-form body.
"""

from __future__ import annotations

import httpx
import structlog
from callmate_contracts.messages import SessionResult

from ..config import settings
from .telegram import format_summary_message

logger = structlog.get_logger(__name__)


async def send_whatsapp_summary(
    *, caller_number: str, caller_name: str | None, result: SessionResult, duration_s: float
) -> None:
    if not settings.whatsapp_to or not settings.twilio_account_sid:
        logger.warning("whatsapp_not_configured", skipping="notification")
        return

    text = format_summary_message(
        caller_number=caller_number, caller_name=caller_name, result=result, duration_s=duration_s
    )
    url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Messages.json"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            url,
            auth=(settings.twilio_account_sid, settings.twilio_auth_token),
            data={"From": settings.whatsapp_from, "To": settings.whatsapp_to, "Body": text},
        )
        response.raise_for_status()
