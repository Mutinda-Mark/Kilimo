from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.session_service import SessionService


def make_fake_pool(fake_conn):
    """
    Create a mock asyncpg pool.

    asyncpg uses:
        async with pool.acquire() as conn:

    Therefore acquire() itself must return an async context
    manager rather than an AsyncMock coroutine.
    """
    fake_pool = MagicMock()

    context_manager = MagicMock()
    context_manager.__aenter__ = AsyncMock(return_value=fake_conn)
    context_manager.__aexit__ = AsyncMock(return_value=None)

    fake_pool.acquire.return_value = context_manager

    return fake_pool


@pytest.mark.asyncio
async def test_get_session_returns_existing_session():
    service = SessionService()

    fake_row = {
        "phone_number": "254700000000",
        "language": "en",
        "last_disease": "Early Blight",
        "last_severity": "Severe",
        "last_confidence": 0.98,
        "context": {},
        "last_active_at": None,
    }

    fake_conn = AsyncMock()
    fake_conn.fetchrow.return_value = fake_row

    fake_pool = make_fake_pool(fake_conn)

    with patch(
        "app.services.session_service.get_pool",
        new=AsyncMock(return_value=fake_pool),
    ):
        result = await service.get_session("254700000000")

    assert result == fake_row
    fake_conn.fetchrow.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_session_returns_none_when_missing():
    service = SessionService()

    fake_conn = AsyncMock()
    fake_conn.fetchrow.return_value = None

    fake_pool = make_fake_pool(fake_conn)

    with patch(
        "app.services.session_service.get_pool",
        new=AsyncMock(return_value=fake_pool),
    ):
        result = await service.get_session("254700000000")

    assert result is None


@pytest.mark.asyncio
async def test_create_session():
    service = SessionService()

    fake_row = {
        "phone_number": "254700000000",
        "language": "en",
        "last_disease": None,
        "last_severity": None,
        "last_confidence": None,
        "context": {},
        "last_active_at": None,
    }

    fake_conn = AsyncMock()
    fake_conn.fetchrow.return_value = fake_row

    fake_pool = make_fake_pool(fake_conn)

    with patch(
        "app.services.session_service.get_pool",
        new=AsyncMock(return_value=fake_pool),
    ):
        result = await service.create_session("254700000000")

    assert result["phone_number"] == "254700000000"
    assert result["language"] == "en"

    fake_conn.fetchrow.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_session():
    service = SessionService()

    fake_row = {
        "phone_number": "254700000000",
        "language": "en",
        "last_disease": "Early Blight",
        "last_severity": "Severe",
        "last_confidence": 0.99,
        "context": {"source": "camera"},
        "last_active_at": None,
    }

    fake_conn = AsyncMock()
    fake_conn.fetchrow.return_value = fake_row

    fake_pool = make_fake_pool(fake_conn)

    with patch(
        "app.services.session_service.get_pool",
        new=AsyncMock(return_value=fake_pool),
    ):
        result = await service.update_session(
            "254700000000",
            disease="Early Blight",
            severity="Severe",
            confidence=0.99,
            context={"source": "camera"},
        )

    assert result["last_disease"] == "Early Blight"
    assert result["last_severity"] == "Severe"
    assert result["last_confidence"] == 0.99


@pytest.mark.asyncio
async def test_save_message():
    service = SessionService()

    fake_row = {
        "id": 1,
        "phone_number": "254700000000",
        "role": "farmer",
        "message_type": "text",
        "content": "What should I do?",
        "created_at": None,
    }

    fake_conn = AsyncMock()
    fake_conn.fetchrow.return_value = fake_row

    fake_pool = make_fake_pool(fake_conn)

    with patch(
        "app.services.session_service.get_pool",
        new=AsyncMock(return_value=fake_pool),
    ):
        result = await service.save_message(
            "254700000000",
            role="farmer",
            message_type="text",
            content="What should I do?",
        )

    assert result["role"] == "farmer"
    assert result["message_type"] == "text"
    assert result["content"] == "What should I do?"


@pytest.mark.asyncio
async def test_get_history_returns_oldest_first():
    service = SessionService()

    fake_rows = [
        {
            "id": 3,
            "phone_number": "254700000000",
            "role": "system",
            "message_type": "text",
            "content": "Here is your advice.",
            "created_at": None,
        },
        {
            "id": 2,
            "phone_number": "254700000000",
            "role": "farmer",
            "message_type": "text",
            "content": "What should I do?",
            "created_at": None,
        },
        {
            "id": 1,
            "phone_number": "254700000000",
            "role": "farmer",
            "message_type": "image",
            "content": None,
            "created_at": None,
        },
    ]

    fake_conn = AsyncMock()
    fake_conn.fetch.return_value = fake_rows

    fake_pool = make_fake_pool(fake_conn)

    with patch(
        "app.services.session_service.get_pool",
        new=AsyncMock(return_value=fake_pool),
    ):
        result = await service.get_history("254700000000")

    assert len(result) == 3

    # The service converts newest-first database results
    # into normal chronological conversation order.
    assert result[0]["id"] == 1
    assert result[1]["id"] == 2
    assert result[2]["id"] == 3


@pytest.mark.asyncio
async def test_get_or_create_session_uses_existing_session():
    service = SessionService()

    existing = {
        "phone_number": "254700000000",
        "language": "en",
        "last_disease": "Early Blight",
        "last_severity": "Severe",
        "last_confidence": 0.99,
        "context": {},
        "last_active_at": None,
    }

    with patch.object(
        service,
        "get_session",
        new=AsyncMock(return_value=existing),
    ) as get_session:
        with patch.object(
            service,
            "create_session",
            new=AsyncMock(),
        ) as create_session:
            result = await service.get_or_create_session(
                "254700000000"
            )

    assert result == existing
    get_session.assert_awaited_once_with("254700000000")
    create_session.assert_not_awaited()


def test_phone_number_cannot_be_empty():
    service = SessionService()

    with pytest.raises(ValueError):
        service._validate_phone_number("")


@pytest.mark.asyncio
async def test_text_message_requires_content():
    service = SessionService()

    with pytest.raises(ValueError):
        await service.save_message(
            "254700000000",
            role="farmer",
            message_type="text",
            content="",
        )