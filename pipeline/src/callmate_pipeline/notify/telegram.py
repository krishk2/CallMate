"""Sends the session.result to the user on Telegram within 15s of hang-up
(docs/HANDOFF.md §6.1.11). Primary notification channel.
"""

from __future__ import annotations

import httpx
import structlog
from callmate_contracts.enums import Priority
from callmate_contracts.messages import SessionResult

from ..config import settings

logger = structlog.get_logger(__name__)

_PRIORITY_EMOJI = {
    Priority.URGENT: "\U0001f534",  # red circle
    Priority.IMPORTANT: "\U0001f7e0",  # orange circle
    Priority.NORMAL: "\U0001f7e1",  # yellow circle
    Priority.LOW: "⚪",  # white circle
}


def format_summary_message(
    *, caller_number: str, caller_name: str | None, result: SessionResult, duration_s: float
) -> str:
    emoji = _PRIORITY_EMOJI[result.priority_level]
    who = caller_name or caller_number
    minutes, seconds = divmod(int(duration_s), 60)
    return (
        f"{emoji} {result.priority_level.value.upper()} · {who} · {result.summary} · "
        f"{minutes}m {seconds}s · tel:{caller_number}"
    )


async def send_telegram_summary(
    *, caller_number: str, caller_name: str | None, result: SessionResult, duration_s: float
) -> None:
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        logger.warning("telegram_not_configured", skipping="notification")
        return

    text = format_summary_message(
        caller_number=caller_number, caller_name=caller_name, result=result, duration_s=duration_s
    )
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            url, json={"chat_id": settings.telegram_chat_id, "text": text}
        )
        response.raise_for_status()
