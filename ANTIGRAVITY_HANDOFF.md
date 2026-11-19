# CallMate: Handoff for Antigravity

> Read this first. `docs/HANDOFF.md` is the full project spec — read it before starting
> anything, especially §5 (the pipeline↔brain contract) and §8 (privacy/safety). This document
> only tells you **which slice is yours** and the rules for touching a repo that Claude Code is
> also actively building.

---

## 0. Why this split exists

CallMate is being built with two AI coding tools in the same monorepo: **Claude Code** owns the
core call pipeline and brain logic (the live-call hot path, the shared contract, memory, and
safety rules). You own everything around that core — tooling, mocks, docs, the optional
dashboard, and content authoring. This isn't a judgment on difficulty of code so much as blast
radius: the things Claude Code owns, if broken, break a live phone call or leak private data.
The things you own, if broken, are easy to catch and low-stakes to fix.

**Rule of thumb for anything not listed below:** if it's on the hot path of a live call, touches
`contracts/`, or is a safety/privacy rule — that's not yours, leave it to Claude Code. If it's a
tool, a doc, a mock, or optional/Phase 3 — it's yours.

---

## 1. What is explicitly yours

### 1.1 `tools/` — dev utilities
- `tools/sim_call.py` — text-only call simulator: type as the caller, see the brain's streamed
  replies, priority updates, and final `session.result`. Talks to the brain over the same
  WebSocket contract pipeline uses (`contracts/`), just from a terminal instead of a phone call.
- `tools/seed_demo_user.py` — creates a demo user, contacts, style samples, and tone settings so
  both services have something to run against locally.
- **Done when:** a fresh clone can run `uv run python tools/seed_demo_user.py` then
  `uv run python tools/sim_call.py --user demo --caller +9198…` and hold a full typed
  conversation against the brain service with no manual DB setup.

### 1.2 Mock providers
- `pipeline/src/callmate_pipeline/stt/mock.py` — reads text fixtures instead of calling Deepgram/Google.
- `pipeline/src/callmate_pipeline/tts/mock.py` — beep/silence instead of calling ElevenLabs/Google.
- `brain/src/callmate_brain/llm/mock.py` — deterministic scripted replies instead of calling Anthropic/Gemini.
- `pipeline/src/callmate_pipeline/brain_client/echo_brain.py` — a stand-in brain that just echoes
  "You said: …" and returns a fixed `session.result`, so Person 1 can build pipeline features
  without the real brain running.
- These must implement the same `STTProvider` / `TTSProvider` / `LLMProvider` protocols that
  Claude Code defines in each `base.py` — **read those protocol files, don't invent your own
  shape.** If a protocol file doesn't exist yet when you get to this, ask rather than guessing
  its signature.
- **Done when:** setting `STT_PROVIDER=mock`, `TTS_PROVIDER=mock`, `LLM_PROVIDER=mock`,
  `BRAIN_MODE=echo` in `.env` lets the whole stack run with zero external API keys.

### 1.3 Notifications
- `pipeline/src/callmate_pipeline/notify/telegram.py` — sends the `session.result` to the user
  via Telegram Bot API within 15 s of hang-up. Format: emoji per priority level (🔴 Urgent,
  🟠 Important, 🟡 Normal, ⚪ Low), caller number/name, intent, 2-sentence summary, and a
  `tel:` callback link. See the example in `docs/HANDOFF.md` §4.
- `pipeline/src/callmate_pipeline/notify/sms.py` — same idea as a Twilio SMS/WhatsApp fallback.
- These are plain outbound API calls triggered on `session.end` — no call-state or
  latency-sensitive logic involved.

### 1.4 Latency reporting (presentation only, not the spans themselves)
- `pipeline/src/callmate_pipeline/metrics/latency.py` defines what gets recorded
  (`eot_detected`, `final_transcript`, `brain_first_token`, `tts_first_byte`, `first_audio_sent`)
  — that instrumentation lives inside the call session code, which is Claude Code's.
- `pipeline/scripts/latency_report.py` is yours: read the recorded spans and print p50/p95 per
  stage. Pure reporting, no call-path code.

### 1.5 Documentation
- `README.md` — quickstart: clone → env → `docker compose up` → call the number.
- `docs/runbook.md` — Twilio number setup, carrier forwarding codes (listed in `docs/HANDOFF.md`
  §6.1), ngrok setup.
