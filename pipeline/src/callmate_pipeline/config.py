"""All pipeline configuration. Never hardcode a provider choice, model ID, or latency
threshold elsewhere — add a field here and read it from there (docs/HANDOFF.md §13).
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

    # telephony
    telephony_mode: Literal["media_streams", "conversation_relay"] = "media_streams"
    public_base_url: str = "http://localhost:8000"
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_number: str = ""
    # Single-tenant demo: one Twilio number maps to one CallMate user. A number -> user_id
    # lookup table is a Phase-2 multi-tenancy concern, not needed for the demo scope.
    demo_user_id: str = "demo"
    brain_rest_base_url: str = "http://localhost:8001"
    call_context_timeout_s: float = 0.5

    # stt / tts
    stt_provider: Literal["deepgram_flux", "deepgram_nova", "google", "mock"] = "mock"
    deepgram_api_key: str = ""
    google_application_credentials: str = ""
    tts_provider: Literal["elevenlabs", "google", "mock"] = "mock"
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""

    # brain client
    brain_mode: Literal["remote", "echo"] = "echo"
    brain_ws_url: str = "ws://localhost:8001/v1/calls"
    brain_first_token_timeout_s: float = 0.6
    brain_fallback_timeout_s: float = 4.0

    # notifications
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # turn-taking / barge-in tuning
    silence_prompt_s: float = 6.0
    goodbye_timeout_s: float = 12.0
    barge_in_min_speech_ms: float = 250.0

    # retention
    audio_retention_days: int = 7


settings = Settings()
