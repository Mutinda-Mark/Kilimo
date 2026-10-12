import pytest
import pytest_asyncio

from httpx import ASGITransport, AsyncClient

from app.main import app, chat_service
from app.db import get_pool


PHONE_NUMBER = "254700000002"


async def cleanup_test_data():
    """Remove records created by this test module."""

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


async def fake_responder_generate(**kwargs):
    """
    Deterministic replacement for Gemini.

    These tests should not depend on:
    - Gemini availability
    - external API latency
    - generated wording
    """

    advisory = kwargs.get(
        "advisory",
        {},
    )

    disease = advisory.get(
        "disease",
        "Unknown",
    )

    if disease == "Unknown":
        return (
            "I can help with tomato farming questions. "
            "Send a clear tomato leaf image if you want "
            "a disease assessment."
        )

    return (
        f"The previous assessment was {disease}."
    )


@pytest_asyncio.fixture(
    autouse=True
)
async def clean_test_session():
    """
    Ensure every test starts and ends with a clean farmer session.
    """

    await cleanup_test_data()

    yield

    await cleanup_test_data()


@pytest.mark.asyncio
async def test_chat_rejects_empty_phone_number():
    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.post(
            "/chat",
            json={
                "phone_number": "",
                "question": "What should I do?",
            },
        )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Phone number is required."
    )


@pytest.mark.asyncio
async def test_chat_rejects_empty_question():
    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.post(
            "/chat",
            json={
                "phone_number": PHONE_NUMBER,
                "question": "",
            },
        )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Question cannot be empty."
    )


@pytest.mark.asyncio
async def test_chat_creates_session_for_new_farmer(
    monkeypatch,
):
    """
    Current KILIMO behavior:

    A new farmer may chat before having a previous session.
    ChatService should create the session automatically.
    """

    monkeypatch.setattr(
        chat_service.advisory_responder,
        "generate",
        fake_responder_generate,
    )

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.post(
            "/chat",
            json={
                "phone_number": PHONE_NUMBER,
                "question": (
                    "What can you help me with?"
                ),
            },
        )

    assert response.status_code == 200

    body = response.json()

    assert "response" in body

    assert (
        "tomato farming"
        in body["response"].lower()
    )

    pool = await get_pool()

    async with pool.acquire() as conn:
        session = await conn.fetchrow(
            """
            SELECT
                phone_number,
                last_disease,
                last_severity,
                last_confidence
            FROM sessions
            WHERE phone_number = $1
            """,
            PHONE_NUMBER,
        )

    assert session is not None

    assert (
        session["phone_number"]
        == PHONE_NUMBER
    )

    assert session[
        "last_disease"
    ] is None

    assert session[
        "last_severity"
    ] is None

    assert session[
        "last_confidence"
    ] is None


@pytest.mark.asyncio
async def test_chat_allows_session_without_assessment(
    monkeypatch,
):
    """
    A farmer may ask general tomato questions before
    uploading an image.
    """

    monkeypatch.setattr(
        chat_service.advisory_responder,
        "generate",
        fake_responder_generate,
    )

    pool = await get_pool()

    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO sessions (
                phone_number
            )
            VALUES ($1)
            """,
            PHONE_NUMBER,
        )

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.post(
            "/chat",
            json={
                "phone_number": PHONE_NUMBER,
                "question": (
                    "How can KILIMO help me?"
                ),
            },
        )

    assert response.status_code == 200

    body = response.json()

    assert "response" in body

    assert (
        "tomato farming"
        in body["response"].lower()
    )

    async with pool.acquire() as conn:
        session = await conn.fetchrow(
            """
            SELECT
                last_disease,
                last_severity,
                last_confidence
            FROM sessions
            WHERE phone_number = $1
            """,
            PHONE_NUMBER,
        )

    assert session is not None

    assert session[
        "last_disease"
    ] is None

    assert session[
        "last_severity"
    ] is None

    assert session[
        "last_confidence"
    ] is None