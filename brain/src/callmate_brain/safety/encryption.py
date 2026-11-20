"""Application-level encryption at rest for stored call content (`MemoryRow.content`,
`CallRow.summary`) — even a compromised DB dump is unreadable without `ENCRYPTION_KEY`, which
never leaves app config (it's a Fly secret, not a database value). Symmetric (Fernet:
AES-128-CBC + HMAC), since we need to read our own data back, not just one-way hash it —
this is privacy-at-rest, not an auth/integrity check like the HMAC uses elsewhere
(`twilio_webhooks.py`'s signature check, `session_ws.py`'s bearer token comparison).

`ENCRYPTION_KEY` empty = disabled (store/read as plaintext), matching this project's pattern
of defaulting new infra to a safe no-op rather than breaking when it isn't configured
(`memory/repeat_calls.py`'s `REDIS_URL` does the same). This assumes every row was written
under whichever key is currently configured — toggling the key on/off/to-a-different-value
after real data exists will make old rows unreadable (`cryptography.fernet.InvalidToken`),
by design: there is no way to decrypt-and-reencrypt data you can no longer decrypt.
"""

from __future__ import annotations


def encrypt(plaintext: str) -> str:
    from ..config import settings

    if not settings.encryption_key:
        return plaintext
    from cryptography.fernet import Fernet

    return Fernet(settings.encryption_key.encode()).encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    from ..config import settings

    if not settings.encryption_key:
        return ciphertext
    from cryptography.fernet import Fernet

    return Fernet(settings.encryption_key.encode()).decrypt(ciphertext.encode()).decode()
