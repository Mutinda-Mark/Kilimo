"""
Simple authentication for KILIMO admin APIs.

For Phase 4B development, admin endpoints use a static Bearer
token stored in the environment.

A proper user/role authentication system can replace this later.
"""

from __future__ import annotations

import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from app.config import settings


bearer_scheme = HTTPBearer(
    auto_error=False
)


async def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
) -> None:
    """Require a valid KILIMO admin token."""

    configured_token = (
        settings.admin_api_token
        or ""
    ).strip()

    if not configured_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Admin authentication "
                "is not configured."
            ),
        )

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required.",
        )

    provided_token = (
        credentials.credentials
        or ""
    )

    if not secrets.compare_digest(
        provided_token,
        configured_token,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials.",
        )