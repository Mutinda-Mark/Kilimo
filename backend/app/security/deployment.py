from __future__ import annotations


DEVELOPMENT_ENVIRONMENTS = frozenset(
    {
        "development",
        "dev",
        "local",
        "test",
        "testing",
    }
)

PRODUCTION_ENVIRONMENTS = frozenset(
    {
        "production",
        "prod",
    }
)


def normalize_environment(
    environment: str | None,
) -> str:
    return (
        environment
        or ""
    ).strip().lower()


def is_production_environment(
    environment: str | None,
) -> bool:
    return (
        normalize_environment(
            environment
        )
        in PRODUCTION_ENVIRONMENTS
    )


def is_known_environment(
    environment: str | None,
) -> bool:
    normalized = normalize_environment(
        environment
    )

    return (
        normalized
        in DEVELOPMENT_ENVIRONMENTS
        or normalized
        in PRODUCTION_ENVIRONMENTS
    )


def api_documentation_urls(
    environment: str | None,
) -> dict[str, str | None]:
    """
    Expose interactive API documentation only in explicitly
    recognised development and testing environments.

    Unknown environments fail closed.
    """

    normalized = normalize_environment(
        environment
    )

    docs_enabled = (
        normalized
        in DEVELOPMENT_ENVIRONMENTS
    )

    return {
        "docs_url": (
            "/docs"
            if docs_enabled
            else None
        ),
        "redoc_url": (
            "/redoc"
            if docs_enabled
            else None
        ),
        "openapi_url": (
            "/openapi.json"
            if docs_enabled
            else None
        ),
    }