"""SQLAlchemy-backed implementations of the memory protocols (profile.py, contacts.py,
longterm.py). Nothing outside `storage/` should import SQLAlchemy directly — everything else
depends on the protocols those modules define.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from callmate_contracts.rest import CallContextResponse, UserSettings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..memory.contacts import ContactRepository
from ..memory.longterm import LongTermMemoryStore, RetrievedMemory
from ..memory.profile import ProfileRepository, UserProfile
from .models import ContactRow, MemoryRow, SettingsRow, UserRow


class SqlProfileRepository(ProfileRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_id: str) -> UserProfile:
        user = await self._session.get(UserRow, user_id)
        if user is None:
            raise LookupError(f"no such user: {user_id}")
        settings_row = await self._session.get(SettingsRow, user_id)
        settings = (
            UserSettings(
                tone={
                    "conciseness": settings_row.conciseness,
                    "empathy": settings_row.empathy,
                    "formality": settings_row.formality,
                    "languages": user.languages,
                },
                never_share=settings_row.never_share,
                modes=settings_row.modes,
                escalation_enabled=settings_row.escalation_enabled,
            )
            if settings_row is not None
            else UserSettings()
        )
        return UserProfile(
            user_id=user.user_id,
            first_name=user.first_name,
            pronouns=user.pronouns,
            languages=user.languages,
            availability_text=user.availability_text,
            settings=settings,
        )

    async def update_settings(self, user_id: str, settings: UserSettings) -> None:
        row = await self._session.get(SettingsRow, user_id)
        if row is None:
            row = SettingsRow(user_id=user_id)
            self._session.add(row)
        row.conciseness = settings.tone.conciseness
        row.empathy = settings.tone.empathy
        row.formality = settings.tone.formality
        row.never_share = settings.never_share
        row.modes = settings.modes
        row.escalation_enabled = settings.escalation_enabled
        await self._session.commit()


class SqlContactRepository(ContactRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def call_context(self, user_id: str, caller_number: str) -> CallContextResponse:
        stmt = select(ContactRow).where(
            ContactRow.user_id == user_id, ContactRow.phone_number == caller_number
        )
        contact = (await self._session.execute(stmt)).scalar_one_or_none()
        if contact is None:
            return CallContextResponse(known_contact=False)
        return CallContextResponse(
            known_contact=True,
            contact_name=contact.name,
            relationship=contact.relationship,
            tags=contact.tags,
            blocked=contact.blocked,
        )

    async def import_contacts(self, user_id: str, contacts: list[dict[str, str]]) -> int:
        count = 0
        for entry in contacts:
            self._session.add(
                ContactRow(
                    contact_id=str(uuid.uuid4()),
                    user_id=user_id,
                    phone_number=entry["phone_number"],
                    name=entry.get("name"),
                    relationship=entry.get("relationship", "service"),
                )
            )
            count += 1
        await self._session.commit()
        return count


class SqlLongTermMemoryStore(LongTermMemoryStore):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(
        self,
        user_id: str,
        content: str,
        embedding: list[float],
        *,
        kind: str = "summary",
        caller_number: str | None = None,
    ) -> str:
        memory_id = str(uuid.uuid4())
        self._session.add(
            MemoryRow(
                memory_id=memory_id,
                user_id=user_id,
                caller_number=caller_number,
                kind=kind,
                content=content,
                embedding=embedding,
                created_at=datetime.now(UTC),
            )
        )
        await self._session.commit()
        return memory_id

    async def search(
        self,
        user_id: str,
        query_embedding: list[float],
        *,
        top_k: int,
        caller_number: str | None = None,
    ) -> list[RetrievedMemory]:
        distance = MemoryRow.embedding.cosine_distance(query_embedding).label("distance")
        stmt = select(MemoryRow, distance).where(MemoryRow.user_id == user_id)
        if caller_number is not None:
            stmt = stmt.where(MemoryRow.caller_number == caller_number)
        stmt = stmt.order_by(distance).limit(top_k)
        rows = (await self._session.execute(stmt)).all()
        return [RetrievedMemory(content=row[0].content, similarity=1 - row[1]) for row in rows]

    async def delete(self, user_id: str, memory_id: str) -> None:
        row = await self._session.get(MemoryRow, memory_id)
        if row is not None and row.user_id == user_id:
            await self._session.delete(row)
            await self._session.commit()

    async def delete_all(self, user_id: str) -> None:
        stmt = select(MemoryRow).where(MemoryRow.user_id == user_id)
        rows = (await self._session.execute(stmt)).scalars().all()
        for row in rows:
            await self._session.delete(row)
        await self._session.commit()
