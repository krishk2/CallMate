"""pgvector-backed long-term memory: past call summaries and style examples
(docs/HANDOFF.md §7.1.4). `reasoning`/`persona` code depends on `LongTermMemoryStore`, never
on SQLAlchemy or pgvector directly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievedMemory:
    content: str
    similarity: float


class LongTermMemoryStore(ABC):
    @abstractmethod
    async def add(
        self,
        user_id: str,
        content: str,
        embedding: list[float],
        *,
        kind: str = "summary",
        caller_number: str | None = None,
    ) -> str:
        """Returns the new memory_id."""

    @abstractmethod
    async def search(
        self,
        user_id: str,
        query_embedding: list[float],
        *,
        top_k: int,
        caller_number: str | None = None,
    ) -> list[RetrievedMemory]:
        """Cosine similarity search, filtered by user_id (and caller_number when given)."""

    @abstractmethod
    async def delete(self, user_id: str, memory_id: str) -> None: ...

    @abstractmethod
    async def delete_all(self, user_id: str) -> None: ...
