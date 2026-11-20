"""Fires whichever notification channel(s) are configured after a call ends. A channel with
no credentials set is silently skipped (each sender already logs+no-ops on its own, per
docs/HANDOFF.md §9's "never leave the caller in silence" spirit extended to "never crash the
call because a notification failed") — a failing channel must never take the call session
down with it, so each is isolated in its own try/except here too.
"""

from __future__ import annotations

import structlog
from callmate_contracts.messages import SessionResult

from ..config import settings
from .telegram import send_telegram_summary
from .whatsapp import send_whatsapp_summary

logger = structlog.get_logger(__name__)


async def send_call_summary_notifications(
    *, caller_number: str, caller_name: str | None, result: SessionResult, duration_s: float
) -> None:
    if settings.telegram_bot_token and settings.telegram_chat_id:
        try:
            await send_telegram_summary(
                caller_number=caller_number,
                caller_name=caller_name,
                result=result,
                duration_s=duration_s,
            )
        except Exception:
            logger.warning("telegram_notify_failed", exc_info=True)

    if settings.whatsapp_to:
        try:
            await send_whatsapp_summary(
                caller_number=caller_number,
                caller_name=caller_name,
                result=result,
                duration_s=duration_s,
            )
        except Exception:
            logger.warning("whatsapp_notify_failed", exc_info=True)
