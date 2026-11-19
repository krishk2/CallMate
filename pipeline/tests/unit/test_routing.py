from callmate_contracts.enums import CallMode
from callmate_contracts.rest import CallContextResponse
from callmate_pipeline.telephony.routing import RoutingDecision, RoutingInput, decide_routing


def _routing_input(**overrides) -> RoutingInput:
    defaults = dict(
        caller_number="+919800000001",
        twilio_number="+919800000000",
        mode=CallMode.SCREEN_UNKNOWN,
        call_context=CallContextResponse(known_contact=False),
    )
    defaults.update(overrides)
    return RoutingInput(**defaults)


def test_blocked_contact_is_blocked():
    routing_input = _routing_input(
        call_context=CallContextResponse(known_contact=True, blocked=True)
    )
    assert decide_routing(routing_input) == RoutingDecision.BLOCK


def test_known_contact_while_away_is_answered_friendly():
    routing_input = _routing_input(
        mode=CallMode.AWAY, call_context=CallContextResponse(known_contact=True)
    )
    assert decide_routing(routing_input) == RoutingDecision.ANSWER_FRIENDLY


def test_unknown_caller_is_answered_with_screening():
    routing_input = _routing_input(call_context=CallContextResponse(known_contact=False))
    assert decide_routing(routing_input) == RoutingDecision.ANSWER_SCREENING


def test_forwarding_loop_goes_to_voicemail():
    routing_input = _routing_input(caller_number="+919800000000", twilio_number="+919800000000")
    assert decide_routing(routing_input) == RoutingDecision.VOICEMAIL


def test_known_contact_while_screening_is_still_screened():
    routing_input = _routing_input(
        mode=CallMode.SCREEN_UNKNOWN, call_context=CallContextResponse(known_contact=True)
    )
    assert decide_routing(routing_input) == RoutingDecision.ANSWER_SCREENING
