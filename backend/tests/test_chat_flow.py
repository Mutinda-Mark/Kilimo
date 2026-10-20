import io

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from PIL import Image

from app.db import get_pool
from app.main import (
    app,
    chat_service,
    image_analysis_service,
)


PHONE_NUMBER = "254700000001"


def make_test_image() -> bytes:
    """
    Create a quality-gate-compatible PNG for chat-flow tests.
    """

    from tests.image_test_utils import (
        create_valid_test_image_bytes,
    )

    return create_valid_test_image_bytes(
        image_format="PNG"
    )


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
            DELETE FROM assessments
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
async def clean_chat_flow_data():
    await cleanup_test_data()

    yield

    await cleanup_test_data()


@pytest.mark.asyncio
async def test_complete_chat_flow(
    monkeypatch,
    supported_subject,
):
    """
    Test the complete farmer conversation flow:

    1. Submit an image through /predict.
    2. Verify the session is created.
    3. Ask follow-up questions.
    4. Verify stored assessment context is reused.
    5. Verify conversation history.
    """

    # ---------------------------------------------------------
    # Fake CV assessment
    # ---------------------------------------------------------

    class FakeAssessment:
        def to_dict(self):
            return {
                "disease": "Bacterial Spot",
                "confidence": 0.9906,
                "label_index": 0,
                "all_scores": {
                    "Bacterial Spot": 0.9906,
                    "Early Blight": 0.0,
                    "Late Blight": 0.0,
                    "Leaf Mold": 0.0,
                    "Septoria Leaf Spot": 0.0094,
                    "Spider Mites / Two-Spotted Spider Mite": 0.0,
                    "Target Spot": 0.0,
                    "Tomato Yellow Leaf Curl Virus": 0.0,
                    "Tomato Mosaic Virus": 0.0,
                    "Healthy": 0.0,
                    "Powdery Mildew": 0.0,
                },
                "severity_level": "High",
                "affected_area_percentage": 38.2,
            }

    def fake_assess(image):
        return FakeAssessment()

    # ---------------------------------------------------------
    # Fake structured advisory
    # ---------------------------------------------------------

    def fake_advisory_generate(
        assessment,
    ):
        return {
            "disease": "Bacterial Spot",
            "confidence": 0.9906,
            "severity": "High",
            "affected_area_percentage": 38.2,
            "description": (
                "A bacterial disease affecting tomato plants."
            ),
            "symptoms": [
                "Small dark spots on leaves",
                "Yellowing around some leaf spots",
            ],
            "recommended_actions": [
                "Remove badly affected plant material.",
                "Avoid working with wet foliage.",
            ],
            "prevention": [
                "Use clean planting material.",
                "Avoid overhead irrigation.",
            ],
            "confidence_message": (
                "The model is highly confident."
            ),
            "urgency": "High",
        }

    # ---------------------------------------------------------
    # Fake natural-language responder
    # ---------------------------------------------------------

    async def fake_responder_generate(
        advisory,
        farmer_query=None,
        conversation_history=None,
        session_context=None,
        **kwargs,
    ):
        if farmer_query:

            question = farmer_query.lower()

            if "prevent" in question:
                return (
                    "To prevent Bacterial Spot from spreading, "
                    "remove affected plant material and avoid "
                    "working with wet foliage."
                )

            if "serious" in question:
                return (
                    "The condition is currently assessed as "
                    "High severity, affecting about 38.2% "
                    "of the leaf area."
                )

            return (
                "The system detected Bacterial Spot "
                "with high confidence."
            )

        return (
            "The system detected Bacterial Spot "
            "with high confidence."
        )

    # ---------------------------------------------------------
    # Patch dependencies actually used by services
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

    # /chat uses ChatService's own stored responder reference.
    monkeypatch.setattr(
        chat_service.advisory_responder,
        "generate",
        fake_responder_generate,
    )

    # ---------------------------------------------------------
    # API requests
    # ---------------------------------------------------------

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        # =====================================================
        # 1. Initial prediction
        # =====================================================

        response = await client.post(
            "/predict",
            files={
                "file": (
                    "tomato.png",
                    make_test_image(),
                    "image/png",
                )
            },
            data={
                "phone_number": PHONE_NUMBER,
                "question": (
                    "What disease is affecting my tomatoes?"
                ),
            },
        )

        assert response.status_code == 200

        predict_result = response.json()

        assert (
            predict_result["prediction"]["disease"]
            == "Bacterial Spot"
        )

        assert (
            predict_result["prediction"]["confidence"]
            == pytest.approx(0.9906)
        )

        assert (
            predict_result["severity"]["level"]
            == "High"
        )

        assert (
            predict_result["severity"][
                "affected_area_percentage"
            ]
            == pytest.approx(38.2)
        )

        assert (
            predict_result["session"]["phone_number"]
            == PHONE_NUMBER
        )

        # =====================================================
        # 2. First follow-up
        # =====================================================

        response = await client.post(
            "/chat",
            json={
                "phone_number": PHONE_NUMBER,
                "question": "What should I do about it?",
            },
        )

        assert response.status_code == 200

        chat_result = response.json()

        assert chat_result["response"]

        assert (
            chat_result["context"]["last_assessment"]["disease"]
            == "Bacterial Spot"
        )

        assert (
            chat_result["context"]["last_assessment"]["severity"]
            == "High"
        )

        assert (
            chat_result["context"]["last_assessment"][
                "affected_area_percentage"
            ]
            == pytest.approx(38.2)
        )

        assert (
            chat_result["context"]["last_assessment"]["confidence"]
            == pytest.approx(0.9906)
        )

        # =====================================================
        # 3. Prevention follow-up
        # =====================================================

        response = await client.post(
            "/chat",
            json={
                "phone_number": PHONE_NUMBER,
                "question": (
                    "How can I prevent it from spreading?"
                ),
            },
        )

        assert response.status_code == 200

        chat_result = response.json()

        assert (
            "Bacterial Spot"
            in chat_result["response"]
        )

        # =====================================================
        # 4. Severity follow-up
        # =====================================================

        response = await client.post(
            "/chat",
            json={
                "phone_number": PHONE_NUMBER,
                "question": "Is the condition serious?",
            },
        )

        assert response.status_code == 200

        chat_result = response.json()

        assert (
            "High severity"
            in chat_result["response"]
        )

        # =====================================================
        # 5. Conversation history
        # =====================================================

        response = await client.get(
            f"/sessions/{PHONE_NUMBER}/history"
        )

        assert response.status_code == 200

        history_result = response.json()
        history = history_result["history"]

        assert history_result["count"] == 9

        assert history[0]["role"] == "farmer"
        assert history[0]["message_type"] == "image"

        assert history[1]["role"] == "farmer"
        assert history[1]["message_type"] == "text"

        assert history[2]["role"] == "system"
        assert history[2]["message_type"] == "text"

        assert history[3]["role"] == "farmer"
        assert (
            history[3]["content"]
            == "What should I do about it?"
        )

        assert history[4]["role"] == "system"

        assert history[5]["role"] == "farmer"
        assert (
            history[5]["content"]
            == "How can I prevent it from spreading?"
        )

        assert history[6]["role"] == "system"

        assert history[7]["role"] == "farmer"
        assert (
            history[7]["content"]
            == "Is the condition serious?"
        )

        assert history[8]["role"] == "system"