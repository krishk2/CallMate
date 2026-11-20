from callmate_pipeline.stt.deepgram_nova import _build_query


def test_explicit_language_is_passed_through():
    query = _build_query("te", None)
    assert "language=te" in query
    assert "detect_language" not in query


def test_auto_language_requests_detection():
    query = _build_query("auto", None)
    assert "detect_language=true" in query
    assert "&language=" not in query


def test_keyterms_are_included():
    query = _build_query("en-IN", ["CallMate", "Asha"])
    assert query.count("keyterm=") == 2
    assert "keyterm=CallMate" in query
    assert "keyterm=Asha" in query


def test_mulaw_8khz_is_always_requested():
    query = _build_query("en-IN", None)
    assert "encoding=mulaw" in query
    assert "sample_rate=8000" in query
