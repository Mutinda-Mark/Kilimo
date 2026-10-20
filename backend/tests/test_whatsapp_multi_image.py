from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from PIL import Image

from app.services.whatsapp_processor import (
    WhatsAppProcessor,
)
from cv.config import DISEASE_CLASSES
from cv.subject_validator import (
    SubjectValidationResult,
)


def make_image_bytes() -> bytes:
    """
    Build a high-detail checkerboard image that passes the
    technical quality gate.
    """

    image = Image.new(
        "RGB",
        (
            512,
            512,
        ),
    )

    pixels = image.load()

    block = 16

    for y in range(
        512
    ):
        for x in range(
            512
        ):

            if (
                (
                    x // block
                    + y // block
                )
                % 2
                == 0
            ):

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

    output = BytesIO()

    image.save(
        output,
        format="JPEG",
        quality=95,
    )

    return output.getvalue()


def build_processor():
    """
    Build the processor entirely from mocked dependencies.
    """

    whatsapp_service = Mock()

    whatsapp_service.send_text_message = AsyncMock(
        return_value={
            "status": "sent"
        }
    )

    whatsapp_service.download_media = AsyncMock(
        return_value=SimpleNamespace(
            media_id="media-1",
            mime_type="image/jpeg",
            file_size=100_000,
            content=make_image_bytes(),
        )
    )

    chat_service = Mock()

    chat_service.process_message = AsyncMock(
        return_value={
            "response":
                "Normal chat response."
        }
    )

    subject_validator = Mock()

    subject_validator.validate.return_value = (
        SubjectValidationResult(
            accepted=True,
            status="supported",
            reason=None,
            message=(
                "Image passed the tomato-subject "
                "validation check."
            ),
            tomato_score=0.99,
            unsupported_threshold=0.20,
            supported_threshold=0.80,
            model_available=True,
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
            return_value=100
        )
    )

    assessor = Mock()

    advisory_engine = Mock()

    advisory_responder = Mock()

    advisory_responder.generate = AsyncMock(
        return_value=(
            "Farmer-friendly assessment."
        )
    )

    image_analysis_service = Mock()

    image_analysis_service.subject_validator = (
        subject_validator
    )

    image_analysis_service.session_service = (
        session_service
    )

    image_analysis_service.assessment_service = (
        assessment_service
    )

    image_analysis_service.assessor = assessor

    image_analysis_service.advisory_engine = (
        advisory_engine
    )

    image_analysis_service.advisory_responder = (
        advisory_responder
    )

    event_service = Mock()

    event_service.mark_completed = (
        AsyncMock()
    )

    event_service.mark_failed = (
        AsyncMock()
    )

    batch_service = Mock()

    batch_service.get_open_batch = AsyncMock(
        return_value=None
    )

    batch_service.get_or_create_active_batch = (
        AsyncMock(
            return_value={
                "id": 10,
                "status": "collecting",
                "max_images": 3,
            }
        )
    )

    batch_service.add_image = AsyncMock(
        return_value={
            "id": 50,
            "batch_id": 10,
            "image_position": 1,
            "status": "accepted",
        }
    )

    batch_service.count_images = AsyncMock(
        return_value=1
    )

    batch_service.begin_processing = (
        AsyncMock(
            return_value=True
        )
    )

    batch_service.list_images = AsyncMock(
        return_value=[]
    )

    batch_service.mark_completed = (
        AsyncMock()
    )

    batch_service.mark_image_processed = (
        AsyncMock()
    )

    batch_service.cancel_batch = (
        AsyncMock()
    )

    processor = WhatsAppProcessor(
        whatsapp_service=whatsapp_service,
        chat_service=chat_service,
        image_analysis_service=(
            image_analysis_service
        ),
        event_service=event_service,
        batch_service=batch_service,
    )

    return {
        "processor":
            processor,

        "whatsapp":
            whatsapp_service,

        "chat":
            chat_service,

        "subject":
            subject_validator,

        "session":
            session_service,

        "assessment":
            assessment_service,

        "assessor":
            assessor,

        "advisory_engine":
            advisory_engine,

        "advisory_responder":
            advisory_responder,

        "events":
            event_service,

        "batch":
            batch_service,
    }


