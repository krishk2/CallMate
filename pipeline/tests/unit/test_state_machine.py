import pytest
from callmate_pipeline.session.state import CallState, InvalidTransition, assert_valid_transition


def test_happy_path_turn_cycle():
    assert_valid_transition(CallState.RINGING, CallState.GREETING)
    assert_valid_transition(CallState.GREETING, CallState.LISTENING)
    assert_valid_transition(CallState.LISTENING, CallState.THINKING)
    assert_valid_transition(CallState.THINKING, CallState.SPEAKING)
    assert_valid_transition(CallState.SPEAKING, CallState.LISTENING)


def test_any_state_can_close():
    for state in CallState:
        if state is CallState.CLOSING:
            continue
        assert_valid_transition(state, CallState.CLOSING)


def test_closing_is_terminal():
    with pytest.raises(InvalidTransition):
        assert_valid_transition(CallState.CLOSING, CallState.LISTENING)


def test_cannot_skip_listening_to_speaking():
    with pytest.raises(InvalidTransition):
        assert_valid_transition(CallState.LISTENING, CallState.SPEAKING)


def test_escalation_returns_to_listening_or_closes():
    assert_valid_transition(CallState.ESCALATING, CallState.LISTENING)
    assert_valid_transition(CallState.ESCALATING, CallState.CLOSING)
