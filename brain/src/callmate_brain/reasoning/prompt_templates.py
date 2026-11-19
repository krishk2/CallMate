"""Shared Jinja2 environment for `brain/prompts/*.j2` — the versioned prompt templates
(docs/HANDOFF.md §1.3). One environment, reused by prompt_builder.py, intent.py,
summariser.py and persona/style_profile.py, so template loading/caching isn't duplicated.
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

_PROMPTS_DIR = Path(__file__).resolve().parents[3] / "prompts"

env = Environment(
    loader=FileSystemLoader(str(_PROMPTS_DIR)),
    autoescape=select_autoescape(enabled_extensions=()),
    trim_blocks=True,
    lstrip_blocks=True,
)