@pytest.mark.asyncio
async def test_done_without_batch_returns_guidance():

    deps = build_processor()

    await deps[
        "processor"
    ]._process_text(
        sender="254700000001",
        message={
            "text": "DONE",
        },
    )

    deps[
        "chat"
    ].process_message.assert_not_awaited()

    deps[
        "whatsapp"
    ].send_text_message.assert_awaited_once()

    sent_text = (
        deps[
            "whatsapp"
        ]
        .send_text_message
        .await_args
        .kwargs[
            "text"
        ]
        .lower()
    )

    assert (
        "no image assessment"
        in sent_text
    )


@pytest.mark.asyncio
async def test_done_while_processing_does_not_finalize():

    deps = build_processor()

    deps[
        "batch"
    ].get_open_batch.return_value = {
        "id": 10,
        "status": "processing",
    }

    await deps[
        "processor"
    ]._process_text(
        sender="254700000001",
        message={
            "text": "done",
        },
    )

    deps[
        "batch"
    ].begin_processing.assert_not_awaited()

    sent_text = (
        deps[
            "whatsapp"
        ]
        .send_text_message
        .await_args
        .kwargs[
            "text"
        ]
        .lower()
    )

    assert (
        "already being analysed"
        in sent_text
    )


@pytest.mark.asyncio
async def test_accepted_image_is_added_to_batch():

    deps = build_processor()

    message = {
        "message_id":
            "wamid-1",

        "type":
            "image",

        "media_id":
            "media-1",

        "mime_type":
            "image/jpeg",

        "caption":
            "",
    }

    await deps[
        "processor"
    ]._process_image(
        sender="254700000001",
        message=message,
    )

    deps[
        "subject"
    ].validate.assert_called_once()

    deps[
        "batch"
    ].add_image.assert_awaited_once()

    kwargs = (
        deps[
            "batch"
        ]
        .add_image
        .await_args
        .kwargs
    )

    assert (
        kwargs[
            "whatsapp_message_id"
        ]
        == "wamid-1"
    )

    assert (
        kwargs[
            "status"
        ]
        == "accepted"
    )

    assert (
        kwargs[
            "tomato_score"
        ]
        == 0.99
    )

    assert (
        isinstance(
            kwargs[
                "image_bytes"
            ],
            bytes,
        )
    )


@pytest.mark.asyncio
async def test_subject_rejection_does_not_use_batch_slot():

    deps = build_processor()

    deps[
        "subject"
    ].validate.return_value = (
        SubjectValidationResult(
            accepted=False,
            status="unsupported",
            reason="unsupported_subject",
            message=(
                "This image is not a supported tomato leaf."
            ),
            tomato_score=0.02,
            unsupported_threshold=0.20,
            supported_threshold=0.80,
            model_available=True,
        )
    )

    await deps[
        "processor"
    ]._process_image(
        sender="254700000001",
        message={
            "message_id":
                "wamid-2",

            "type":
                "image",

            "media_id":
                "media-2",

            "mime_type":
                "image/jpeg",
        },
    )

    deps[
        "batch"
    ].get_or_create_active_batch.assert_not_awaited()

    deps[
        "batch"
    ].add_image.assert_not_awaited()


@pytest.mark.asyncio
async def test_processing_batch_ignores_extra_image():

    deps = build_processor()

    deps[
        "batch"
    ].get_open_batch.return_value = {
        "id": 10,
        "status": "processing",
    }

    await deps[
        "processor"
    ]._process_image(
        sender="254700000001",
        message={
            "message_id":
                "wamid-extra",

            "type":
                "image",

            "media_id":
                "media-extra",

            "mime_type":
                "image/jpeg",
        },
    )

    deps[
        "whatsapp"
    ].download_media.assert_not_awaited()

    deps[
        "subject"
    ].validate.assert_not_called()

    deps[
        "batch"
    ].add_image.assert_not_awaited()


@pytest.mark.asyncio
async def test_third_accepted_image_triggers_finalization(
    monkeypatch,
):

    deps = build_processor()

    deps[
        "batch"
    ].add_image.return_value = {
        "id": 52,
        "batch_id": 10,
        "image_position": 3,
        "status": "accepted",
    }

    deps[
        "batch"
    ].count_images.return_value = 3

    finalize = AsyncMock()

    monkeypatch.setattr(
        deps[
            "processor"
        ],
        "_finalize_batch",
        finalize,
    )

    await deps[
        "processor"
    ]._process_image(
        sender="254700000001",
        message={
            "message_id":
                "wamid-3",

            "type":
                "image",

            "media_id":
                "media-3",

            "mime_type":
                "image/jpeg",
        },
    )

    finalize.assert_awaited_once_with(
        sender="254700000001",
        batch_id=10,
    )

