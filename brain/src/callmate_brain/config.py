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

    # repeat-call tracking (docs/HANDOFF.md §7.1.8/demo scenario #7: 3 calls in 10 min bumps
    # priority). Empty = disabled, falls back to always-zero rather than breaking when Redis
    # isn't set up — e.g. Upstash's free tier works fine for this on the deployed app.
    redis_url: str = ""
    repeat_call_window_s: int = 600

    # application-level encryption at rest for stored call content (MemoryRow.content,
    # CallRow.summary). Empty = disabled (store/read as plaintext) — losing this key after
    # it's been used means everything encrypted with it becomes permanently unreadable, so
    # it's opt-in rather than defaulted on.
    encryption_key: str = ""

    # llm — two roles, not one interchangeable backend (docs/HANDOFF.md §1.3's original
    # Haiku/Sonnet split): Groq for the latency-critical live reply + intent classification,
    # NVIDIA NIM for the not-latency-critical post-call summary. Both are OpenAI-compatible.
    reply_llm_provider: Literal["groq", "mock"] = "mock"
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    reply_model: str = "openai/gpt-oss-20b"

    summary_llm_provider: Literal["nvidia", "mock"] = "mock"
    nvidia_api_key: str = ""
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    summary_model: str = "nvidia/nemotron-3.5-lightning-30b-a3b"

    embedding_provider: Literal["nvidia", "local"] = "local"
    nvidia_embedding_model: str = "nvidia/nemotron-3-embed-1b"

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
