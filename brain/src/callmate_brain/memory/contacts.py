"""Caller lookup + relationship tags (docs/HANDOFF.md §7.1.3). `routing.py` on the pipeline
side needs `call_context` to answer in < 150ms — keep its implementation to a single indexed
lookup by E.164 number, no joins that could regress that.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from callmate_contracts.rest import CallContextResponse


class ContactRepository(ABC):
    @abstractmethod
    async def call_context(self, user_id: str, caller_number: str) -> CallContextResponse: ...

    @abstractmethod
    async def import_contacts(self, user_id: str, contacts: list[dict[str, str]]) -> int:
        """Returns the number of contacts imported."""
