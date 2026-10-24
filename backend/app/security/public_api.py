from __future__ import annotations

from fastapi import (
    HTTPException,
    status,
)


DIRECT_API_ENVIRONMENTS = frozenset(
    {
        "development",
        "dev",
        "local",
        "test",
        "testing",
    }
)


def direct_api_is_enabled(
    environment: str | None,
) -> bool:
    """
    Determine whether direct /predict and /chat access is allowed.

    Only explicitly recognised development/test environments are
    permitted. Unknown values fail closed.
    """

    normalized_environment = (
        environment
        or ""
    ).strip().lower()

    return (
        normalized_environment
        in DIRECT_API_ENVIRONMENTS
    )


def require_direct_api_access(
    environment: str | None,
) -> None:
    """
    Reject direct API access when KILIMO is not running in an
    explicitly permitted development/test environment.

    HTTP 404 is returned rather than advertising that a disabled
    production endpoint exists.
    """

    if direct_api_is_enabled(
        environment
    ):
        return

    raise HTTPException(
        status_code=(
            status.HTTP_404_NOT_FOUND
        ),
        detail="Not Found",
    )