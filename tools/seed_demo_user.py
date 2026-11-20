#!/usr/bin/env python
"""Creates the demo user + settings row so both services have something to run against
locally (docs/HANDOFF.md §9.1) — without this, every memory write hits a foreign-key
violation on `memories.user_id`, since nothing actually created "demo" in `brain.users`.

Idempotent: safe to run multiple times, only inserts if the row doesn't already exist.
"""

from __future__ import annotations

import asyncio

from callmate_brain.config import settings
from callmate_brain.storage import create_schema_and_tables, get_session
from callmate_brain.storage.models import SettingsRow, UserRow

DEMO_USER_ID = "demo"


async def seed() -> None:
    await create_schema_and_tables()
    async with get_session() as db:
        user = await db.get(UserRow, DEMO_USER_ID)
        if user is None:
            db.add(
                UserRow(
                    user_id=DEMO_USER_ID,
                    first_name="Demo",
                    pronouns="they/them",
                    languages=["en-IN"],
                    availability_text="away",
                )
            )
            print(f"Created user {DEMO_USER_ID!r}")
        else:
            print(f"User {DEMO_USER_ID!r} already exists, skipping")

        existing_settings = await db.get(SettingsRow, DEMO_USER_ID)
        if existing_settings is None:
            db.add(
                SettingsRow(
                    user_id=DEMO_USER_ID,
                    conciseness=3,
                    empathy=3,
                    formality="auto",
                    never_share=[],
                    modes=["away", "screen_unknown"],
                    escalation_enabled=True,
                )
            )
            print(f"Created settings for {DEMO_USER_ID!r}")
        else:
            print(f"Settings for {DEMO_USER_ID!r} already exist, skipping")

        await db.commit()


def main() -> None:
    print(f"Seeding against: {settings.database_url}")
    asyncio.run(seed())


if __name__ == "__main__":
    main()
