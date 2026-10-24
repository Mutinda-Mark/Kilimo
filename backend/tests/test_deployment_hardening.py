import pytest

from httpx import (
    ASGITransport,
    AsyncClient,
)

from app import main as main_module
from app.security.deployment import (
    api_documentation_urls,
)

def documentation_urls(
    environment: str,
):
    is_production = (
        environment
        .strip()
        .lower()
        == "production"
    )

    return {
        "docs_url": (
            None
            if is_production
            else "/docs"
        ),
        "redoc_url": (
            None
            if is_production
            else "/redoc"
        ),
        "openapi_url": (
            None
            if is_production
            else "/openapi.json"
        ),
    }


def test_development_keeps_api_docs_enabled():
    urls = documentation_urls(
        "development"
    )

    assert urls == {
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "openapi_url": "/openapi.json",
    }


def test_production_disables_api_docs():
    urls = documentation_urls(
        "production"
    )

    assert urls == {
        "docs_url": None,
        "redoc_url": None,
        "openapi_url": None,
    }

def test_unknown_environment_disables_api_docs():

    urls = api_documentation_urls(
        "unknown"
    )

    assert urls == {
        "docs_url": None,
        "redoc_url": None,
        "openapi_url": None,
    }


def test_empty_environment_disables_api_docs():

    urls = api_documentation_urls(
        ""
    )

    assert urls == {
        "docs_url": None,
        "redoc_url": None,
        "openapi_url": None,
    }

@pytest.mark.asyncio
async def test_health_returns_minimal_response(
    monkeypatch,
):
    class FakeConnection:
        async def fetchval(
            self,
            query,
        ):
            return 1


    class FakeAcquire:
        async def __aenter__(self):
            return FakeConnection()

        async def __aexit__(
            self,
            exc_type,
            exc,
            tb,
        ):
            return False


    class FakePool:
        def acquire(self):
            return FakeAcquire()


    async def fake_get_pool():
        return FakePool()


    monkeypatch.setattr(
        main_module,
        "get_pool",
        fake_get_pool,
    )

    transport = ASGITransport(
        app=main_module.app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.get(
            "/health"
        )

    assert response.status_code == 200

    assert response.json() == {
        "status": "ok"
    }


@pytest.mark.asyncio
async def test_health_does_not_expose_environment(
    monkeypatch,
):
    async def fake_get_pool():
        raise RuntimeError(
            "database unavailable"
        )


    monkeypatch.setattr(
        main_module,
        "get_pool",
        fake_get_pool,
    )

    transport = ASGITransport(
        app=main_module.app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.get(
            "/health"
        )

    assert response.status_code == 200

    body = response.json()

    assert body == {
        "status": "degraded"
    }

    assert "database" not in body
    assert "environment" not in body