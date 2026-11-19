"""Builds a short style card once from the user's consented message samples
(docs/HANDOFF.md §7.1.2) — greeting habits, sentence length, emoji/slang, language mixing.
Do not fine-tune; this is a prompt-time summary, generated once and cached.
"""

from __future__ import annotations

from ..llm.base import LLMProvider
from ..reasoning.prompt_templates import env


def render_style_profile_prompt(consented_samples: list[str]) -> str:
    return env.get_template("style_profile.j2").render(samples=consented_samples).strip()


async def build_style_card(llm: LLMProvider, *, consented_samples: list[str]) -> str:
    """TODO (Week 3, docs/HANDOFF.md §7.1.2): wire to Sonnet once anthropic_provider.py
    exists. `LLMProvider.summarise()` takes a JSON schema, so either add a single-field
    `{"style_card": str}` schema here, or add a plain-text completion method to the
    protocol — decide once there's a real provider to implement it against.
    """
    raise NotImplementedError("build_style_card: see TODO above")
