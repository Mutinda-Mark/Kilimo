from io import BytesIO

from PIL import Image
from fastapi.testclient import TestClient

import app.main as main


def create_test_image() -> bytes:
    """
    Create a simple RGB image for API testing.
    """

    image = Image.new(
        "RGB",
        (224, 224),
        color=(120, 180, 80),
    )

    buffer = BytesIO()

    image.save(
        buffer,
        format="PNG",
    )

    return buffer.getvalue()


def test_predict_returns_gemini_response(monkeypatch):
    """
    Verify that /predict returns the structured assessment
    together with the natural-language advisory response.
    """

    async def fake_generate(
        advisory,
        farmer_query=None,
        conversation_history=None,
        session_context=None,
    ):
        assert advisory["disease"] == "Early Blight"

        # No phone_number was supplied, so context should be absent.
        assert conversation_history is None
        assert session_context is None

        return (
            "The system detected Early Blight. "
            "Remove affected leaves and improve airflow."
        )

    monkeypatch.setattr(
        main.advisory_responder,
        "generate",
        fake_generate,
    )

    class FakeAssessment:
        def to_dict(self):
            return {
                "disease": "Early Blight",
                "confidence": 0.98,
                "label_index": 1,
                "affected_area_percentage": 18.5,
                "severity_level": "Moderate",
                "leaf_pixels": 10000,
                "affected_pixels": 1850,
                "activation_threshold": 0.5,
                "all_scores": {
                    "Bacterial Spot": 0.001,
                    "Early Blight": 0.98,
                    "Late Blight": 0.005,
                    "Leaf Mold": 0.001,
                    "Septoria Leaf Spot": 0.001,
                    "Spider Mites / Two-Spotted Spider Mite": 0.001,
                    "Target Spot": 0.001,
                    "Tomato Yellow Leaf Curl Virus": 0.001,
                    "Tomato Mosaic Virus": 0.001,
                    "Healthy": 0.007,
                    "Powdery Mildew": 0.001,
                },
            }

    def fake_assess(image):
        return FakeAssessment()

    monkeypatch.setattr(
        main.assessor,
        "assess",
        fake_assess,
    )

    client = TestClient(main.app)

    response = client.post(
        "/predict",
        files={
            "file": (
                "tomato.png",
                create_test_image(),
                "image/png",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "prediction" in data
    assert "severity" in data
    assert "advisory" in data
    assert "response" in data

    assert data["prediction"]["disease"] == "Early Blight"
    assert data["prediction"]["confidence"] == 0.98

    assert data["severity"]["level"] == "Moderate"

    assert (
        data["advisory"]["disease"]
        == "Early Blight"
    )

    assert (
        data["response"]
        == (
            "The system detected Early Blight. "
            "Remove affected leaves and improve airflow."
        )
    )


def test_predict_passes_farmer_question_to_responder(
    monkeypatch,
):
    """
    Verify that an optional farmer question reaches
    AdvisoryResponder.
    """

    received_question = {}

    async def fake_generate(
        advisory,
        farmer_query=None,
        conversation_history=None,
        session_context=None,
    ):
        received_question["value"] = farmer_query

        # No phone_number was supplied, so context should be absent.
        assert conversation_history is None
        assert session_context is None

        return "Farmer-friendly advisory."

    monkeypatch.setattr(
        main.advisory_responder,
        "generate",
        fake_generate,
    )

    class FakeAssessment:
        def to_dict(self):
            return {
                "disease": "Late Blight",
                "confidence": 0.95,
                "label_index": 2,
                "affected_area_percentage": 20.0,
                "severity_level": "Moderate",
                "leaf_pixels": 10000,
                "affected_pixels": 2000,
                "activation_threshold": 0.5,
                "all_scores": {
                    "Bacterial Spot": 0.001,
                    "Early Blight": 0.001,
                    "Late Blight": 0.95,
                    "Leaf Mold": 0.001,
                    "Septoria Leaf Spot": 0.001,
                    "Spider Mites / Two-Spotted Spider Mite": 0.001,
                    "Target Spot": 0.001,
                    "Tomato Yellow Leaf Curl Virus": 0.001,
                    "Tomato Mosaic Virus": 0.001,
                    "Healthy": 0.007,
                    "Powdery Mildew": 0.001,
                },
            }

    monkeypatch.setattr(
        main.assessor,
        "assess",
        lambda image: FakeAssessment(),
    )

    client = TestClient(main.app)

    question = (
        "What can I do to stop this from spreading?"
    )

    response = client.post(
        "/predict",
        data={
            "question": question,
        },
        files={
            "file": (
                "tomato.png",
                create_test_image(),
                "image/png",
            )
        },
    )

    assert response.status_code == 200

    assert (
        received_question["value"]
        == question
    )


    assert (
        response.json()["response"]
        == "Farmer-friendly advisory."
    )

def test_predict_passes_session_context_to_responder(monkeypatch):
    """
    Verify that a farmer's previous conversation and session context
    are retrieved and passed to AdvisoryResponder.
    """

    received = {}

    async def fake_generate(
        advisory,
        farmer_query=None,
        conversation_history=None,
        session_context=None,
    ):
        received["question"] = farmer_query
        received["history"] = conversation_history
        received["session_context"] = session_context

        return "Based on your previous diagnosis, continue monitoring the affected leaves."

    monkeypatch.setattr(
        main.advisory_responder,
        "generate",
        fake_generate,
    )

    class FakeAssessment:
        def to_dict(self):
            return {
                "disease": "Early Blight",
                "confidence": 0.96,
                "label_index": 1,
                "affected_area_percentage": 22.0,
                "severity_level": "Moderate",
                "leaf_pixels": 10000,
                "affected_pixels": 2200,
                "activation_threshold": 0.5,
                "all_scores": {
                    "Bacterial Spot": 0.001,
                    "Early Blight": 0.96,
                    "Late Blight": 0.005,
                    "Leaf Mold": 0.001,
                    "Septoria Leaf Spot": 0.001,
                    "Spider Mites / Two-Spotted Spider Mite": 0.001,
                    "Target Spot": 0.001,
                    "Tomato Yellow Leaf Curl Virus": 0.001,
                    "Tomato Mosaic Virus": 0.001,
                    "Healthy": 0.025,
                    "Powdery Mildew": 0.001,
                },
            }

    monkeypatch.setattr(
        main.assessor,
        "assess",
        lambda image: FakeAssessment(),
    )

    # Simulated existing farmer session
    fake_session = {
        "phone_number": "254700000001",
        "language": "en",
        "last_disease": "Early Blight",
        "last_severity": "Moderate",
        "last_confidence": 0.96,
        "context": {
            "last_assessment": {
                "disease": "Early Blight",
                "severity": "Moderate",
                "affected_area_percentage": 22.0,
            }
        },
    }

    fake_history = [
        {
            "id": 1,
            "phone_number": "254700000001",
            "role": "farmer",
            "message_type": "image",
            "content": "tomato.png",
        },
        {
            "id": 2,
            "phone_number": "254700000001",
            "role": "farmer",
            "message_type": "text",
            "content": "What can I do to stop this from spreading?",
        },
        {
            "id": 3,
            "phone_number": "254700000001",
            "role": "system",
            "message_type": "text",
            "content": "The system detected Early Blight.",
        },
    ]

    async def fake_get_or_create_session(phone_number):
        assert phone_number == "254700000001"
        return fake_session

    async def fake_get_session(phone_number):
        assert phone_number == "254700000001"
        return fake_session

    async def fake_get_history(phone_number, limit=10):
        assert phone_number == "254700000001"
        assert limit == 10
        return fake_history

    async def fake_save_message(
        phone_number,
        *,
        role,
        message_type,
        content=None,
    ):
        return {
            "phone_number": phone_number,
            "role": role,
            "message_type": message_type,
            "content": content,
        }

    async def fake_update_session(
        phone_number,
        *,
        disease=None,
        severity=None,
        confidence=None,
        context=None,
    ):
        return fake_session

    monkeypatch.setattr(
        main.session_service,
        "get_or_create_session",
        fake_get_or_create_session,
    )

    monkeypatch.setattr(
        main.session_service,
        "get_session",
        fake_get_session,
    )

    monkeypatch.setattr(
        main.session_service,
        "get_history",
        fake_get_history,
    )

    monkeypatch.setattr(
        main.session_service,
        "save_message",
        fake_save_message,
    )

    monkeypatch.setattr(
        main.session_service,
        "update_session",
        fake_update_session,
    )

    client = TestClient(main.app)

    question = "Will it spread to my other tomato plants?"

    response = client.post(
        "/predict",
        data={
            "question": question,
            "phone_number": "254700000001",
        },
        files={
            "file": (
                "tomato.png",
                create_test_image(),
                "image/png",
            )
        },
    )

    assert response.status_code == 200

    # Verify the current question reached the responder.
    assert received["question"] == question

    # Verify previous conversation reached the responder.
    assert received["history"] == fake_history

    # Verify the previous assessment/session context reached the responder.
    assert received["session_context"] == fake_session["context"]

    # Verify the endpoint still returned the response normally.
    assert (
        response.json()["response"]
        == "Based on your previous diagnosis, continue monitoring the affected leaves."
    )

    # Verify the session was actually enabled.
    assert response.json()["session"]["enabled"] is True

    assert (
        response.json()["session"]["phone_number"]
        == "254700000001"
    )