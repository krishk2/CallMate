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
    # Guards CallSession.close()'s wait for brain's session.result (brain's own retry-on-
    # invalid-JSON summariser can take two full LLM round trips back to back, ~20-30s in the
    # worst case) — without this, a slow/unreachable brain hangs the whole call-close path
    # forever, and send_call_summary_notifications() (the Telegram/WhatsApp ping) never runs.
    # Measured live against the actual Render free-tier deployment: a fully slept brain
    # service took ~28.5s to answer its first request after waking. brain_end_session_timeout_s
    # must stay comfortably above brain_connect_max_attempts * brain_connect_retry_delay_s, or
    # this timeout cuts the connection off before the retries below even get a chance to work.
    brain_end_session_timeout_s: float = 45.0
    # Retries a failed brain WebSocket handshake rather than crashing the call outright — a
    # sleeping free-tier deployment returning a 502 while it cold-starts is transient, not a
    # real outage. 6 attempts * 5s (~30s budget) covers the measured cold-start time above;
    # scripts/warm_render.ps1 is the actual fix for a testing session (keeps brain from
    # sleeping at all) — this is just the safety net for whenever that isn't running.
    brain_connect_max_attempts: int = 6
    brain_connect_retry_delay_s: float = 5.0

    # notifications
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    whatsapp_from: str = "whatsapp:+14155238886"  # Twilio's shared WhatsApp Sandbox number
    whatsapp_to: str = ""

    # turn-taking / barge-in tuning
    silence_prompt_s: float = 6.0
    goodbye_timeout_s: float = 12.0
    barge_in_min_speech_ms: float = 250.0

    # retention
    audio_retention_days: int = 7


settings = Settings()
