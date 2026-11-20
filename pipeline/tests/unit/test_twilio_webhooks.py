from callmate_pipeline.telephony.twilio_webhooks import (
    _effective_caller_number,
    validate_twilio_signature,
)


def test_normal_inbound_call_uses_from():
    params = {"From": "+919800000001", "To": "+14632922519", "Direction": "inbound"}
    assert _effective_caller_number(params) == "+919800000001"


def test_outbound_api_triggered_call_uses_to():
    params = {"From": "+14632922519", "To": "+919800000001", "Direction": "outbound-api"}
    assert _effective_caller_number(params) == "+919800000001"


def test_missing_direction_defaults_to_inbound_behavior():
    params = {"From": "+919800000001", "To": "+14632922519"}
    assert _effective_caller_number(params) == "+919800000001"


def test_signature_matches_known_good_value():
    # Computed independently with the same algorithm Twilio documents, to catch a regression
    # in our implementation rather than just mirroring it back.
    import base64
    import hashlib
    import hmac

    auth_token = "test-token"
    url = "https://example.com/twilio/voice"
    params = {"CallSid": "CA123", "From": "+919800000001"}
    data = url + "".join(f"{k}{params[k]}" for k in sorted(params))
    digest = hmac.new(auth_token.encode(), data.encode(), hashlib.sha1).digest()
    expected = base64.b64encode(digest).decode()

    assert validate_twilio_signature(url, params, expected, auth_token)
    assert not validate_twilio_signature(url, params, "wrong-signature", auth_token)
