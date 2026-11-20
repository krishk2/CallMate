"""`POST /v1/calls/outbound` — triggers an outbound call via Twilio to any number, running
the same assistant flow a real inbound call would. This is what `scripts/trigger_test_call.ps1`
now calls into, and the mechanism behind the missed-call-callback workaround discussed for
India's outbound-ISD restriction.

`service_token` travels as a body field here, not a bearer header like `api/turns.py` — the
point of this endpoint is that dropping a number into Swagger UI's "Try it out" places a real
call with nothing else to configure first (no separate Authorize step). That's a deliberate
trade: a token sitting in a visible JSON field is easier to demo but less conventional than
header auth, since body fields are more likely to end up logged or cached somewhere. Still
checked with the same `hmac.compare_digest` as everywhere else — every call this places is
real and billable (Twilio minutes), so it can't be left open regardless of where the token
travels.
"""

from __future__ import annotations

import hmac

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..config import settings

router = APIRouter()

_TWILIO_CALLS_URL = "https://api.twilio.com/2010-04-01/Accounts/{sid}/Calls.json"


class OutboundCallRequest(BaseModel):
    to: str = Field(description="Number to call, E.164 format, e.g. +91XXXXXXXXXX")
    service_token: str = Field(description="Must match SERVICE_TOKEN (.env / fly secrets)")


class OutboundCallResponse(BaseModel):
    call_sid: str
    status: str


def _check_service_token(token: str) -> None:
    if not hmac.compare_digest(token, settings.service_token):
        raise HTTPException(status_code=403, detail="invalid service_token")


@router.post("/v1/calls/outbound", response_model=OutboundCallResponse)
async def trigger_outbound_call(body: OutboundCallRequest) -> OutboundCallResponse:
    _check_service_token(body.service_token)
    if not (settings.twilio_account_sid and settings.twilio_auth_token and settings.twilio_number):
        raise HTTPException(status_code=503, detail="Twilio credentials not configured")

    voice_url = f"{settings.public_base_url}/twilio/voice"
    url = _TWILIO_CALLS_URL.format(sid=settings.twilio_account_sid)
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            url,
            auth=(settings.twilio_account_sid, settings.twilio_auth_token),
            data={
                "To": body.to,
                "From": settings.twilio_number,
                "Url": voice_url,
                "Method": "POST",
            },
        )
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Twilio error: {response.text}")

    data = response.json()
    return OutboundCallResponse(call_sid=data["sid"], status=data["status"])
