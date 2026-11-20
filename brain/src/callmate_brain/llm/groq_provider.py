"""Groq: fast inference for the latency-critical live reply + intent classification
(docs/HANDOFF.md §1.3's former Haiku role). OpenAI-compatible API.
"""

from __future__ import annotations

from ..config import settings
from .openai_compatible import OpenAICompatibleProvider


class GroqProvider(OpenAICompatibleProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        super().__init__(
            api_key=api_key or settings.groq_api_key,
            base_url=settings.groq_base_url,
            model=model or settings.reply_model,
        )
