# CallMate

An AI call assistant: when you're away, CallMate answers forwarded calls in your own style,
figures out why the caller is calling, ranks the call by priority, and sends you a summary.
Urgent calls can be bridged to you live.

Full spec: [docs/HANDOFF.md](docs/HANDOFF.md). Tool-split for agents working this repo:
[AGENTS.md](AGENTS.md) and [ANTIGRAVITY_HANDOFF.md](ANTIGRAVITY_HANDOFF.md).

## Repository layout

| Path | Owns |
|---|---|
| `contracts/` | Shared WebSocket/REST message schemas — the only thing both services agree on |
| `pipeline/` | Telephony, audio, STT/TTS, turn-taking, notifications |
| `brain/` | Persona, memory, intent, priority, safety, replies |
| `tools/` | Dev utilities (call simulator, demo seed data) |
| `web/`, `android/` | Optional Phase 3 companions |

## Quickstart

```bash
cp .env.example .env            # defaults run fully on mock providers, no API keys needed
docker compose up -d postgres
uv sync
uv run alembic -c brain/alembic.ini upgrade head
uv run python tools/seed_demo_user.py
uv run uvicorn callmate_brain.main:app --port 8001 --reload
uv run uvicorn callmate_pipeline.main:app --port 8000 --reload
```

To take a real phone call instead of the mock/sim tools, see
[docs/runbook.md](docs/runbook.md) for Twilio number setup and `ngrok http 8000`.

## Independent development

- Pipeline against a stand-in brain: set `BRAIN_MODE=echo`.
- Brain against a typed caller instead of a phone call: `uv run python tools/sim_call.py`.
- Every external provider (STT, TTS, LLM) has a `mock` implementation selected via `.env` —
  the defaults in `.env.example` already use them.

## Checks

```bash
uv run ruff check .
uv run mypy contracts
uv run pytest -q
```
