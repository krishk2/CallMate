"""Stable user facts + settings (docs/HANDOFF.md §7.1). `reasoning`/`persona` code depends on
`ProfileRepository`, never on a concrete storage backend.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from callmate_contracts.rest import UserSettings


@dataclass(frozen=True)
class UserProfile:
    user_id: str
    first_name: str
    pronouns: str
    languages: list[str]
    availability_text: str
    settings: UserSettings


class ProfileRepository(ABC):
    @abstractmethod
    async def get(self, user_id: str) -> UserProfile: ...

    @abstractmethod
    async def update_settings(self, user_id: str, settings: UserSettings) -> None: ...
