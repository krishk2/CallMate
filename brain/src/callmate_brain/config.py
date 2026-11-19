"""All brain configuration. Never hardcode a provider choice, model ID, or priority weight
elsewhere — add a field here and read it from there (docs/HANDOFF.md §13).
"""

from __future__ import annotations

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # shared
    service_token: str = "change-me"
    database_url: str = "postgresql+asyncpg://callmate:callmate@localhost:5432/callmate"
    log_level: str = "INFO"

    # llm
    llm_provider: Literal["anthropic", "gemini", "mock"] = "mock"
    anthropic_api_key: str = ""
    reply_model: str = "claude-haiku-5-5"
    summary_model: str = "claude-sonnet-5-5"
    google_api_key: str = ""
    embedding_provider: Literal["gemini", "local"] = "local"

    # retention
    transcript_retention_days: int = 30

    # turn engine
    reply_first_token_target_s: float = 0.6
    prompt_token_budget: int = 2500
    retrieval_top_k: int = 5

    # priority weights (tunable from eval results, docs/HANDOFF.md §7.1/§10 week 6-7)
    priority_relationship_weights: dict[str, int] = {
        "family": 30,
        "work": 15,
        "friend": 20,
        "service": 5,
        "blocked": 0,
    }
    priority_repeat_call_bonus: int = 15
    priority_llm_urgency_weight: int = 40
    priority_spam_penalty: int = 25
    priority_urgent_threshold: int = 80
    priority_important_threshold: int = 55
    priority_normal_threshold: int = 30


settings = Settings()
