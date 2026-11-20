# 0003: Application-level encryption at rest for stored call content

## Status
Accepted

## Context
`MemoryRow.content` (long-term memory summaries) and `CallRow.summary` (call history) store
real natural-language content about callers — redacted (`safety/redact.py`) but otherwise
plaintext. A compromised DB dump would expose it in full. Neon/Fly provide platform-level
encryption, but nothing at the application layer meant the data itself was legible to anyone
with raw DB access, independent of this app's own access controls.

## Decision
Encrypt both fields with Fernet (`cryptography` library — AES-128-CBC + HMAC, symmetric,
since the app needs to read its own data back) via `safety/encryption.py`'s `encrypt`/
`decrypt`, wired into `storage/repositories.py` (`SqlLongTermMemoryStore.add`/`search`,
`SqlCallHistoryRepository.add_call`) and `api/calls.py`'s read paths.

`ENCRYPTION_KEY` empty = disabled (store/read as plaintext) — same pattern as `REDIS_URL`
(`memory/repeat_calls.py`): new infra defaults to a safe no-op rather than breaking when it
isn't configured. It's a Fly secret on `brain` only; `pipeline` never touches this content.

## Consequences
- **No key-loss recovery.** If `ENCRYPTION_KEY` is lost or changed after real data exists,
  every row written under the old key becomes permanently unreadable
  (`cryptography.fernet.InvalidToken`) — there is no decrypt-and-reencrypt path for data you
  can no longer decrypt. Back the key up somewhere safe outside Fly's secret store.
- No migration path for mixed plaintext/ciphertext rows — this was adopted by deleting the
  (placeholder, non-sensitive) rows that existed before the key was set, rather than building
  try-decrypt-else-plaintext fallback logic for a handful of test rows. A real migration would
  be needed if this is ever toggled on against a database with real data already in it.
- `pgvector` similarity search is unaffected — only the `content`/`summary` text columns are
  encrypted, not the embedding vectors, so retrieval ranking works exactly as before.
- This is privacy-at-rest, not an integrity/auth mechanism — unrelated to the HMAC signature
  check in `twilio_webhooks.py` or the bearer-token comparison in `session_ws.py`/
  `outbound.py`, which use HMAC for a different purpose (verifying a sender's identity, not
  keeping data confidential).
