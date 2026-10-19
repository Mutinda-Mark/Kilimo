import io

import pytest
import pytest_asyncio

from httpx import ASGITransport, AsyncClient
from PIL import Image

from app.main import (
    app,
    advisory_engine,
    advisory_responder,
    assessor,
    assessment_service,
)
from app.db import get_pool
from tests.image_test_utils import create_valid_test_image_bytes

PHONE_NUMBER = "254700000004"


def create_test_image() -> bytes:
    """
    Create a technically valid PNG image.

    Failure-handling tests need an image that passes the quality
    gate so that the test can reach the deliberately mocked
    downstream failure.
    """

    from tests.image_test_utils import (
        create_valid_test_image_bytes,
    )

    return create_valid_test_image_bytes(
        image_format="PNG"
    )


async def cleanup_test_data():
    """Remove database records created for the chat test."""

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


@pytest_asyncio.fixture(
    autouse=True
)
async def clean_failure_test_data():
    """Keep the failure tests isolated."""

    await cleanup_test_data()

    yield

    await cleanup_test_data()


async def fake_save_assessment(
    **kwargs,
):
    """
    Prevent failure tests from inserting fake assessment
    records into the real test database.
    """

    return 999


def fake_assess(image):
    """Return a deterministic CV assessment."""

    class FakeAssessment:
        def to_dict(self):
            return {
                "disease": "Early Blight",
                "confidence": 0.95,
                "label_index": 1,
                "severity_level": "Moderate",
                "affected_area_percentage": 20.0,
                "all_scores": {
                    "Early Blight": 0.95,
                },
            }

    return FakeAssessment()


def fake_advisory_generate(
    assessment,
):
    """Return a deterministic structured advisory."""

    return {
        "disease": "Early Blight",
        "confidence": 0.95,
        "severity": "Moderate",
        "affected_area_percentage": 20.0,
        "description": "Test advisory",
        "symptoms": [],
        "recommended_actions": [],
        "prevention": [],
        "confidence_message": "Test confidence",
        "urgency": "Medium",
    }


@pytest.mark.asyncio
async def test_predict_handles_cv_failure(
    monkeypatch,
):
    """
    A CV exception should not expose internal details.

    /predict should return the stable public image-analysis
    error response.
    """

    def failing_assess(image):
        raise RuntimeError(
            "Simulated CV failure"
        )

    monkeypatch.setattr(
        assessor,
        "assess",
        failing_assess,
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
                    "tomato.png",
                    create_test_image(),
                    "image/png",
                )
            },
        )

    assert response.status_code == 500

    assert (
        response.json()["detail"]
        == "Could not complete tomato image assessment."
    )


@pytest.mark.asyncio
async def test_predict_handles_advisory_failure(
    monkeypatch,
):
    """
    Advisory-generation failures should return the same
    stable public image-analysis error.
    """

    def failing_generate(
        assessment,
    ):
        raise RuntimeError(
            "Simulated advisory failure"
        )

    monkeypatch.setattr(
        assessor,
        "assess",
        fake_assess,
    )

    monkeypatch.setattr(
        assessment_service,
        "save_assessment",
        fake_save_assessment,
    )

    monkeypatch.setattr(
        advisory_engine,
        "generate",
        failing_generate,
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
                    "tomato.png",
                    create_test_image(),
                    "image/png",
                )
            },
        )

    assert response.status_code == 500

    assert (
        response.json()["detail"]
        == "Could not complete tomato image assessment."
    )


@pytest.mark.asyncio
async def test_predict_handles_responder_failure(
    monkeypatch,
):
    """
    Natural-language generation failure should not leak
    responder/Gemini implementation details.
    """

    async def failing_generate(
        **kwargs,
    ):
        raise RuntimeError(
            "Simulated responder failure"
        )

    monkeypatch.setattr(
        assessor,
        "assess",
        fake_assess,
    )

    monkeypatch.setattr(
        assessment_service,
        "save_assessment",
        fake_save_assessment,
    )

    monkeypatch.setattr(
        advisory_engine,
        "generate",
        fake_advisory_generate,
    )

    monkeypatch.setattr(
        advisory_responder,
        "generate",
        failing_generate,
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
                    "tomato.png",
                    create_test_image(),
                    "image/png",
                )
            },
        )

    assert response.status_code == 500

    assert (
        response.json()["detail"]
        == "Could not complete tomato image assessment."
    )


@pytest.mark.asyncio
async def test_chat_handles_responder_failure(
    monkeypatch,
):
    """
    Chat responder failure should return the stable public
    chat error without exposing internal implementation details.
    """

    pool = await get_pool()

    async with pool.acquire() as conn:

        await conn.execute(
            """
            INSERT INTO sessions (
                phone_number,
                last_disease,
                last_severity,
                last_confidence,
                context
            )
            VALUES (
                $1,
                $2,
                $3,
                $4,
                $5::jsonb
            )
            """,
            PHONE_NUMBER,
            "Early Blight",
            "Moderate",
            0.95,
            """
            {
                "last_assessment": {
                    "disease": "Early Blight",
                    "confidence": 0.95,
                    "severity": "Moderate",
                    "affected_area_percentage": 20.0,
                    "description": "Test advisory",
                    "symptoms": [],
                    "recommended_actions": [],
                    "prevention": [],
                    "confidence_message": "Test confidence",
                    "urgency": "Medium"
                },

                "last_advisory": {
                    "disease": "Early Blight",
                    "confidence": 0.95,
                    "severity": "Moderate",
                    "affected_area_percentage": 20.0,
                    "description": "Test advisory",
                    "symptoms": [],
                    "recommended_actions": [],
                    "prevention": [],
                    "confidence_message": "Test confidence",
                    "urgency": "Medium"
                }
            }
            """,
        )

    async def failing_generate(
        **kwargs,
    ):
        raise RuntimeError(
            "Simulated chat responder failure"
        )

    monkeypatch.setattr(
        advisory_responder,
        "generate",
        failing_generate,
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
                "question": "What should I do?",
            },
        )

    assert response.status_code == 500

    assert (
        response.json()["detail"]
        == "Unable to process chat message."
    )