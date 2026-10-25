import pytest

from httpx import (
    ASGITransport,
    AsyncClient,
)

from app.db import get_pool
from app.main import (
    app,
    settings,
)


PHONE_NUMBER = (
    "254700000003"
)

TEST_ADMIN_TOKEN = (
    "test-admin-api-token"
)


def admin_headers() -> dict[str, str]:
    return {
        "Authorization": (
            f"Bearer "
            f"{TEST_ADMIN_TOKEN}"
        )
    }


async def cleanup_test_data():
    pool = await get_pool()

    async with pool.acquire() as conn:

        await conn.execute(
            """
            DELETE FROM conversation_history

            WHERE phone_number = $1
            """,
            PHONE_NUMBER,
        )

        await conn.execute(
            """
            DELETE FROM sessions

            WHERE phone_number = $1
            """,
            PHONE_NUMBER,
        )


@pytest.mark.asyncio
async def test_public_history_endpoint_is_removed():

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.get(
            (
                f"/sessions/"
                f"{PHONE_NUMBER}/history"
            )
        )

    assert (
        response.status_code
        == 404
    )


@pytest.mark.asyncio
async def test_admin_history_requires_authentication(
    monkeypatch,
):

    monkeypatch.setattr(
        settings,
        "admin_api_token",
        TEST_ADMIN_TOKEN,
    )

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.get(
            (
                f"/admin/sessions/"
                f"{PHONE_NUMBER}/history"
            )
        )

    assert (
        response.status_code
        == 401
    )

    assert (
        response.json()[
            "detail"
        ]
        == (
            "Admin authentication required."
        )
    )


@pytest.mark.asyncio
async def test_admin_history_rejects_invalid_token(
    monkeypatch,
):

    monkeypatch.setattr(
        settings,
        "admin_api_token",
        TEST_ADMIN_TOKEN,
    )

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.get(
            (
                f"/admin/sessions/"
                f"{PHONE_NUMBER}/history"
            ),
            headers={
                "Authorization":
                    "Bearer wrong-token",
            },
        )

    assert (
        response.status_code
        == 401
    )

    assert (
        response.json()[
            "detail"
        ]
        == "Invalid admin credentials."
    )


@pytest.mark.asyncio
async def test_admin_history_fails_closed_when_auth_not_configured(
    monkeypatch,
):

    monkeypatch.setattr(
        settings,
        "admin_api_token",
        "",
    )

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.get(
            (
                f"/admin/sessions/"
                f"{PHONE_NUMBER}/history"
            ),
            headers={
                "Authorization":
                    "Bearer anything",
            },
        )

    assert (
        response.status_code
        == 503
    )

    assert (
        response.json()[
            "detail"
        ]
        == (
            "Admin authentication "
            "is not configured."
        )
    )


@pytest.mark.asyncio
async def test_admin_history_rejects_zero_limit(
    monkeypatch,
):

    monkeypatch.setattr(
        settings,
        "admin_api_token",
        TEST_ADMIN_TOKEN,
    )

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.get(
            (
                f"/admin/sessions/"
                f"{PHONE_NUMBER}/history"
                "?limit=0"
            ),
            headers=admin_headers(),
        )

    assert (
        response.status_code
        == 422
    )


@pytest.mark.asyncio
async def test_admin_history_rejects_negative_limit(
    monkeypatch,
):

    monkeypatch.setattr(
        settings,
        "admin_api_token",
        TEST_ADMIN_TOKEN,
    )

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.get(
            (
                f"/admin/sessions/"
                f"{PHONE_NUMBER}/history"
                "?limit=-1"
            ),
            headers=admin_headers(),
        )

    assert (
        response.status_code
        == 422
    )


@pytest.mark.asyncio
async def test_admin_history_rejects_excessive_limit(
    monkeypatch,
):

    monkeypatch.setattr(
        settings,
        "admin_api_token",
        TEST_ADMIN_TOKEN,
    )

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.get(
            (
                f"/admin/sessions/"
                f"{PHONE_NUMBER}/history"
                "?limit=201"
            ),
            headers=admin_headers(),
        )

    assert (
        response.status_code
        == 422
    )


@pytest.mark.asyncio
async def test_admin_history_returns_empty_history_for_unknown_session(
    monkeypatch,
):

    monkeypatch.setattr(
        settings,
        "admin_api_token",
        TEST_ADMIN_TOKEN,
    )

    await cleanup_test_data()

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.get(
            (
                f"/admin/sessions/"
                f"{PHONE_NUMBER}/history"
            ),
            headers=admin_headers(),
        )

    assert (
        response.status_code
        == 200
    )

    data = response.json()

    assert (
        data["phone_number"]
        == PHONE_NUMBER
    )

    assert (
        data["count"]
        == 0
    )

    assert (
        data["history"]
        == []
    )