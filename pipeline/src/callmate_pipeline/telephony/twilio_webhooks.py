"""`/twilio/voice` and `/twilio/status`. Validates `X-Twilio-Signature` on every webhook
(docs/HANDOFF.md §8 — security) before doing anything else.
"""

from __future__ import annotations

import base64
import hashlib
import hmac

import httpx
import structlog
from callmate_contracts.enums import CallMode
from callmate_contracts.rest import CallContextResponse
from fastapi import APIRouter, HTTPException, Request, Response

from ..config import settings
from .routing import RoutingDecision, RoutingInput, decide_routing
from .twiml import build_twiml_for_call

router = APIRouter()
logger = structlog.get_logger(__name__)


def validate_twilio_signature(
    url: str, params: dict[str, str], signature: str, auth_token: str
) -> bool:
    """Twilio's documented signature algorithm: base64(hmac-sha1(auth_token, url + sorted
    'key'+'value' pairs)). Implemented directly (stdlib hmac/hashlib) to avoid pulling in the
    full `twilio` SDK for one check.
    """
    data = url + "".join(f"{key}{params[key]}" for key in sorted(params))
    digest = hmac.new(auth_token.encode(), data.encode(), hashlib.sha1).digest()
    expected = base64.b64encode(digest).decode()
    return hmac.compare_digest(expected, signature)


async def _require_valid_signature(request: Request, params: dict[str, str]) -> None:
    signature = request.headers.get("X-Twilio-Signature", "")
    auth_token = settings.twilio_auth_token
    if not validate_twilio_signature(str(request.url), params, signature, auth_token):
        raise HTTPException(status_code=403, detail="invalid Twilio signature")


def _effective_caller_number(params: dict[str, str]) -> str:
    """Normal inbound call: the caller is `From`, our number is `To`. A call we triggered
    ourselves via the REST API (`Direction=outbound-api` — e.g. testing from a phone that
    can't dial our number directly due to international-dialing restrictions) reverses that:
    `From` is our own number and `To` is whoever picked up, so *they* are the caller for
    routing purposes.
    """
    if params.get("Direction") == "outbound-api":
        return params.get("To", "")
    return params.get("From", "")


async def _fetch_call_context(caller_number: str) -> CallContextResponse:
    url = f"{settings.brain_rest_base_url}/v1/users/{settings.demo_user_id}/call-context"
    try:
        async with httpx.AsyncClient(timeout=settings.call_context_timeout_s) as client:
            response = await client.get(url, params={"caller": caller_number})
            response.raise_for_status()
            return CallContextResponse.model_validate(response.json())
    except httpx.HTTPError:
        logger.warning("call_context_lookup_failed", caller_number=caller_number)
        return CallContextResponse(known_contact=False)


@router.post("/twilio/voice")
async def twilio_voice(request: Request) -> Response:
    form = await request.form()
    params = {key: str(value) for key, value in form.items()}
    await _require_valid_signature(request, params)

    call_sid = params.get("CallSid", "")
    caller_number = _effective_caller_number(params)
    call_context = await _fetch_call_context(caller_number)
    decision = decide_routing(
        RoutingInput(
            caller_number=caller_number,
            twilio_number=settings.twilio_number,
            mode=CallMode.SCREEN_UNKNOWN if not call_context.known_contact else CallMode.AWAY,
            call_context=call_context,
        )
    )

    if decision == RoutingDecision.BLOCK:
        twiml = '<?xml version="1.0" encoding="UTF-8"?><Response><Hangup /></Response>'
    elif decision == RoutingDecision.VOICEMAIL:
        twiml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<Response><Say>Please leave a message after the tone.</Say>"
            '<Record maxLength="120" /></Response>'
        )
    else:
        # ANSWER_FRIENDLY / ANSWER_SCREENING both connect to the media stream; the brain
        # adapts tone based on whether the caller is a known contact (sent in session.start).
        is_friendly = decision == RoutingDecision.ANSWER_FRIENDLY
        mode = CallMode.AWAY if is_friendly else CallMode.SCREEN_UNKNOWN
        twiml = build_twiml_for_call(
            call_sid,
            public_base_url=settings.public_base_url,
            user_id=settings.demo_user_id,
            caller_number=caller_number,
            mode=mode.value,
            caller_name=call_context.contact_name,
            telephony_mode=settings.telephony_mode,
        )

    return Response(content=twiml, media_type="application/xml")


@router.post("/twilio/status")
async def twilio_status(request: Request) -> Response:
    form = await request.form()
    params = {key: str(value) for key, value in form.items()}
    await _require_valid_signature(request, params)
    logger.info("twilio_status", call_sid=params.get("CallSid"), status=params.get("CallStatus"))
    return Response(status_code=204)
