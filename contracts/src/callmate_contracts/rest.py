"""REST request/response models for the brain's user-facing API (docs/HANDOFF.md §5.3)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from .enums import Intent, Priority


class CallContextResponse(BaseModel):
    """GET /v1/users/{id}/call-context?caller=+91... — pipeline routing.py, must answer < 150ms."""

    known_contact: bool
    contact_name: str | None = None
    relationship: Literal["family", "work", "friend", "service", "blocked"] | None = None
    tags: list[str] = Field(default_factory=list)
    blocked: bool = False


class ToneSettings(BaseModel):
    conciseness: int = Field(default=3, ge=1, le=5)
    empathy: int = Field(default=3, ge=1, le=5)
    formality: Literal["auto", "casual", "formal"] = "auto"
    languages: list[str] = Field(default_factory=lambda: ["en-IN"])
    code_mixing: bool = True


class UserSettings(BaseModel):
    """GET/PUT /v1/users/{id}/settings"""

    tone: ToneSettings = Field(default_factory=ToneSettings)
    never_share: list[str] = Field(default_factory=list)
    modes: list[Literal["away", "screen_unknown"]] = Field(default_factory=list)
    escalation_enabled: bool = True


class CallSummaryItem(BaseModel):
    """One row of GET /v1/users/{id}/calls"""

    call_id: str
    caller_number: str
    caller_name: str | None = None
    started_at: datetime
    duration_s: float
    priority_level: Priority
    intent: Intent
    summary: str


class CallDetail(CallSummaryItem):
    """GET /v1/calls/{call_id}"""

    score: int = Field(ge=0, le=100)
    callback_needed: bool
    callback_window: str | None = None
    recording_url: str | None = None


class MemoryItem(BaseModel):
    memory_id: str
    kind: Literal["summary", "contact_note", "style_example"]
    content: str
    created_at: datetime
    caller_number: str | None = None
