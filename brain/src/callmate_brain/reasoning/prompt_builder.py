"""Assembles the system prompt + turn messages (docs/HANDOFF.md §7.1.5): identity +
disclosure + tone + style + never-share from `prompts/system_reply.j2`, then retrieved
memories (fenced as data, not instructions — AGENTS.md), few-shot examples, recent turns,
caller text.
"""

from __future__ import annotations

from .prompt_templates import env


def build_system_prompt(
    *,
    user_first_name: str,
    tone_directives: list[str],
    guardrail_directive: str,
    style_card: str = "",
) -> str:
    template = env.get_template("system_reply.j2")
    return template.render(
        user_first_name=user_first_name,
        tone_directives=tone_directives,
        guardrail_directive=guardrail_directive,
        style_card=style_card,
    ).strip()


def fence_caller_text(caller_text: str) -> str:
    return f"<caller_said>{caller_text}</caller_said>"


def fence_memory(memory_text: str) -> str:
    return f"<retrieved_memory>{memory_text}</retrieved_memory>"


def build_turn_messages(
    *, retrieved_memories: list[str], recent_turns: list[tuple[str, str]], caller_text: str
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    if retrieved_memories:
        memory_block = "\n".join(fence_memory(memory) for memory in retrieved_memories)
        messages.append({"role": "user", "content": memory_block})
    for role, text in recent_turns:
        messages.append({"role": role, "content": text})
    messages.append({"role": "user", "content": fence_caller_text(caller_text)})
    return messages
