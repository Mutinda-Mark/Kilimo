import pytest

from httpx import (
    ASGITransport,
    AsyncClient,
)

import app.main as main_module

from app.main import app
from app.security.rate_limit import (
    InMemoryRateLimiter,
)


@pytest.mark.asyncio
async def test_chat_returns_429_after_rate_limit(
    monkeypatch,
):

    limiter = InMemoryRateLimiter(
        limit=2,
        window_seconds=60,
    )

    monkeypatch.setattr(
        main_module,
        "chat_rate_limiter",
        limiter,
    )

    calls = {
        "count": 0
    }

    async def fake_process_message(
        *,
        phone_number,
        question,
    ):
        calls["count"] += 1

        return {
            "response":
                "Test response.",
            "context": {},
        }

    monkeypatch.setattr(
        main_module.chat_service,
        "process_message",
        fake_process_message,
    )

    transport = ASGITransport(
        app=app
    )

    payload = {
        "phone_number":
            "254700000099",
        "question":
            "How is my tomato plant?",
    }

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        first = await client.post(
            "/chat",
            json=payload,
        )

        second = await client.post(
            "/chat",
            json=payload,
        )

        third = await client.post(
            "/chat",
            json=payload,
        )

    assert first.status_code == 200
    assert second.status_code == 200

    assert (
        third.status_code
        == 429
    )

    assert (
        "Retry-After"
        in third.headers
    )

    assert (
        calls["count"]
        == 2
    )


@pytest.mark.asyncio
async def test_predict_returns_429_before_image_processing(
    monkeypatch,
):

    limiter = InMemoryRateLimiter(
        limit=2,
        window_seconds=60,
    )

    monkeypatch.setattr(
        main_module,
        "predict_rate_limiter",
        limiter,
    )

    calls = {
        "count": 0
    }

    async def fake_process_image(
        *,
        image,
        phone_number=None,
        question=None,
        image_history_content=None,
        source="api",
        file_size_bytes=None,
        mime_type=None,
    ):
        calls["count"] += 1

        return {
            "status":
                "accepted"
        }

    monkeypatch.setattr(
        main_module.image_analysis_service,
        "process_image",
        fake_process_image,
    )

    from tests.image_test_utils import (
        create_valid_test_image_bytes,
    )

    image_bytes = (
        create_valid_test_image_bytes(
            image_format="JPEG"
        )
    )

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        async def send():
            return await client.post(
                "/predict",
                files={
                    "file": (
                        "tomato.jpg",
                        image_bytes,
                        "image/jpeg",
                    )
                },
            )

        first = await send()
        second = await send()
        third = await send()

    assert first.status_code == 200
    assert second.status_code == 200

    assert (
        third.status_code
        == 429
    )

    assert (
        "Retry-After"
        in third.headers
    )

    assert (
        calls["count"]
        == 2
    )


@pytest.mark.asyncio
async def test_predict_and_chat_have_independent_limits(
    monkeypatch,
):

    predict_limiter = (
        InMemoryRateLimiter(
            limit=1,
            window_seconds=60,
        )
    )

    chat_limiter = (
        InMemoryRateLimiter(
            limit=1,
            window_seconds=60,
        )
    )

    monkeypatch.setattr(
        main_module,
        "predict_rate_limiter",
        predict_limiter,
    )

    monkeypatch.setattr(
        main_module,
        "chat_rate_limiter",
        chat_limiter,
    )

    async def fake_chat(
        *,
        phone_number,
        question,
    ):
        return {
            "response":
                "Test response.",
            "context": {},
        }

    async def fake_image(
        *,
        image,
        phone_number=None,
        question=None,
        image_history_content=None,
        source="api",
        file_size_bytes=None,
        mime_type=None,
    ):
        return {
            "status":
                "accepted"
        }

    monkeypatch.setattr(
        main_module.chat_service,
        "process_message",
        fake_chat,
    )

    monkeypatch.setattr(
        main_module.image_analysis_service,
        "process_image",
        fake_image,
    )

    from tests.image_test_utils import (
        create_valid_test_image_bytes,
    )

    image_bytes = (
        create_valid_test_image_bytes(
            image_format="JPEG"
        )
    )

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        chat_response = (
            await client.post(
                "/chat",
                json={
                    "phone_number":
                        "254700000099",
                    "question":
                        "Test question",
                },
            )
        )

        predict_response = (
            await client.post(
                "/predict",
                files={
                    "file": (
                        "tomato.jpg",
                        image_bytes,
                        "image/jpeg",
                    )
                },
            )
        )

    assert (
        chat_response.status_code
        == 200
    )

    assert (
        predict_response.status_code
        == 200
    )