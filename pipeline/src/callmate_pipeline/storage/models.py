"""Pipeline-owned tables, in the `pipeline` Postgres schema (docs/HANDOFF.md §3: "Database
ownership" — brain never reads or writes these directly, only via contracts/).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Float, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class CallRow(Base):
    __tablename__ = "calls"
    __table_args__ = {"schema": "pipeline"}

    call_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    caller_number: Mapped[str] = mapped_column(String, index=True)
    started_at: Mapped[datetime]
    ended_at: Mapped[datetime | None]
    duration_s: Mapped[float | None] = mapped_column(Float)
    end_reason: Mapped[str | None] = mapped_column(String)
    recording_url: Mapped[str | None] = mapped_column(String)

    turns: Mapped[list[TurnRow]] = relationship(back_populates="call")


class TurnRow(Base):
    __tablename__ = "turns"
    __table_args__ = {"schema": "pipeline"}

    turn_id: Mapped[str] = mapped_column(String, primary_key=True)
    call_id: Mapped[str] = mapped_column(ForeignKey("pipeline.calls.call_id"), index=True)
    caller_text: Mapped[str] = mapped_column(String)
    agent_text: Mapped[str | None] = mapped_column(String)
    started_at: Mapped[datetime]

    call: Mapped[CallRow] = relationship(back_populates="turns")


class LatencySpanRow(Base):
    """Persisted docs/HANDOFF.md §6.1.13 spans, read by scripts/latency_report.py."""

    __tablename__ = "latency_spans"
    __table_args__ = {"schema": "pipeline"}

    turn_id: Mapped[str] = mapped_column(ForeignKey("pipeline.turns.turn_id"), primary_key=True)
    call_id: Mapped[str] = mapped_column(String, index=True)
    marks_ms_since_epoch: Mapped[dict[str, float]] = mapped_column(JSON)
