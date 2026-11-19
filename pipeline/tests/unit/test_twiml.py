from callmate_pipeline.config import settings
from callmate_pipeline.telephony.twiml import build_twiml_for_call


def test_media_streams_mode_builds_connect_stream(monkeypatch):
    monkeypatch.setattr(settings, "telephony_mode", "media_streams")
    monkeypatch.setattr(settings, "public_base_url", "https://example.ngrok-free.app")
    twiml = build_twiml_for_call("CA123")
    assert "<Connect><Stream" in twiml
    assert "wss://example.ngrok-free.app/media/CA123" in twiml


def test_conversation_relay_mode_builds_connect_relay(monkeypatch):
    monkeypatch.setattr(settings, "telephony_mode", "conversation_relay")
    monkeypatch.setattr(settings, "public_base_url", "http://localhost:8000")
    twiml = build_twiml_for_call("CA123")
    assert "<ConversationRelay" in twiml
    assert "ws://localhost:8000/relay/CA123" in twiml


def test_call_id_is_escaped():
    from callmate_pipeline.telephony.twiml import build_media_stream_twiml

    twiml = build_media_stream_twiml('"><script>')
    assert "<script>" not in twiml