- `docs/contracts.md` — human-readable description of the WebSocket/REST contract in
  `docs/HANDOFF.md` §5. **You write the prose, but you do not change the contract itself** — if the
  schema and this doc disagree, the schema (owned by Claude Code, reviewed by both per
  CODEOWNERS) wins and you update the doc to match, never the other way around.
- `docs/adr/NNNN-*.md` — short architecture decision records (≤ 1 page) whenever a choice in
  `docs/HANDOFF.md` §1 changes. You can draft these; anything touching the contract or a safety rule
  needs Claude Code's sign-off before merging.

### 1.6 Eval content authoring (not the scoring logic)
- `brain/evals/transcripts/*.yaml` — golden call transcripts with expected intent + priority
  label. Target ≥ 40 scenarios (`docs/HANDOFF.md` §7.12).
- `brain/evals/redteam/*.yaml` — adversarial scenarios (OTP grabs, injections, commitment
  traps). Target ≥ 20.
- You're authoring realistic *content* here (what a caller plausibly says, and what the
  correct label should be) — `run_evals.py` itself (the scorer) is Claude Code's, since it
  grades against the priority/intent logic Claude Code owns.

### 1.7 Optional / Phase 3
- `web/` — settings + call-history dashboard (sliders for tone, contacts list, memory list with
  delete, call history with priority badges). Reads the brain's REST API (`docs/HANDOFF.md` §5.3) —
  it's a client of the contract, never a definer of it. Next.js or plain HTMX, your call.
- `android/` — `CallScreeningService` companion app that rejects non-contact callers so carrier
  "forward on busy" routes them to Twilio. Entirely separate codebase; only needs to agree on
  the mode toggle it exposes.

### 1.8 Repo scaffolding (one-time, early)
- `.env.example`, root `pyproject.toml` workspace wiring, `docker-compose.yml` boilerplate
  (postgres/pipeline/brain service definitions). Get the skeleton running; Claude Code fills in
  the real logic inside it.

---

## 2. What is explicitly NOT yours

Do not edit these, even if a task above seems to brush up against them:

- `contracts/` (any file) — shared schemas. Changing this without both owners' sign-off breaks
  both services silently. If a tool/mock/doc you're writing seems to need a new message type or
  field, **stop and flag it** rather than adding it yourself.
- Anything under `pipeline/.../media/`, `pipeline/.../stt/` (real providers), `pipeline/.../tts/`
  (real providers), `pipeline/.../session/`, `pipeline/.../telephony/` — the live-call hot path.
- Anything under `brain/.../memory/`, `brain/.../reasoning/`, `brain/.../safety/`,
  `brain/.../persona/`, `brain/.../llm/` (real providers) — judgement, memory, and safety logic.
- Alembic migrations and DB schema definitions.
- CI workflow logic (`.github/workflows/ci.yml`) beyond adding your own test targets to it.

If you're ever unsure whether something is yours, check this list and the hot-path/contract/
safety rule of thumb in §0 before writing code.

---

## 3. Working rules

- Keep `AGENTS.md` (shared agent rules, read by both Claude Code via `CLAUDE.md` and by you) up
  to date if you learn something both tools should follow — don't fork a separate rule set.
- Branch naming: your work isn't owned by "Person 1" or "Person 2" in `docs/HANDOFF.md`'s sense, so
  prefix branches `tooling/<feature>`, `docs/<feature>`, or `web/<feature>` to keep it visually
  distinct from `p1/*` and `p2/*` branches.
- Every mock/provider you write must satisfy the existing protocol in that module's `base.py` —
  if `base.py` doesn't exist yet, that's a sign Claude Code hasn't built that slice yet; ask
  before inventing the interface yourself, since you'd be guessing at a contract someone else
  has to implement against.
- Before calling anything done, run `uv run ruff check . && uv run pytest -q <your package>`,
  same as the root `CLAUDE.md` rule.
- `docker compose up -d postgres && uv sync` should always be enough for a fresh clone to get to
  a runnable state for whatever you just built — if it isn't, that's a scaffolding gap, fix it.

---

## 4. Suggested first prompt

> "Read ANTIGRAVITY_HANDOFF.md and the relevant sections of docs/HANDOFF.md it points to. Start with
> §1.8 (repo scaffolding: `.env.example`, workspace `pyproject.toml`, `docker-compose.yml`) so
> there's something to run, then §1.2 (mock providers) so Claude Code can build pipeline and
> brain independently against them. Plan first."
