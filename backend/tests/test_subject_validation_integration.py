"""
Integration tests for the KILIMO tomato-subject validation gate.

These tests verify that:

1. unsupported images never reach disease inference;
2. uncertain images never reach disease inference;
3. supported images continue through the normal pipeline;
4. rejected subjects are not persisted as disease assessments.
"""

from unittest.mock import AsyncMock, Mock

import pytest
from PIL import Image

from app.services.image_analysis_service import (
    ImageAnalysisService,
)
from cv.subject_validator import (
    SubjectValidationResult,
)


def make_quality_compatible_image() -> Image.Image:
    """
    Create a deterministic high-detail image that passes the
    basic blur/brightness quality gate.

    The image has no semantic meaning. Subject decisions in
    these tests are controlled using a mocked validator.
    """

    size = 512

    image = Image.new(
        "RGB",
        (
            size,
            size,
        ),
    )

    pixels = image.load()

    block_size = 16

    for y in range(size):
        for x in range(size):

            checker = (
                (
                    x // block_size
                    + y // block_size
                )
                % 2
            )

            if checker == 0:
                pixels[
                    x,
                    y
                ] = (
                    70,
                    130,
                    70,
                )

            else:
                pixels[
                    x,
                    y
                ] = (
                    190,
                    210,
                    170,
                )

    return image


def build_service(
    subject_result: SubjectValidationResult,
):
    """
    Create ImageAnalysisService with fully controlled
    dependencies.
    """

    assessor = Mock()

    subject_validator = Mock()

    subject_validator.validate.return_value = (
        subject_result
    )

    advisory_engine = Mock()

    advisory_responder = Mock()

    advisory_responder.generate = AsyncMock(
        return_value=(
            "The image was assessed successfully."
        )
    )

    session_service = Mock()

    session_service.get_or_create_session = (
        AsyncMock()
    )

    session_service.save_message = (
        AsyncMock()
    )

    session_service.get_session = (
        AsyncMock(
            return_value=None
        )
    )

    session_service.get_history = (
        AsyncMock(
            return_value=[]
        )
    )

    session_service.update_session = (
        AsyncMock()
    )

    assessment_service = Mock()

    assessment_service.save_assessment = (
        AsyncMock(
            return_value=123
        )
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

        "assessment_service":
            assessment_service,
    }


@pytest.mark.asyncio
async def test_unsupported_subject_never_reaches_assessor():
    """
    Clearly unsupported input must stop before EfficientNet.
    """

    subject_result = SubjectValidationResult(
        accepted=False,
        status="unsupported",
        reason="unsupported_subject",
        message=(
            "This image does not appear to contain "
            "a supported tomato leaf."
        ),
        tomato_score=0.05,
        unsupported_threshold=0.20,
        supported_threshold=0.80,
        model_available=True,
    )

    dependencies = build_service(
        subject_result
    )

    image = make_quality_compatible_image()

    result = await dependencies[
        "service"
    ].process_image(
        image=image,
        source="api",
        mime_type="image/jpeg",
        file_size_bytes=150_000,
    )

    assert result["status"] == "rejected"

    assert (
        result["subject_validation"][
            "status"
        ]
        == "unsupported"
    )

    assert (
        result["subject_validation"][
            "tomato_score"
        ]
        == 0.05
    )

    assert result["prediction"] is None
    assert result["severity"] is None
    assert result["advisory"] is None
    assert result["assessment_id"] is None

    dependencies[
        "subject_validator"
    ].validate.assert_called_once()

    dependencies[
        "assessor"
    ].assess.assert_not_called()

    dependencies[
        "assessment_service"
    ].save_assessment.assert_not_awaited()

    dependencies[
        "advisory_engine"
    ].generate.assert_not_called()

    dependencies[
        "advisory_responder"
    ].generate.assert_not_awaited()


