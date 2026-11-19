"""Gemini fallback behind the same LLMProvider interface as Anthropic (docs/HANDOFF.md §1.3).
TODO: implement against `google-genai` if/when the Anthropic fallback is needed. Add the
dependency to brain/pyproject.toml when this is implemented.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from ..config import settings
from .base import LLMProvider, ReplyChunk


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or settings.google_api_key

    async def stream_reply(
        self, *, system_prompt: str, messages: list[dict[str, str]]
    ) -> AsyncIterator[ReplyChunk]:
        raise NotImplementedError("GeminiProvider: see TODO at top of module")
        yield  # pragma: no cover

    async def classify(
        self, *, system_prompt: str, user_prompt: str, schema: dict[str, Any]
    ) -> dict[str, Any]:
        raise NotImplementedError

    async def summarise(
        self, *, system_prompt: str, user_prompt: str, schema: dict[str, Any]
    ) -> dict[str, Any]:
        raise NotImplementedError
