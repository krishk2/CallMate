from callmate_contracts.enums import Intent, Priority
from callmate_contracts.messages import SessionResult
from callmate_pipeline.notify.telegram import format_summary_message


def _result(**overrides) -> SessionResult:
    defaults = dict(
        call_id="c1",
        seq=1,
        priority_level=Priority.URGENT,
        score=90,
        intent=Intent.PERSONAL_URGENT,
        summary="Caller says it's an emergency.",
        callback_needed=True,
        reason="emergency keyword",
    )
    defaults.update(overrides)
    return SessionResult(**defaults)


def test_message_includes_priority_and_intent():
    text = format_summary_message(
        caller_number="+919800000001", caller_name=None, result=_result(), duration_s=72
    )
    assert "URGENT" in text
    assert "personal urgent" in text
    assert "1m 12s" in text


def test_message_prefers_caller_name_over_number():
    text = format_summary_message(
        caller_number="+919800000001",
        caller_name="Asha",
        result=_result(),
        duration_s=5,
    )
    assert "Asha" in text
    assert "tel:+919800000001" in text


def test_message_falls_back_to_number_without_name():
    text = format_summary_message(
        caller_number="+919800000001", caller_name=None, result=_result(), duration_s=5
    )
    assert "+919800000001" in text
