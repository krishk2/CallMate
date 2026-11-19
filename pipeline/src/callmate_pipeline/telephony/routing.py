"""Decides answer / bridge / voicemail / block before Twilio gets any TwiML back
(docs/HANDOFF.md §6.1.1). Pure decision logic — no Twilio or HTTP calls here, so it's
unit-testable; `twilio_webhooks.py` fetches the CallContextResponse and calls this.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from callmate_contracts.enums import CallMode
from callmate_contracts.rest import CallContextResponse


class RoutingDecision(StrEnum):
    ANSWER_FRIENDLY = "answer_friendly"
    ANSWER_SCREENING = "answer_screening"
    VOICEMAIL = "voicemail"
    BLOCK = "block"


@dataclass(frozen=True)
class RoutingInput:
    caller_number: str
    twilio_number: str
    mode: CallMode
    call_context: CallContextResponse


def decide_routing(routing_input: RoutingInput) -> RoutingDecision:
    if routing_input.caller_number == routing_input.twilio_number:
        # Our own Twilio number calling itself means a forwarding loop — never re-forward.
        return RoutingDecision.VOICEMAIL
    if routing_input.call_context.blocked:
        return RoutingDecision.BLOCK
    if routing_input.call_context.known_contact and routing_input.mode == CallMode.AWAY:
        return RoutingDecision.ANSWER_FRIENDLY
    return RoutingDecision.ANSWER_SCREENING
