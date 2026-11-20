import pytest
from callmate_pipeline.config import settings
from callmate_pipeline.telephony.outbound import _check_service_token
from fastapi import HTTPException


def test_correct_token_passes(monkeypatch):
    monkeypatch.setattr(settings, "service_token", "secret123")
    _check_service_token("secret123")  # should not raise


def test_wrong_token_rejected(monkeypatch):
    monkeypatch.setattr(settings, "service_token", "secret123")
    with pytest.raises(HTTPException) as exc_info:
        _check_service_token("wrong")
    assert exc_info.value.status_code == 403
