"""Anthropic provider: Claude Haiku for streaming replies, Claude Sonnet for summaries
(docs/HANDOFF.md §1.3). Needs a pay-as-you-go API key from the Claude Console — NOT the
Claude Code subscription (docs/HANDOFF.md §1.4).
TODO (Week 2, docs/HANDOFF.md §10): implement against the `anthropic` Python SDK, streaming
for `stream_reply`, and structured/tool-forced JSON output for `classify`/`summarise`. Add the
dependency to brain/pyproject.toml when this is implemented.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from ..config import settings
from .base import LLMProvider, ReplyChunk


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or settings.anthropic_api_key

    async def stream_reply(
        self, *, system_prompt: str, messages: list[dict[str, str]]
    ) -> AsyncIterator[ReplyChunk]:
        raise NotImplementedError("AnthropicProvider: see TODO at top of module")
        yield  # pragma: no cover

    async def classify(
        self, *, system_prompt: str, user_prompt: str, schema: dict[str, Any]
    ) -> dict[str, Any]:
        raise NotImplementedError

    async def summarise(
        self, *, system_prompt: str, user_prompt: str, schema: dict[str, Any]
    ) -> dict[str, Any]:
        raise NotImplementedError
