"""
Tests for the FastAPI application.

Covers:
    - Root endpoint
    - Health endpoint
    - Prediction endpoint
    - Invalid uploads
    - Empty uploads
    - Invalid image data
"""

import io

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from tests.image_test_utils import create_valid_test_image_bytes
from nlp.advisory import AdvisoryEngine

advisory_engine = AdvisoryEngine()


client = TestClient(app)


# ---------------------------------------------------------------------------
# Test image helper
# ---------------------------------------------------------------------------

def create_test_image() -> bytes:
    """
    Create a technically valid synthetic JPEG image for API tests.

    The image contains sufficient edge detail to pass the
    Sprint III image-quality gate.
    """

    from tests.image_test_utils import (
        create_valid_test_image_bytes,
    )

    return create_valid_test_image_bytes(
        image_format="JPEG"
    )


# ---------------------------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------------------------

def test_root_endpoint():
    """GET / should return a successful response."""

    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert "message" in data
    assert "version" in data

    assert data["message"] == "Tomato Disease Advisory Backend"


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------

def test_health_endpoint():
    """GET /health should return the API health information."""

    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data
    assert "database" in data
    assert "environment" in data

    assert data["status"] in {
        "ok",
        "degraded",
    }


# ---------------------------------------------------------------------------
# Prediction endpoint
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Prediction endpoint
# ---------------------------------------------------------------------------

def test_predict_valid_image(supported_subject):
    """POST /predict should accept an image and return prediction, severity and advisory data."""

    image_bytes = create_test_image()

    response = client.post(
        "/predict",
        files={
            "file": (
                "tomato.jpg",
                image_bytes,
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    # Top-level sections
    assert "prediction" in data
    assert "severity" in data
    assert "advisory" in data

    prediction = data["prediction"]
    severity = data["severity"]
    advisory = data["advisory"]

    # Prediction fields
    assert "disease" in prediction
    assert "confidence" in prediction
    assert "label_index" in prediction
    assert "all_scores" in prediction

    # Severity fields
    assert "level" in severity
    assert "affected_area_percentage" in severity

    # Advisory fields
    assert "disease" in advisory
    assert "confidence" in advisory
    assert "severity" in advisory
    assert "description" in advisory
    assert "symptoms" in advisory
    assert "recommended_actions" in advisory
    assert "prevention" in advisory
    assert "confidence_message" in advisory
    assert "urgency" in advisory

    # Basic validation
    assert isinstance(prediction["disease"], str)

    assert 0.0 <= prediction["confidence"] <= 1.0

    assert isinstance(prediction["label_index"], int)

    assert isinstance(prediction["all_scores"], dict)

    assert len(prediction["all_scores"]) == 11

    assert isinstance(severity["level"], str)

    assert isinstance(
        severity["affected_area_percentage"],
        (int, float),
    )


# ---------------------------------------------------------------------------
# Prediction probability validation
# ---------------------------------------------------------------------------

def test_predict_probabilities_sum_to_one(supported_subject):
    """Prediction class probabilities should sum approximately to 1."""

    image_bytes = create_test_image()

    response = client.post(
        "/predict",
        files={
            "file": (
                "tomato.jpg",
                image_bytes,
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    scores = data["prediction"]["all_scores"]

    assert len(scores) == 11

    for score in scores.values():
        assert 0.0 <= score <= 1.0

    assert abs(sum(scores.values()) - 1.0) < 1e-3

# ---------------------------------------------------------------------------
# Invalid file type
# ---------------------------------------------------------------------------

def test_predict_rejects_non_image_file():
    """POST /predict should reject non-image uploads."""

    response = client.post(
        "/predict",
        files={
            "file": (
                "document.txt",
                b"This is not an image.",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert "detail" in data


# ---------------------------------------------------------------------------
# Empty image
# ---------------------------------------------------------------------------

def test_predict_rejects_empty_file():
    """POST /predict should reject an empty upload."""

    response = client.post(
        "/predict",
        files={
            "file": (
                "empty.jpg",
                b"",
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert "detail" in data


# ---------------------------------------------------------------------------
# Invalid image data
# ---------------------------------------------------------------------------

def test_predict_rejects_invalid_image():
    """POST /predict should reject corrupted image data."""

    response = client.post(
        "/predict",
        files={
            "file": (
                "fake.jpg",
                b"This is not really a JPEG image.",
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert "detail" in data

