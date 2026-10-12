import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.db import get_pool


PHONE_NUMBER = "254700000003"


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
async def test_history_rejects_empty_phone_number():

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.get(
            "/sessions/   /history"
        )

    assert response.status_code == 400
    assert "Phone number cannot be empty" in response.json()["detail"]


@pytest.mark.asyncio
async def test_history_rejects_zero_limit():

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.get(
            f"/sessions/{PHONE_NUMBER}/history?limit=0"
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_history_rejects_negative_limit():

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.get(
            f"/sessions/{PHONE_NUMBER}/history?limit=-1"
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_history_rejects_excessive_limit():

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.get(
            f"/sessions/{PHONE_NUMBER}/history?limit=101"
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_history_returns_empty_history_for_unknown_session():

    await cleanup_test_data()

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.get(
            f"/sessions/{PHONE_NUMBER}/history"
        )

    assert response.status_code == 200

    data = response.json()

    assert data["phone_number"] == PHONE_NUMBER
    assert data["count"] == 0
    assert data["history"] == []