"""Per-utterance orchestration (docs/HANDOFF.md §7.1.6): builds the prompt, streams the LLM,
runs every completed sentence through the output filter before it's allowed to leave as a
reply.delta, and finishes with reply.done.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable

from callmate_contracts.enums import Action, Language
from callmate_contracts.messages import ReplyDelta, ReplyDone

from ..llm.base import LLMProvider
from ..safety.output_filter import OutputBlocked, check_reply_sentence
from .prompt_builder import build_turn_messages


async def generate_reply(
    *,
    llm: LLMProvider,
    system_prompt: str,
    retrieved_memories: list[str],
    recent_turns: list[tuple[str, str]],
    caller_text: str,
    call_id: str,
    turn_id: str,
    next_seq: Callable[[], int],
    language: Language,
    action: Action = Action.CONTINUE,
) -> AsyncIterator[ReplyDelta | ReplyDone]:
    messages = build_turn_messages(
        retrieved_memories=retrieved_memories, recent_turns=recent_turns, caller_text=caller_text
    )
    full_text = ""
    async for chunk in llm.stream_reply(system_prompt=system_prompt, messages=messages):
        if chunk.is_final:
            break
        try:
            safe_text = check_reply_sentence(chunk.text)
        except OutputBlocked:
            continue  # drop the unsafe fragment rather than speak it
        full_text += safe_text
        yield ReplyDelta(call_id=call_id, seq=next_seq(), turn_id=turn_id, text=safe_text)

    yield ReplyDone(
        call_id=call_id,
        seq=next_seq(),
        turn_id=turn_id,
        full_text=full_text,
        action=action,
        language=language,
    )