@pytest.mark.asyncio
async def test_finalize_batch_saves_one_combined_assessment():
    """
    Three stored images with a 2/3 disease agreement should
    produce one combined assessment and one farmer response.
    """

    deps = build_processor()

    # ---------------------------------------------------------
    # Stored batch images
    # ---------------------------------------------------------

    image_bytes = make_image_bytes()

    deps[
        "batch"
    ].list_images.return_value = [
        {
            "id": 51,
            "batch_id": 10,
            "image_position": 1,
            "status": "accepted",
            "image_bytes": image_bytes,
        },
        {
            "id": 52,
            "batch_id": 10,
            "image_position": 2,
            "status": "accepted",
            "image_bytes": image_bytes,
        },
        {
            "id": 53,
            "batch_id": 10,
            "image_position": 3,
            "status": "accepted",
            "image_bytes": image_bytes,
        },
    ]

    # ---------------------------------------------------------
    # Individual CV assessments
    # ---------------------------------------------------------

    class FakeAssessment:

        def __init__(
            self,
            disease,
            confidence,
            severity,
            affected_area,
        ):
            self.disease = disease
            self.confidence = confidence
            self.severity = severity
            self.affected_area = affected_area

        def to_dict(self):

            scores = {
                class_name: 0.0
                for class_name in DISEASE_CLASSES
            }

            scores[
                self.disease
            ] = self.confidence

            return {
                "disease":
                    self.disease,

                "confidence":
                    self.confidence,

                "severity_level":
                    self.severity,

                "affected_area_percentage":
                    self.affected_area,

                "label_index":
                    DISEASE_CLASSES.index(
                        self.disease
                    ),

                "all_scores":
                    scores,
            }

    deps[
        "assessor"
    ].assess.side_effect = [
        FakeAssessment(
            "Early Blight",
            0.95,
            "Moderate",
            20.0,
        ),
        FakeAssessment(
            "Early Blight",
            0.90,
            "Moderate",
            30.0,
        ),
        FakeAssessment(
            "Septoria Leaf Spot",
            0.80,
            "Low",
            10.0,
        ),
    ]

    # ---------------------------------------------------------
    # Structured advisory
    # ---------------------------------------------------------

    deps[
        "advisory_engine"
    ].generate.return_value = {
        "description":
            "Early blight advisory.",

        "symptoms":
            [
                "Dark leaf lesions"
            ],

        "recommended_actions":
            [
                "Remove badly affected leaves."
            ],

        "prevention":
            [
                "Improve field hygiene."
            ],

        "confidence_message":
            "The combined assessment produced a strong result.",

        "urgency":
            "Medium",
    }

    # ---------------------------------------------------------
    # Finalize
    # ---------------------------------------------------------

    await deps[
        "processor"
    ]._finalize_batch(
        sender="254700000001",
        batch_id=10,
    )

    # ---------------------------------------------------------
    # Three individual images were classified
    # ---------------------------------------------------------

    assert (
        deps[
            "assessor"
        ].assess.call_count
        == 3
    )

    # ---------------------------------------------------------
    # Only ONE combined historical assessment is saved
    # ---------------------------------------------------------

    deps[
        "assessment"
    ].save_assessment.assert_awaited_once()

    save_kwargs = (
        deps[
            "assessment"
        ]
        .save_assessment
        .await_args
        .kwargs
    )

    assert (
        save_kwargs[
            "phone_number"
        ]
        == "254700000001"
    )

    assert (
        save_kwargs[
            "source"
        ]
        == "whatsapp"
    )

    combined = save_kwargs[
        "assessment"
    ]

    assert (
        combined[
            "disease"
        ]
        == "Early Blight"
    )

    assert (
        combined[
            "image_count"
        ]
        == 3
    )

    assert (
        combined[
            "agreement_count"
        ]
        == 2
    )

    assert (
        combined[
            "agreement_ratio"
        ]
        == pytest.approx(
            2 / 3,
            abs=0.0001,
        )
    )

    # Severity is based on the two images supporting the
    # consensus disease.
    assert (
        combined[
            "affected_area_percentage"
        ]
        == 25.0
    )

    # ---------------------------------------------------------
    # Structured advisory + responder run only once
    # ---------------------------------------------------------

    deps[
        "advisory_engine"
    ].generate.assert_called_once()

    deps[
        "advisory_responder"
    ].generate.assert_awaited_once()

    # ---------------------------------------------------------
    # All three images link to the SAME combined assessment
    # ---------------------------------------------------------

    assert (
        deps[
            "batch"
        ].mark_image_processed.await_count
        == 3
    )

    for call in (
        deps[
            "batch"
        ].mark_image_processed.await_args_list
    ):

        assert (
            call.kwargs[
                "assessment_id"
            ]
            == 100
        )

    # ---------------------------------------------------------
    # Batch is completed exactly once
    # ---------------------------------------------------------

    deps[
        "batch"
    ].mark_completed.assert_awaited_once_with(
        10
    )

    deps[
        "batch"
    ].cancel_batch.assert_not_awaited()

    # ---------------------------------------------------------
    # One final farmer-facing WhatsApp result
    # ---------------------------------------------------------

    deps[
        "whatsapp"
    ].send_text_message.assert_awaited_once()

    sent_text = (
        deps[
            "whatsapp"
        ]
        .send_text_message
        .await_args
        .kwargs[
            "text"
        ]
    )

    assert (
        "2/3 photos agreed"
        in sent_text
    )


