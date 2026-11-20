from callmate_brain.config import settings
from callmate_brain.safety.encryption import decrypt, encrypt


def test_disabled_when_no_key_is_a_passthrough(monkeypatch):
    monkeypatch.setattr(settings, "encryption_key", "")
    assert encrypt("hello") == "hello"
    assert decrypt("hello") == "hello"


def test_roundtrip_with_key(monkeypatch):
    monkeypatch.setattr(settings, "encryption_key", "AZafUaBLd7OVD8b-lIsi9fveEbFja3rAUdwx5AihwIA=")
    ciphertext = encrypt("caller asked about a package delivery")
    assert ciphertext != "caller asked about a package delivery"
    assert decrypt(ciphertext) == "caller asked about a package delivery"


def test_ciphertext_does_not_contain_plaintext_substring(monkeypatch):
    monkeypatch.setattr(settings, "encryption_key", "AZafUaBLd7OVD8b-lIsi9fveEbFja3rAUdwx5AihwIA=")
    secret = "the OTP is 482913"
    ciphertext = encrypt(secret)
    assert "482913" not in ciphertext
    assert "OTP" not in ciphertext
