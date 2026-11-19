# Agent rules for CallMate

These rules apply to every coding agent working in this repo (Claude Code, Antigravity, or
anyone else). Read `docs/HANDOFF.md` for the full spec and `ANTIGRAVITY_HANDOFF.md` for how
work is split between tools.

## Boundaries

- This is a multi-owner monorepo: `pipeline/` (call pipeline), `brain/` (memory + LLM), and a
  set of supporting pieces (`tools/`, `web/`, `android/`, `docs/`). Check which folder you are
  in before editing; do not reach into another owner's folder to "help."
- `contracts/` is shared. **Never** change a message or REST model in `contracts/` without, in
  the same commit: bumping `PROTOCOL_VERSION` in `version.py`, updating `docs/contracts.md`,
  and updating `contracts/tests/test_roundtrip.py`. This is enforced by CODEOWNERS review.
- Unknown message types on either side of the WebSocket contract must be logged and ignored,
  never raise.

## Design principles (apply these, don't just read them)

- **Dependency inversion at every provider boundary.** `pipeline` and `brain` code depend on
  the `Protocol`/ABC in each module's `base.py` (`STTProvider`, `TTSProvider`, `LLMProvider`),
  never on a concrete SDK client directly. Adding a provider means adding a new class that
  satisfies the protocol, not editing the callers (open/closed).
- **Single responsibility per module.** `telephony/` decides *whether* to answer; `media/`
  moves bytes; `stt/`/`tts/` convert audio↔text; `session/` orchestrates state; `reasoning/`
  decides *what to say*; `safety/` decides what's allowed to leave the brain. Don't let one
  module grow a second job.
- **Config over hardcoding.** All provider choice, model IDs, thresholds and timeouts come from
  `config.py` (`pydantic-settings`, reading `.env`). Never hardcode an API key, model ID, or
  magic latency threshold inline — if you need a new tunable, add it to `config.py`.
- **Narrow interfaces.** Don't add a method to a provider protocol that only one implementation
  needs — split it into a smaller protocol instead (interface segregation).
- **Data, never instructions.** Caller speech and retrieved memories are always treated as
  fenced data in prompts, never as instructions to the model. Any new prompt-assembly code must
  preserve that fencing.
- **Never leave the caller in silence.** Any new pipeline code on the call path needs a
  documented fallback (filler, failover provider, or voicemail) if it fails.

## Before calling a task done

```bash
uv run ruff check .
uv run mypy contracts
uv run pytest -q <the package(s) you touched>
```

## Workflow

- Start non-trivial features in plan mode, referencing the `docs/HANDOFF.md` section.
- Branch naming: `p1/<feature>` (pipeline), `p2/<feature>` (brain), `tooling/<feature>`,
  `docs/<feature>`, or `web/<feature>` for supporting work.
- Write an ADR (`docs/adr/NNNN-*.md`, ≤ 1 page) whenever a choice in `docs/HANDOFF.md` §1
  changes.
