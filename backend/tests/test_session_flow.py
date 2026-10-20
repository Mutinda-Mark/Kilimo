import io

import pytest
import pytest_asyncio

import json
from httpx import ASGITransport, AsyncClient
from PIL import Image

from app.db import get_pool
from app.main import (
    app,
    image_analysis_service,
    settings,
)


TEST_PHONE = "254700000003"

TEST_ADMIN_TOKEN = (
    "test-admin-api-token"
)


def make_test_image() -> bytes:
    """
    Create a technically valid JPEG for session-flow tests.
    """

    from tests.image_test_utils import (
        create_valid_test_image_bytes,
    )

    return create_valid_test_image_bytes(
        image_format="JPEG"
    )


async def cleanup_test_data():
    pool = await get_pool()

    async with pool.acquire() as conn:
        await conn.execute(
            """
            DELETE FROM conversation_history
            WHERE phone_number = $1
            """,
            TEST_PHONE,
        )

        await conn.execute(
            """
            DELETE FROM assessments
            WHERE phone_number = $1
            """,
            TEST_PHONE,
        )

        await conn.execute(
            """
            DELETE FROM sessions
            WHERE phone_number = $1
            """,
            TEST_PHONE,
        )


@pytest_asyncio.fixture(
    autouse=True
)
async def clean_session_flow_data():
    await cleanup_test_data()

    yield

    await cleanup_test_data()


@pytest.mark.asyncio
async def test_complete_session_flow(
    monkeypatch,
    supported_subject,
):
    monkeypatch.setattr(
        settings,
        "admin_api_token",
        TEST_ADMIN_TOKEN,
    )
    # ---------------------------------------------------------
    # Fake CV assessment
    # ---------------------------------------------------------

    class FakeAssessment:
        def to_dict(self):
            return {
                "disease": "Early Blight",
                "confidence": 0.95,
                "label_index": 1,
                "all_scores": {
                    "Bacterial Spot": 0.01,
                    "Early Blight": 0.95,
                    "Late Blight": 0.01,
                    "Leaf Mold": 0.005,
                    "Septoria Leaf Spot": 0.005,
                    "Spider Mites / Two-Spotted Spider Mite": 0.005,
                    "Target Spot": 0.003,
                    "Tomato Yellow Leaf Curl Virus": 0.003,
                    "Tomato Mosaic Virus": 0.001,
                    "Healthy": 0.002,
                    "Powdery Mildew": 0.005,
                },
                "severity_level": "Moderate",
                "affected_area_percentage": 25.0,
            }

    def fake_assess(image):
        return FakeAssessment()

    # ---------------------------------------------------------
    # Fake advisory
    # ---------------------------------------------------------

    def fake_advisory_generate(
        assessment_data,
    ):
        return {
            "disease": (
                assessment_data["disease"]
            ),
            "confidence": (
                assessment_data["confidence"]
            ),
            "severity": (
                assessment_data["severity_level"]
            ),
            "affected_area_percentage": (
                assessment_data[
                    "affected_area_percentage"
                ]
            ),
            "urgency": "Medium",
            "description": "Test advisory.",
            "symptoms": [
                "Test symptom"
            ],
            "recommended_actions": [
                "Test action"
            ],
            "prevention": [
                "Test prevention"
            ],
            "confidence_message": (
                "Test confidence message."
            ),
        }

    # ---------------------------------------------------------
    # Fake responder
    # ---------------------------------------------------------

    async def fake_responder_generate(
        advisory,
        farmer_query=None,
        conversation_history=None,
        session_context=None,
        **kwargs,
    ):
        return (
            "Test response: Early Blight was detected. "
            "Please monitor the affected leaves."
        )

    # ---------------------------------------------------------
    # Patch actual ImageAnalysisService dependencies
    # ---------------------------------------------------------

    monkeypatch.setattr(
        image_analysis_service.assessor,
        "assess",
        fake_assess,
    )

    monkeypatch.setattr(
        image_analysis_service.advisory_engine,
        "generate",
        fake_advisory_generate,
    )

    monkeypatch.setattr(
        image_analysis_service.advisory_responder,
        "generate",
        fake_responder_generate,
    )

    # ---------------------------------------------------------
    # POST /predict
    # ---------------------------------------------------------

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
                    make_test_image(),
                    "image/jpeg",
                )
            },
            data={
                "phone_number": TEST_PHONE,
                "question": (
                    "What should I do about this disease?"
                ),
            },
        )

        assert response.status_code == 200

        result = response.json()

        assert (
            result["prediction"]["disease"]
            == "Early Blight"
        )

        assert (
            result["prediction"]["confidence"]
            == pytest.approx(0.95)
        )

        assert (
            result["severity"]["level"]
            == "Moderate"
        )

        assert (
            result["severity"][
                "affected_area_percentage"
            ]
            == pytest.approx(25.0)
        )

        assert (
            result["session"]["phone_number"]
            == TEST_PHONE
        )

        assert (
            result["session"]["enabled"]
            is True
        )

        assert (
            "Early Blight"
            in result["response"]
        )

        # -----------------------------------------------------
        # GET conversation history
        # -----------------------------------------------------

        history_response = await client.get(
            f"/admin/sessions/{TEST_PHONE}/history",
            headers = {
                "Authorization": (
                    f"Bearer {TEST_ADMIN_TOKEN}"
                )
            }
        )

        assert (
            history_response.status_code
            == 200
        )

        history_result = (
            history_response.json()
        )

        assert (
            history_result["phone_number"]
            == TEST_PHONE
        )

        assert (
            history_result["count"]
            == 3
        )

        history = history_result["history"]

        assert (
            history[0]["role"]
            == "farmer"
        )

        assert (
            history[0]["message_type"]
            == "image"
        )

        assert (
            history[1]["role"]
            == "farmer"
        )

        assert (
            history[1]["message_type"]
            == "text"
        )

        assert (
            history[2]["role"]
            == "system"
        )

        assert (
            history[2]["message_type"]
            == "text"
        )

        assert (
            "Early Blight"
            in history[2]["content"]
        )

    # ---------------------------------------------------------
    # Verify session directly
    # ---------------------------------------------------------

    pool = await get_pool()

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                phone_number,
                last_disease,
                last_severity,
                last_confidence,
                context
            FROM sessions
            WHERE phone_number = $1
            """,
            TEST_PHONE,
        )

    assert row is not None

    assert (
        row["phone_number"]
        == TEST_PHONE
    )

    assert (
        row["last_disease"]
        == "Early Blight"
    )

    assert (
        row["last_severity"]
        == "Moderate"
    )

    assert (
        float(
            row["last_confidence"]
        )
        == pytest.approx(0.95)
    )

    # ---------------------------------------------------------
    # Verify full assessment is preserved in context
    # ---------------------------------------------------------

    context = row["context"]

    if isinstance(context, str):
        context = json.loads(context)

    assert (
        context["last_assessment"]["disease"]
        == "Early Blight"
    )

    assert (
        context["last_assessment"]["severity"]
        == "Moderate"
    )

    assert (
        context["last_assessment"][
            "affected_area_percentage"
        ]
        == pytest.approx(25.0)
    )

    assert (
        context["last_assessment"]["confidence"]
        == pytest.approx(0.95)
    )