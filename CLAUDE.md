@AGENTS.md

- This is a two-person monorepo. Before editing, check which folder you are in and stay there.
- `contracts/` is shared: never change it without updating `docs/contracts.md` and the
  contracts round-trip tests, in the same commit.
- Read `docs/HANDOFF.md` sections 5 (contract) and 8 (privacy) before any feature work.
- Run `uv run ruff check . && uv run pytest -q <your package>` before saying a task is done.
