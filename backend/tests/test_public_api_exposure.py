import pytest

from httpx import (
    ASGITransport,
    AsyncClient,
)

from app.main import (
    app,
    settings,
)
from app.security.public_api import (
    direct_api_is_enabled,
)


def test_direct_api_enabled_in_development():

    assert (
        direct_api_is_enabled(
            "development"
        )
        is True
    )


def test_direct_api_enabled_in_testing():

    assert (
        direct_api_is_enabled(
            "testing"
        )
        is True
    )


def test_direct_api_disabled_in_production():

    assert (
        direct_api_is_enabled(
            "production"
        )
        is False
    )


def test_direct_api_fails_closed_for_unknown_environment():

    assert (
        direct_api_is_enabled(
            "unexpected-environment"
        )
        is False
    )


def test_direct_api_fails_closed_for_empty_environment():

    assert (
        direct_api_is_enabled(
            ""
        )
        is False
    )


@pytest.mark.asyncio
async def test_chat_is_disabled_in_production(
    monkeypatch,
):

    monkeypatch.setattr(
        settings,
        "environment",
        "production",
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
                "phone_number":
                    "254700000099",
                "question":
                    "How is my tomato plant?",
            },
        )

    assert (
        response.status_code
        == 404
    )

    assert (
        response.json()["detail"]
        == "Not Found"
    )


@pytest.mark.asyncio
async def test_predict_is_disabled_in_production(
    monkeypatch,
):

    monkeypatch.setattr(
        settings,
        "environment",
        "production",
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

        response = await client.post(
            "/predict",
            files={
                "file": (
                    "tomato.jpg",
                    image_bytes,
                    "image/jpeg",
                )
            },
        )

    assert (
        response.status_code
        == 404
    )

    assert (
        response.json()["detail"]
        == "Not Found"
    )