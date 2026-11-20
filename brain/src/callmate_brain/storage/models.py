"""Brain-owned tables, in the `brain` Postgres schema (docs/HANDOFF.md §3: pipeline never
reads or writes these directly, only via contracts/).
"""

from __future__ import annotations

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON

from ..memory.embeddings import EMBEDDING_DIM


class Base(DeclarativeBase):
    pass


class UserRow(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "brain"}

    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    first_name: Mapped[str] = mapped_column(String)
    pronouns: Mapped[str] = mapped_column(String, default="they/them")
    languages: Mapped[list[str]] = mapped_column(JSON, default=list)
    availability_text: Mapped[str] = mapped_column(String, default="")


class SettingsRow(Base):
    __tablename__ = "settings"
    __table_args__ = {"schema": "brain"}

    user_id: Mapped[str] = mapped_column(ForeignKey("brain.users.user_id"), primary_key=True)
    conciseness: Mapped[int] = mapped_column(Integer, default=3)
    empathy: Mapped[int] = mapped_column(Integer, default=3)
    formality: Mapped[str] = mapped_column(String, default="auto")
    never_share: Mapped[list[str]] = mapped_column(JSON, default=list)
    modes: Mapped[list[str]] = mapped_column(JSON, default=list)
    escalation_enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class ContactRow(Base):
    __tablename__ = "contacts"
    __table_args__ = {"schema": "brain"}

    contact_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("brain.users.user_id"), index=True)
    phone_number: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str | None] = mapped_column(String)
    relationship: Mapped[str] = mapped_column(String, default="service")
    blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)


class MemoryRow(Base):
    __tablename__ = "memories"
    __table_args__ = {"schema": "brain"}

    memory_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("brain.users.user_id"), index=True)
    caller_number: Mapped[str | None] = mapped_column(String, index=True)
    kind: Mapped[str] = mapped_column(String)  # "summary" | "contact_note" | "style_example"
    content: Mapped[str] = mapped_column(String)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))
    # timezone=True: writer.py inserts datetime.now(UTC) (aware); a naive column makes
    # asyncpg's encoder raise "can't subtract offset-naive and offset-aware datetimes".
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CallRow(Base):
    __tablename__ = "calls"
    __table_args__ = {"schema": "brain"}

    call_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("brain.users.user_id"), index=True)
    caller_number: Mapped[str] = mapped_column(String, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_s: Mapped[float] = mapped_column(Float)
    priority_level: Mapped[str] = mapped_column(String)
    score: Mapped[int] = mapped_column(Integer)
    intent: Mapped[str] = mapped_column(String)
    summary: Mapped[str] = mapped_column(String)
    callback_needed: Mapped[bool] = mapped_column(Boolean, default=False)
    callback_window: Mapped[str | None] = mapped_column(String)
    recording_url: Mapped[str | None] = mapped_column(String)
