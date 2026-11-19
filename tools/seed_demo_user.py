#!/usr/bin/env python
"""Creates a demo user, contacts, style samples, and tone settings so both services have
something to run against locally (docs/HANDOFF.md §9.1).

Owned by Antigravity (ANTIGRAVITY_HANDOFF.md §1.1). Should insert directly via
`callmate_brain.storage` (UserRow/SettingsRow/ContactRow) rather than going through the REST
API, since this runs before the brain service is necessarily up.
"""

from __future__ import annotations


def main() -> None:
    raise NotImplementedError("seed_demo_user.py: owned by Antigravity, see module docstring")


if __name__ == "__main__":
    main()
