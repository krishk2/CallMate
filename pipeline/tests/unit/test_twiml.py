from callmate_pipeline.telephony.twiml import build_media_stream_twiml, build_twiml_for_call

_BASE_KWARGS = dict(user_id="demo", caller_number="+919800000001", mode="away")


def test_media_streams_mode_builds_connect_stream():
    twiml = build_twiml_for_call(
        "CA123", public_base_url="https://example.ngrok-free.app", **_BASE_KWARGS
    )
    assert "<Connect><Stream" in twiml
    assert "wss://example.ngrok-free.app/media/CA123" in twiml


def test_conversation_relay_mode_builds_connect_relay():
    twiml = build_twiml_for_call(
        "CA123",
        public_base_url="http://localhost:8000",
        telephony_mode="conversation_relay",
        **_BASE_KWARGS,
    )
    assert "<ConversationRelay" in twiml
    assert "ws://localhost:8000/relay/CA123" in twiml


def test_call_id_is_escaped():
    twiml = build_media_stream_twiml(
        '"><script>', public_base_url="http://localhost:8000", **_BASE_KWARGS
    )
    assert "<script>" not in twiml


def test_caller_parameters_are_passed_through():
    twiml = build_media_stream_twiml(
        "CA123",
        public_base_url="http://localhost:8000",
        user_id="demo",
        caller_number="+919800000001",
        mode="away",
        caller_name="Asha",
        language_hint="hi-IN",
    )
    assert '<Parameter name="user_id" value="demo" />' in twiml
    assert '<Parameter name="caller_number" value="+919800000001" />' in twiml
    assert '<Parameter name="caller_name" value="Asha" />' in twiml
    assert '<Parameter name="language_hint" value="hi-IN" />' in twiml


def test_empty_caller_name_is_omitted():
    twiml = build_media_stream_twiml(
        "CA123", public_base_url="http://localhost:8000", **_BASE_KWARGS
    )
    assert "caller_name" not in twiml


def test_parameter_values_are_escaped():
    twiml = build_media_stream_twiml(
        "CA123",
        public_base_url="http://localhost:8000",
        user_id="demo",
        caller_number="+919800000001",
        mode="away",
        caller_name='"><script>alert(1)</script>',
    )
    assert "<script>" not in twiml
