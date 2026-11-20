# Privacy, consent and safety

Owned by Person 2 / brain (`docs/HANDOFF.md` §8). This should expand the principles table in
`docs/HANDOFF.md` §8 into a full design doc, plus:

**TODO:**
- Which third parties process what (Twilio, Deepgram, ElevenLabs, Anthropic, Google) and
  their retention/training settings; prefer zero-retention options where offered.
- DPDP Act 2023 principles (notice, consent, purpose limitation, erasure) — note this is a
  student demo, not legal advice.
- Retention policy specifics once `AUDIO_RETENTION_DAYS` / `TRANSCRIPT_RETENTION_DAYS` cleanup
  jobs exist (`docs/HANDOFF.md` §8, "Retention" row).

The enforcement code this doc describes already exists: `brain/src/callmate_brain/safety/`
(guardrails, output_filter, injection, redact, encryption) and
`pipeline/.../telephony/twilio_webhooks.py` (signature validation). This doc is the write-up,
not a spec for new code.

**Encryption at rest** (`safety/encryption.py`, `docs/adr/0003-encrypt-stored-content-at-rest.md`):
stored call summaries (`MemoryRow.content`, `CallRow.summary`) are encrypted with Fernet
before they ever reach Postgres — a DB dump alone doesn't expose them. This is on top of,
not instead of, the redaction in `safety/redact.py`: redaction removes specific
OTP/card/Aadhaar-shaped patterns before storage; encryption protects everything else that's
left. Key (`ENCRYPTION_KEY`) is a Fly secret on `brain` only — losing it makes existing
encrypted rows permanently unreadable, so it needs a backup outside Fly's secret store.
