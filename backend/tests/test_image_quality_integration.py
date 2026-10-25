"""
Integration tests for the Sprint III image-quality gate.

These tests verify that image-quality rejection occurs before
subject validation, disease inference, and downstream advisory
processing.
"""

from unittest.mock import AsyncMock, Mock

import pytest
from PIL import Image

from app.services.image_analysis_service import (
    ImageAnalysisService,
)


def build_service():
    """
    Build ImageAnalysisService using mocked downstream
    dependencies.
    """

    assessor = Mock()

    subject_validator = Mock()

    advisory_engine = Mock()

    advisory_responder = Mock()

    advisory_responder.generate = (
        AsyncMock()
    )

    session_service = Mock()

    session_service.get_or_create_session = (
        AsyncMock()
    )

    session_service.save_message = (
        AsyncMock()
    )

    session_service.get_session = (
        AsyncMock()
    )

    session_service.get_history = (
        AsyncMock()
    )

    session_service.update_session = (
        AsyncMock()
    )

    assessment_service = Mock()

    assessment_service.save_assessment = (
        AsyncMock()
    )

    service = ImageAnalysisService(
        assessor=assessor,
        advisory_engine=advisory_engine,
        advisory_responder=advisory_responder,
        session_service=session_service,
        assessment_service=assessment_service,
        subject_validator=subject_validator,
    )

    return {
        "service":
            service,

        "assessor":
            assessor,

        "subject_validator":
            subject_validator,

        "advisory_engine":
            advisory_engine,

        "advisory_responder":
            advisory_responder,

        "session_service":
            session_service,

        "assessment_service":
            assessment_service,
    }


@pytest.mark.asyncio
async def test_rejected_image_does_not_call_assessor():
    """
    A technically unsuitable image must never reach either
    the subject validator or disease classifier.
    """

    dependencies = build_service()

    service = dependencies[
        "service"
    ]

    assessor = dependencies[
        "assessor"
    ]

    subject_validator = dependencies[
        "subject_validator"
    ]

    advisory_engine = dependencies[
        "advisory_engine"
    ]

    advisory_responder = dependencies[
        "advisory_responder"
    ]

    assessment_service = dependencies[
        "assessment_service"
    ]

    # Featureless image:
    # technically valid PIL input, but effectively no useful
    # edge detail.
    image = Image.new(
        "RGB",
        (
            512,
            512,
        ),
        color=(
            120,
            120,
            120,
        ),
    )

    result = await service.process_image(
        image=image,
        phone_number=None,
        source="api",
        mime_type="image/jpeg",
        file_size_bytes=100_000,
    )

    assert (
        result["status"]
        == "rejected"
    )

    assert (
        result["quality"]["reason"]
        == "blur"
    )

    assert (
        result["subject_validation"]
        is None
    )

    assert result["prediction"] is None
    assert result["severity"] is None
    assert result["assessment_id"] is None

    # Quality rejection occurs before subject validation.
    subject_validator.validate.assert_not_called()

    # It also occurs before disease inference.
    assessor.assess.assert_not_called()

    assessment_service.save_assessment.assert_not_awaited()

    advisory_engine.generate.assert_not_called()

    advisory_responder.generate.assert_not_awaited()


@pytest.mark.asyncio
async def test_rejected_image_returns_actionable_message():
    """
    A rejected image should produce actionable feedback
    rather than a generic server error.
    """

    dependencies = build_service()

    service = dependencies[
        "service"
    ]

    subject_validator = dependencies[
        "subject_validator"
    ]

    image = Image.new(
        "RGB",
        (
            512,
            512,
        ),
        color=(
            120,
            120,
            120,
        ),
    )

    result = await service.process_image(
        image=image,
        phone_number=None,
        source="api",
        mime_type="image/jpeg",
        file_size_bytes=100_000,
    )

    response = (
        result["response"]
        or ""
    ).lower()

    assert (
        result["status"]
        == "rejected"
    )

    assert "blurry" in response

    assert (
        "retake" in response
        or "focus" in response
    )

    subject_validator.validate.assert_not_called()