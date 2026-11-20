"""Shared SERVICE_TOKEN bearer-auth dependency for pipeline REST endpoints that are reachable
on the public internet and must not be left open (outbound calling, call/turn history reads).
"""

from __future__ import annotations

import hmac

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings

bearer_scheme = HTTPBearer(description="SERVICE_TOKEN (see .env / fly secrets)")


def require_service_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> None:
    if not hmac.compare_digest(credentials.credentials, settings.service_token):
        raise HTTPException(status_code=403, detail="invalid bearer token")
