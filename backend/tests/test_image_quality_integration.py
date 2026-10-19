"""
Integration tests for the Sprint III image-quality gate.

These tests verify that image-quality rejection occurs before
disease inference and downstream advisory processing.
"""

from unittest.mock import AsyncMock, Mock

import pytest
from PIL import Image

from app.services.image_analysis_service import (
    ImageAnalysisService,
)


@pytest.mark.asyncio
async def test_rejected_image_does_not_call_assessor():
    """
    A technically unsuitable image must never reach the disease
    classifier.

    This is a core Sprint III safety requirement.
    """

    # ---------------------------------------------------------
    # Dependencies
    # ---------------------------------------------------------

    assessor = Mock()

    advisory_engine = Mock()

    advisory_responder = Mock()
    advisory_responder.generate = AsyncMock()

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

    # ---------------------------------------------------------
    # Service under test
    # ---------------------------------------------------------

    service = ImageAnalysisService(
        assessor=assessor,
        advisory_engine=advisory_engine,
        advisory_responder=advisory_responder,
        session_service=session_service,
        assessment_service=assessment_service,
    )

    # ---------------------------------------------------------
    # Featureless image
    #
    # Technically valid PIL image but with effectively no
    # useful edge detail.
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Run
    # ---------------------------------------------------------

    result = await service.process_image(
        image=image,
        phone_number=None,
        source="api",
        mime_type="image/jpeg",
        file_size_bytes=100_000,
    )

    # ---------------------------------------------------------
    # Quality decision
    # ---------------------------------------------------------

    assert result["status"] == "rejected"

    assert result["quality"][
        "reason"
    ] == "blur"

    assert result["prediction"] is None
    assert result["severity"] is None
    assert result["assessment_id"] is None

    # ---------------------------------------------------------
    # Critical safety assertion:
    # rejected input never reaches disease inference.
    # ---------------------------------------------------------

    assessor.assess.assert_not_called()

    # No assessment should be persisted.
    assessment_service.save_assessment.assert_not_awaited()

    # No advisory should be generated.
    advisory_engine.generate.assert_not_called()

    # Gemini/RAG responder must not run either.
    advisory_responder.generate.assert_not_awaited()


@pytest.mark.asyncio
async def test_rejected_image_returns_actionable_message():
    """
    A rejected image should produce actionable feedback rather
    than a generic server error.
    """

    assessor = Mock()

    advisory_engine = Mock()

    advisory_responder = Mock()
    advisory_responder.generate = AsyncMock()

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
    )

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

    assert result["status"] == "rejected"

    assert "blurry" in response

    assert (
        "retake" in response
        or "focus" in response
    )