@pytest.mark.asyncio
async def test_finalize_batch_abstains_when_predictions_disagree():
    """
    Three conflicting predictions must produce an abstention
    instead of a forced combined diagnosis.
    """

    deps = build_processor()

    image_bytes = make_image_bytes()

    deps[
        "batch"
    ].list_images.return_value = [
        {
            "id": 61,
            "batch_id": 20,
            "image_position": 1,
            "status": "accepted",
            "image_bytes": image_bytes,
        },
        {
            "id": 62,
            "batch_id": 20,
            "image_position": 2,
            "status": "accepted",
            "image_bytes": image_bytes,
        },
        {
            "id": 63,
            "batch_id": 20,
            "image_position": 3,
            "status": "accepted",
            "image_bytes": image_bytes,
        },
    ]

    class FakeAssessment:

        def __init__(
            self,
            disease,
            confidence,
        ):
            self.disease = disease
            self.confidence = confidence

        def to_dict(self):

            scores = {
                class_name: 0.0
                for class_name in DISEASE_CLASSES
            }

            scores[
                self.disease
            ] = self.confidence

            return {
                "disease":
                    self.disease,

                "confidence":
                    self.confidence,

                "severity_level":
                    "Moderate",

                "affected_area_percentage":
                    20.0,

                "label_index":
                    DISEASE_CLASSES.index(
                        self.disease
                    ),

                "all_scores":
                    scores,
            }

    deps[
        "assessor"
    ].assess.side_effect = [
        FakeAssessment(
            "Early Blight",
            0.95,
        ),
        FakeAssessment(
            "Late Blight",
            0.93,
        ),
        FakeAssessment(
            "Septoria Leaf Spot",
            0.91,
        ),
    ]

    await deps[
        "processor"
    ]._finalize_batch(
        sender="254700000001",
        batch_id=20,
    )

    # ---------------------------------------------------------
    # All images are individually assessed.
    # ---------------------------------------------------------

    assert (
        deps[
            "assessor"
        ].assess.call_count
        == 3
    )

    # ---------------------------------------------------------
    # NO combined disease assessment should be persisted.
    # ---------------------------------------------------------

    deps[
        "assessment"
    ].save_assessment.assert_not_awaited()

    # Advisory generation must also not run.
    deps[
        "advisory_engine"
    ].generate.assert_not_called()

    deps[
        "advisory_responder"
    ].generate.assert_not_awaited()

    # ---------------------------------------------------------
    # Batch images are closed without linking them to a
    # disease assessment.
    # ---------------------------------------------------------

    assert (
        deps[
            "batch"
        ].mark_image_processed.await_count
        == 3
    )

    for call in (
        deps[
            "batch"
        ].mark_image_processed.await_args_list
    ):

        assert (
            call.kwargs[
                "assessment_id"
            ]
            is None
        )

    # ---------------------------------------------------------
    # Batch is closed cleanly.
    # ---------------------------------------------------------

    deps[
        "batch"
    ].mark_completed.assert_awaited_once_with(
        20
    )

    deps[
        "batch"
    ].cancel_batch.assert_not_awaited()

    # ---------------------------------------------------------
    # Farmer receives one uncertainty message.
    # ---------------------------------------------------------

    deps[
        "whatsapp"
    ].send_text_message.assert_awaited_once()

    sent_text = (
        deps[
            "whatsapp"
        ]
        .send_text_message
        .await_args
        .kwargs[
            "text"
        ]
        .lower()
    )

    assert (
        "different disease"
        in sent_text
        or "cannot give a reliable"
        in sent_text
    )