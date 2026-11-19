"""LLM provider protocol. Every provider (Anthropic, Gemini, mock) implements this and only
this — reasoning/turn_engine.py, intent.py and summariser.py depend on `LLMProvider`, never
on a concrete SDK client.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ReplyChunk:
    text: str
    is_final: bool


class LLMProvider(ABC):
    @abstractmethod
    def stream_reply(
        self, *, system_prompt: str, messages: list[dict[str, str]]
    ) -> AsyncIterator[ReplyChunk]:
        """Stream a conversational reply (the live, latency-critical path)."""

    @abstractmethod
    async def classify(
        self, *, system_prompt: str, user_prompt: str, schema: dict[str, Any]
    ) -> dict[str, Any]:
        """Return strict JSON matching `schema` — used for intent classification."""

    @abstractmethod
    async def summarise(
        self, *, system_prompt: str, user_prompt: str, schema: dict[str, Any]
    ) -> dict[str, Any]:
        """Return strict JSON matching `schema` — used for the post-call session.result."""
