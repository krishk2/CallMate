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
(guardrails, output_filter, injection, redact) and `pipeline/.../telephony/twilio_webhooks.py`
(signature validation). This doc is the write-up, not a spec for new code.
