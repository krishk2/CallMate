# Deploying to Fly.io

Both services deploy to Fly.io as separate apps (`fly.brain.toml`, `fly.pipeline.toml` at the
repo root). Deploy `brain` first — `pipeline`'s config references it over Fly's private
network before it necessarily exists.

Prerequisites: a Fly.io account, `flyctl` installed and logged in (`fly auth login`). Run all
commands from the repo root — the Dockerfiles expect the repo root as build context, since
each one `COPY`s both `contracts/` and its own service directory.

## 1. Brain

```bash
fly launch --no-deploy --config fly.brain.toml --dockerfile brain/Dockerfile
# Follow the prompt to confirm the app name ("callmate-brain") and region; say no to
# attaching a Postgres — this project uses Neon, not Fly Postgres.

fly secrets set --config fly.brain.toml \
  SERVICE_TOKEN=<same value pipeline will use> \
  DATABASE_URL="postgresql+asyncpg://<user>:<password>@<host>.neon.tech/<db>?ssl=require" \
  GROQ_API_KEY=<key> NVIDIA_API_KEY=<key>
  # only needed if REPLY_LLM_PROVIDER=groq / SUMMARY_LLM_PROVIDER=nvidia / EMBEDDING_PROVIDER=nvidia;
  # leave those set to "mock"/"local" to deploy without real keys first

fly deploy --config fly.brain.toml

# One-time schema setup (Alembic migrations aren't wired to a CI step yet — see
# docs/HANDOFF.md §10 Week 1 scope):
fly ssh console --config fly.brain.toml -C "uv run alembic -c brain/alembic.ini upgrade head"
```

## 2. Pipeline

```bash
fly launch --no-deploy --config fly.pipeline.toml --dockerfile pipeline/Dockerfile
# Same prompts; again, no Fly Postgres.

fly secrets set --config fly.pipeline.toml \
  SERVICE_TOKEN=<same value as brain> \
  TWILIO_ACCOUNT_SID=... TWILIO_AUTH_TOKEN=... TWILIO_NUMBER=... \
  TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=...
  # DEEPGRAM_API_KEY / ELEVENLABS_API_KEY only if you flip STT_PROVIDER/TTS_PROVIDER off mock

fly deploy --config fly.pipeline.toml
```

## 3. Point Twilio at the deployed pipeline

In the Twilio console, set the number's Voice webhook to:

```
https://callmate-pipeline.fly.dev/twilio/voice
```

(swap the hostname if you changed the app name in `fly.pipeline.toml`).

## Running this alongside local/ngrok development

A single Twilio number can only point its webhook at one URL. To develop locally while the
Fly deployment keeps working for others, use a **second Twilio number** for local dev,
pointed at your ngrok URL — see the ngrok section of `docs/runbook.md`. Both numbers can run
at the same time without conflict; only the webhook URL differs.

## Why Fly.io for both services, not the Cloud Run split in docs/HANDOFF.md §1.1

See `docs/adr/0001-deploy-to-fly-io.md`.
