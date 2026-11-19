from enum import StrEnum


class CallState(StrEnum):
    RINGING = "ringing"
    GREETING = "greeting"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    ESCALATING = "escalating"
    CLOSING = "closing"


# Allowed transitions (docs/HANDOFF.md §6.1.7). LISTENING/THINKING/SPEAKING cycle per turn;
# any state can go to CLOSING (hangup, error, or voicemail fallback can happen at any point).
_ALLOWED: dict[CallState, set[CallState]] = {
    CallState.RINGING: {CallState.GREETING, CallState.CLOSING},
    CallState.GREETING: {CallState.LISTENING, CallState.CLOSING},
    CallState.LISTENING: {CallState.THINKING, CallState.CLOSING},
    CallState.THINKING: {CallState.SPEAKING, CallState.ESCALATING, CallState.CLOSING},
    CallState.SPEAKING: {CallState.LISTENING, CallState.ESCALATING, CallState.CLOSING},
    CallState.ESCALATING: {CallState.LISTENING, CallState.CLOSING},
    CallState.CLOSING: set(),
}


class InvalidTransition(Exception):
    def __init__(self, from_state: CallState, to_state: CallState) -> None:
        super().__init__(f"Cannot transition {from_state} -> {to_state}")


def assert_valid_transition(from_state: CallState, to_state: CallState) -> None:
    if to_state not in _ALLOWED[from_state]:
        raise InvalidTransition(from_state, to_state)
