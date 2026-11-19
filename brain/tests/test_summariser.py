from typing import Any

import pytest
from callmate_brain.llm.base import LLMProvider, ReplyChunk
from callmate_brain.llm.mock import MockLLMProvider
from callmate_brain.reasoning.summariser import render_summarise_system_prompt, summarise_call


class _BrokenLLMProvider(LLMProvider):
    """Always returns JSON missing a required field, to exercise the retry+fallback path."""

    async def stream_reply(self, *, system_prompt: str, messages: list[dict[str, str]]):
        yield ReplyChunk(text="", is_final=True)

    async def classify(self, *, system_prompt, user_prompt, schema) -> dict[str, Any]:
        return {}

    async def summarise(self, *, system_prompt, user_prompt, schema) -> dict[str, Any]:
        return {"summary": "incomplete, missing required fields"}


@pytest.mark.asyncio
async def test_happy_path_returns_llm_result():
    result = await summarise_call(
        MockLLMProvider(), call_id="c1", seq=1, user_first_name="Asha", transcript="hi\nhello"
    )
    assert result.call_id == "c1"
    assert result.summary  # mock always returns a non-empty summary


@pytest.mark.asyncio
async def test_invalid_json_falls_back_to_rules_only():
    result = await summarise_call(
        _BrokenLLMProvider(), call_id="c1", seq=1, user_first_name="Asha", transcript="hi"
    )
    assert result.reason == "summariser_fallback"


def test_summarise_prompt_mentions_user_first_name():
    assert "Asha" in render_summarise_system_prompt("Asha")
