from callmate_brain.reasoning.priority import PriorityInputs, score_call
from callmate_contracts.enums import Priority


def test_emergency_keyword_forces_urgent_regardless_of_other_signals():
    result = score_call(
        PriorityInputs(
            relationship=None,
            repeat_calls_in_window=0,
            caller_text="There's been an accident, please call back.",
            llm_urgency=0.0,
            spam_signal=True,
        )
    )
    assert result.level == Priority.URGENT
    assert result.forced_urgent is True


def test_family_relationship_scores_higher_than_service():
    family = score_call(
        PriorityInputs(
            relationship="family",
            repeat_calls_in_window=0,
            caller_text="Hey, call me back when you can.",
            llm_urgency=0.0,
            spam_signal=False,
        )
    )
    service = score_call(
        PriorityInputs(
            relationship="service",
            repeat_calls_in_window=0,
            caller_text="Hey, call me back when you can.",
            llm_urgency=0.0,
            spam_signal=False,
        )
    )
    assert family.score > service.score


def test_spam_signal_reduces_score():
    clean = score_call(
        PriorityInputs(
            relationship="service",
            repeat_calls_in_window=0,
            caller_text="Just checking in.",
            llm_urgency=0.5,
            spam_signal=False,
        )
    )
    spammy = score_call(
        PriorityInputs(
            relationship="service",
            repeat_calls_in_window=0,
            caller_text="Just checking in.",
            llm_urgency=0.5,
            spam_signal=True,
        )
    )
    assert spammy.score < clean.score


def test_score_is_clamped_to_0_100():
    result = score_call(
        PriorityInputs(
            relationship="family",
            repeat_calls_in_window=10,
            caller_text="hello",
            llm_urgency=1.0,
            spam_signal=False,
        )
    )
    assert 0 <= result.score <= 100


def test_repeat_calls_bump_priority():
    once = score_call(
        PriorityInputs(
            relationship="service",
            repeat_calls_in_window=0,
            caller_text="hello",
            llm_urgency=0.2,
            spam_signal=False,
        )
    )
    repeated = score_call(
        PriorityInputs(
            relationship="service",
            repeat_calls_in_window=3,
            caller_text="hello",
            llm_urgency=0.2,
            spam_signal=False,
        )
    )
    assert repeated.score > once.score