@pytest.mark.asyncio
async def test_uncertain_subject_never_reaches_assessor():
    """
    Ambiguous subject input must trigger abstention rather
    than forcing a disease prediction.
    """

    subject_result = SubjectValidationResult(
        accepted=False,
        status="uncertain",
        reason="subject_uncertain",
        message=(
            "I could not confirm that this image is "
            "suitable for tomato disease assessment."
        ),
        tomato_score=0.55,
        unsupported_threshold=0.20,
        supported_threshold=0.80,
        model_available=True,
    )

    dependencies = build_service(
        subject_result
    )

    image = make_quality_compatible_image()

    result = await dependencies[
        "service"
    ].process_image(
        image=image,
        source="api",
        mime_type="image/jpeg",
        file_size_bytes=150_000,
    )

    assert result["status"] == "rejected"

    assert (
        result["subject_validation"][
            "status"
        ]
        == "uncertain"
    )

    assert result["prediction"] is None
    assert result["severity"] is None
    assert result["assessment_id"] is None

    dependencies[
        "subject_validator"
    ].validate.assert_called_once()

    dependencies[
        "assessor"
    ].assess.assert_not_called()

    dependencies[
        "assessment_service"
    ].save_assessment.assert_not_awaited()

    dependencies[
        "advisory_engine"
    ].generate.assert_not_called()

    dependencies[
        "advisory_responder"
    ].generate.assert_not_awaited()


@pytest.mark.asyncio
async def test_supported_subject_reaches_disease_assessor():
    """
    A supported tomato image should continue into the normal
    disease-assessment pipeline.
    """

    subject_result = SubjectValidationResult(
        accepted=True,
        status="supported",
        reason=None,
        message=(
            "Image passed the tomato-subject "
            "validation check."
        ),
        tomato_score=0.98,
        unsupported_threshold=0.20,
        supported_threshold=0.80,
        model_available=True,
    )

    dependencies = build_service(
        subject_result
    )

    assessment = Mock()

    assessment.to_dict.return_value = {
        "disease":
            "Early Blight",

        "confidence":
            0.95,

        "severity_level":
            "Moderate",

        "affected_area_percentage":
            24.0,

        "label_index":
            1,

        "all_scores":
            [
                0.01,
                0.95,
                0.01,
                0.01,
                0.01,
                0.0,
                0.0,
                0.0,
                0.0,
                0.01,
                0.0,
            ],
    }

    dependencies[
        "assessor"
    ].assess.return_value = assessment

    advisory = {
        "description":
            "Early blight advisory.",

        "symptoms":
            [
                "Leaf lesions"
            ],

        "recommended_actions":
            [
                "Remove affected leaves"
            ],

        "prevention":
            [
                "Maintain field hygiene"
            ],

        "confidence_message":
            "The model produced a strong score.",

        "urgency":
            "medium",
    }

    dependencies[
        "advisory_engine"
    ].generate.return_value = advisory

    image = make_quality_compatible_image()

    result = await dependencies[
        "service"
    ].process_image(
        image=image,
        source="api",
        mime_type="image/jpeg",
        file_size_bytes=150_000,
    )

    assert result["status"] == "completed"

    assert (
        result["subject_validation"][
            "status"
        ]
        == "supported"
    )

    assert (
        result["subject_validation"][
            "tomato_score"
        ]
        == 0.98
    )

    assert (
        result["prediction"][
            "disease"
        ]
        == "Early Blight"
    )

    assert result["assessment_id"] == 123

    dependencies[
        "subject_validator"
    ].validate.assert_called_once()

    dependencies[
        "assessor"
    ].assess.assert_called_once()

    dependencies[
        "assessment_service"
    ].save_assessment.assert_awaited_once()

    dependencies[
        "advisory_engine"
    ].generate.assert_called_once()

    dependencies[
        "advisory_responder"
    ].generate.assert_awaited_once()


@pytest.mark.asyncio
async def test_subject_validator_failure_fails_closed():
    """
    If the trained subject-validator model cannot be loaded,
    disease inference must not be allowed to continue.
    """

    subject_result = SubjectValidationResult(
        accepted=True,
        status="supported",
        reason=None,
        message="unused",
        tomato_score=0.99,
        unsupported_threshold=0.20,
        supported_threshold=0.80,
        model_available=True,
    )

    dependencies = build_service(
        subject_result
    )

    dependencies[
        "subject_validator"
    ].validate.side_effect = (
        FileNotFoundError(
            "checkpoint missing"
        )
    )

    image = make_quality_compatible_image()

    result = await dependencies[
        "service"
    ].process_image(
        image=image,
        source="api",
        mime_type="image/jpeg",
        file_size_bytes=150_000,
    )

    assert result["status"] == "rejected"

    assert (
        result["subject_validation"][
            "status"
        ]
        == "unavailable"
    )

    assert (
        result["subject_validation"][
            "model_available"
        ]
        is False
    )

    assert result["prediction"] is None
    assert result["assessment_id"] is None

    dependencies[
        "assessor"
    ].assess.assert_not_called()

    dependencies[
        "assessment_service"
    ].save_assessment.assert_not_awaited()