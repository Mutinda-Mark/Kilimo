"""
Background processing for incoming WhatsApp farmer messages.

The actual webhook endpoint should acknowledge Meta quickly.

Heavy work such as:
- image downloads
- image validation
- CV inference
- RAG
- Gemini generation

happens here after the HTTP response is sent.

WhatsApp image messages support multi-image assessment batches.

A farmer may submit up to three usable images for one assessment.
The farmer may also reply DONE to finalize a batch early.
"""

from __future__ import annotations

import json
import logging


logger = logging.getLogger(__name__)
from io import BytesIO
from typing import Any

from PIL import Image, UnidentifiedImageError

from app.services.chat_service import ChatService
from app.services.image_analysis_service import ImageAnalysisService
from app.services.image_compression import (
    compress_batch_image,
    decode_batch_image,
)
from app.services.multi_image_aggregation import (
    aggregate_assessments,
)
from app.services.whatsapp_batch_service import (
    WhatsAppBatchService,
)
from app.services.whatsapp_event_service import (
    WhatsAppEventService,
)
from app.whatsapp.service import WhatsAppService
from cv.image_quality import evaluate_image_quality


class WhatsAppProcessor:
    """
    Process one already-claimed WhatsApp farmer message.
    """

    MAX_BATCH_IMAGES = 3

    def __init__(
        self,
        whatsapp_service: WhatsAppService,
        chat_service: ChatService,
        image_analysis_service: ImageAnalysisService,
        event_service: WhatsAppEventService,
        batch_service: WhatsAppBatchService,
    ) -> None:

        self.whatsapp_service = whatsapp_service
        self.chat_service = chat_service
        self.image_analysis_service = image_analysis_service
        self.event_service = event_service
        self.batch_service = batch_service

    # =========================================================
    # TOP-LEVEL MESSAGE PROCESSING
    # =========================================================

    async def process_message(
        self,
        message: dict[str, Any],
    ) -> None:
        """
        Process one WhatsApp message.

        The message must already have been claimed through
        WhatsAppEventService.
        """

        message_id = (
            message.get("message_id")
            or ""
        ).strip()

        sender = (
            message.get("from")
            or ""
        ).strip()

        message_type = (
            message.get("type")
            or ""
        ).strip()

        try:

            if not message_id:
                raise ValueError(
                    "WhatsApp message ID is missing."
                )

            if not sender:
                raise ValueError(
                    "WhatsApp sender is missing."
                )

            # =================================================
            # TEXT
            # =================================================

            if message_type == "text":

                await self._process_text(
                    sender=sender,
                    message=message,
                )

            # =================================================
            # IMAGE
            # =================================================

            elif message_type == "image":

                await self._process_image(
                    sender=sender,
                    message=message,
                )

            # =================================================
            # UNSUPPORTED MESSAGE TYPE
            # =================================================

            else:

                logger.warning(
                    "[WhatsApp] Unsupported message type: "
                    f"{message_type}"
                )

                await self.whatsapp_service.send_text_message(
                    to=sender,
                    text=(
                        "KILIMO currently supports text "
                        "messages and tomato leaf images."
                    ),
                )

            # =================================================
            # MESSAGE COMPLETED
            # =================================================

            await self.event_service.mark_completed(
                message_id
            )

        except Exception as exc:

            logger.error(
                "========== WHATSAPP PROCESSING ERROR =========="
            )

            logger.error(
                f"Message ID: {message_id}"
            )

            logger.error(
                repr(
                    exc
                )
            )

            logger.error(
                "=============================================="
            )

            if message_id:

                try:

                    await self.event_service.mark_failed(
                        message_id=message_id,
                        error_message=str(
                            "WhatsApp message processing failed"
                        ),
                    )

                except Exception as db_exc:

                    logger.error(
                        "Could not update failed WhatsApp event state."
                    )

            if sender:

                try:

                    await self.whatsapp_service.send_text_message(
                        to=sender,
                        text=(
                            "Sorry, I could not process your "
                            "message right now. Please try "
                            "again."
                        ),
                    )

                except Exception as send_exc:

                    logger.error(
                        "Could not send WhatsApp fallback response."
                    )

    # =========================================================
    # TEXT PROCESSING
    # =========================================================

    async def _process_text(
        self,
        sender: str,
        message: dict[str, Any],
    ) -> None:

        incoming_text = (
            message.get("text")
            or ""
        ).strip()

        if not incoming_text:
            raise ValueError(
                "Incoming WhatsApp text message is empty."
            )

        logger.info(
            "Processing WhatsApp text message."
        )

        # -----------------------------------------------------
        # Batch finalization command
        # -----------------------------------------------------

        if incoming_text.upper() == "DONE":

            await self._process_done(
                sender
            )

            return

        # -----------------------------------------------------
        # Normal farmer question
        # -----------------------------------------------------

        result = (
            await self.chat_service.process_message(
                phone_number=sender,
                question=incoming_text,
            )
        )

        response_text = result[
            "response"
        ]

        send_result = (
            await self.whatsapp_service.send_text_message(
                to=sender,
                text=response_text,
            )
        )

        logger.info(
            "WhatsApp Text response sent successfully."
        )

    # =========================================================
    # DONE COMMAND
    # =========================================================

    async def _process_done(
        self,
        sender: str,
    ) -> None:
        """
        Finalize the farmer's current image batch.
        """

        batch = (
            await self.batch_service.get_open_batch(
                sender
            )
        )

        if batch is None:

            await self.whatsapp_service.send_text_message(
                to=sender,
                text=(
                    "There is no image assessment waiting "
                    "to be analysed. Please send a clear "
                    "photo of an affected tomato leaf first."
                ),
            )

            return

        if batch[
            "status"
        ] == "processing":

            await self.whatsapp_service.send_text_message(
                to=sender,
                text=(
                    "Your tomato images are already being "
                    "analysed. Please wait for the result."
                ),
            )

            return

        await self._finalize_batch(
            sender=sender,
            batch_id=int(
                batch["id"]
            ),
        )

    # =========================================================
    # IMAGE PROCESSING
    # =========================================================

    async def _process_image(
        self,
        sender: str,
        message: dict[str, Any],
    ) -> None:

        message_id = (
            message.get("message_id")
            or ""
        ).strip()

        media_id = (
            message.get("media_id")
            or ""
        ).strip()

        mime_type = (
            message.get("mime_type")
            or ""
        ).strip()

        caption = (
            message.get("caption")
            or ""
        ).strip()

        if not message_id:
            raise ValueError(
                "Incoming WhatsApp image has no message ID."
            )

        if not media_id:
            raise ValueError(
                "Incoming WhatsApp image has no media ID."
            )

        if (
            mime_type
            and not mime_type.startswith(
                "image/"
            )
        ):
            raise ValueError(
                "WhatsApp media is not an image."
            )

        # -----------------------------------------------------
        # If an existing batch is already being processed,
        # this is probably another image from the same media
        # burst. Do not create a second batch.
        # -----------------------------------------------------

        open_batch = (
            await self.batch_service.get_open_batch(
                sender
            )
        )

        if (
            open_batch is not None
            and open_batch["status"]
            == "processing"
        ):

            logger.info(
                "Additional WhatsApp image ignored because "
                "the current batch is already processing."
            )
            return

        logger.info(
             "Processing WhatsApp image with MIME type %s.",
            mime_type,
        )


        # -----------------------------------------------------
        # Download from Meta
        # -----------------------------------------------------

        media = (
            await self.whatsapp_service.download_media(
                media_id
            )
        )
        logger.info(
            "WhatsApp media downloaded: mime_type=%s, size_bytes=%s",
            media.mime_type,
            media.file_size,
        )

        # -----------------------------------------------------
        # Decode image
        # -----------------------------------------------------

        try:

            with Image.open(
                BytesIO(
                    media.content
                )
            ) as decoded_image:

                decoded_image.load()

                image = (
                    decoded_image.convert(
                        "RGB"
                    )
                )

        except (
            UnidentifiedImageError,
            OSError,
            ValueError,
        ):

            await self.whatsapp_service.send_text_message(
                to=sender,
                text=(
                    "I couldn't read this image. "
                    "Please send a valid JPEG, PNG, or WebP "
                    "photograph of the affected tomato leaf."
                ),
            )

            return

        effective_mime_type = (
            media.mime_type
            or mime_type
            or None
        )

        # =====================================================
        # 1. TECHNICAL QUALITY GATE
        # =====================================================

        quality_result = evaluate_image_quality(
            image,
            file_size_bytes=media.file_size,
            mime_type=effective_mime_type,
        )

        if not quality_result.accepted:

            await self.whatsapp_service.send_text_message(
                to=sender,
                text=(
                    quality_result.message
                    + "\n\n"
                    "This photo was not added to your "
                    "assessment, so you can send another one."
                ),
            )

            return

        # =====================================================
        # 2. TOMATO SUBJECT GATE
        # =====================================================

        try:

            subject_result = (
                self.image_analysis_service
                .subject_validator
                .validate(
                    image
                )
            )

        except (
            FileNotFoundError,
            RuntimeError,
        ):

            await self.whatsapp_service.send_text_message(
                to=sender,
                text=(
                    "Image assessment is temporarily "
                    "unavailable because the tomato-image "
                    "validation service could not be loaded. "
                    "Please try again later."
                ),
            )

            return

        if not subject_result.accepted:

            await self.whatsapp_service.send_text_message(
                to=sender,
                text=(
                    subject_result.message
                    + "\n\n"
                    "This photo was not added to your "
                    "assessment, so you can send another one."
                ),
            )

            return

        # =====================================================
        # 3. GET / CREATE COLLECTING BATCH
        # =====================================================

        batch = (
            await self.batch_service
            .get_or_create_active_batch(
                sender
            )
        )

        batch_id = int(
            batch["id"]
        )

        # =====================================================
        # 4. COMPRESS ACCEPTED IMAGE
        # =====================================================

        (
            compressed_bytes,
            stored_width,
            stored_height,
        ) = compress_batch_image(
            image
        )

        # =====================================================
        # 5. STORE ACCEPTED IMAGE
        # =====================================================

        try:

            stored_image = (
                await self.batch_service.add_image(
                    batch_id=batch_id,
                    whatsapp_message_id=message_id,
                    media_id=media_id,
                    mime_type=effective_mime_type,
                    original_file_size=media.file_size,
                    stored_file_size=len(
                        compressed_bytes
                    ),
                    width=stored_width,
                    height=stored_height,
                    status="accepted",
                    rejection_reason=None,
                    tomato_score=(
                        subject_result.tomato_score
                    ),
                    image_bytes=compressed_bytes,
                )
            )

        except ValueError as exc:

            # The common expected case here is that several
            # WhatsApp photos arrived concurrently and another
            # worker filled the three-image batch first.

            if (
                "already full"
                in str(
                    exc
                ).lower()
                or "not collecting"
                in str(
                    exc
                ).lower()
            ):

                logger.warning(
                    "[WhatsApp] Additional burst image "
                    "ignored because batch is full or "
                    "already processing."
                )

                return

            raise

        # -----------------------------------------------------
        # Save image/caption into conversation history
        # -----------------------------------------------------

        await (
            self.image_analysis_service
            .session_service
            .get_or_create_session(
                sender
            )
        )

        await (
            self.image_analysis_service
            .session_service
            .save_message(
                sender,
                role="farmer",
                message_type="image",
                content=(
                    "Farmer uploaded a tomato leaf image "
                    "for multi-image assessment."
                ),
            )
        )

        if caption:

            await (
                self.image_analysis_service
                .session_service
                .save_message(
                    sender,
                    role="farmer",
                    message_type="text",
                    content=caption,
                )
            )

        # =====================================================
        # 6. BATCH PROGRESS
        # =====================================================

        image_count = (
            await self.batch_service.count_images(
                batch_id
            )
        )

        image_position = stored_image[
            "image_position"
        ]

        logger.info(
            "[WhatsApp] Accepted batch image "
            f"{image_position}/{self.MAX_BATCH_IMAGES} "
        )

        # -----------------------------------------------------
        # Automatically finalize once three usable images
        # have been collected.
        # -----------------------------------------------------

        if (
            image_count
            >= self.MAX_BATCH_IMAGES
        ):

            await self.whatsapp_service.send_text_message(
                to=sender,
                text=(
                    "3 usable tomato-leaf photos were "
                    "received. KILIMO will analyse these "
                    "photos now. Additional photos from the "
                    "same upload will not be used."
                ),
            )

            await self._finalize_batch(
                sender=sender,
                batch_id=batch_id,
            )

            return

        remaining = (
            self.MAX_BATCH_IMAGES
            - image_count
        )

        if remaining == 1:

            progress_message = (
                f"Photo {image_count} received and accepted. "
                "You can send 1 more usable photo of the same "
                "affected tomato plant, or reply DONE to "
                "analyse the photos now."
            )

        else:

            progress_message = (
                f"Photo {image_count} received and accepted. "
                f"You can send up to {remaining} more usable "
                "photos of the same affected tomato plant, "
                "or reply DONE to analyse the photos now."
            )

        await self.whatsapp_service.send_text_message(
            to=sender,
            text=progress_message,
        )

    # =========================================================
    # FINALIZE MULTI-IMAGE BATCH
    # =========================================================

    async def _finalize_batch(
        self,
        sender: str,
        batch_id: int,
    ) -> None:
        """
        Perform disease inference for every accepted image,
        aggregate predictions, and produce one farmer-facing
        assessment.
        """

        claimed = (
            await self.batch_service.begin_processing(
                batch_id
            )
        )

        if not claimed:

            logger.info(
                "[WhatsApp] Batch finalization skipped "
                "because another worker already claimed "
            )

            return

        try:

            batch_images = (
                await self.batch_service.list_images(
                    batch_id
                )
            )

            usable_images = [
                item
                for item in batch_images
                if item.get(
                    "status"
                ) == "accepted"
            ]

            if not usable_images:

                await self.batch_service.cancel_batch(
                    batch_id
                )

                await self.whatsapp_service.send_text_message(
                    to=sender,
                    text=(
                        "There are no usable tomato-leaf "
                        "photos in this assessment. Please "
                        "send a clear photo and try again."
                    ),
                )

                return

            # =================================================
            # 1. INDIVIDUAL DISEASE INFERENCE
            # =================================================

            assessments: list[
                dict[str, Any]
            ] = []

            for batch_image in usable_images:

                stored_bytes = batch_image.get(
                    "image_bytes"
                )

                if not stored_bytes:
                    raise RuntimeError(
                        "Stored batch image bytes are missing."
                    )

                image = decode_batch_image(
                    bytes(
                        stored_bytes
                    )
                )

                assessment = (
                    self.image_analysis_service
                    .assessor
                    .assess(
                        image
                    )
                )

                assessment_data = (
                    assessment.to_dict()
                )

                # ---------------------------------------------
                # Healthy normalization
                # ---------------------------------------------

                if (
                    assessment_data[
                        "disease"
                    ]
                    == "Healthy"
                ):

                    assessment_data[
                        "severity_level"
                    ] = "None"

                    assessment_data[
                        "affected_area_percentage"
                    ] = 0.0

                assessments.append(
                    assessment_data
                )

            # =================================================
            # 2. AGGREGATION
            # =================================================

            aggregation = (
                aggregate_assessments(
                    assessments
                )
            )

            # =================================================
            # 3. DISAGREEMENT / ABSTENTION
            # =================================================

            if not aggregation.accepted:

                for batch_image in usable_images:

                    await (
                        self.batch_service
                        .mark_image_processed(
                            image_id=int(
                                batch_image["id"]
                            ),
                            assessment_id=None,
                        )
                    )

                await self.batch_service.mark_completed(
                    batch_id
                )

                response_text = aggregation.message

                await (
                    self.image_analysis_service
                    .session_service
                    .save_message(
                        sender,
                        role="system",
                        message_type="text",
                        content=response_text,
                    )
                )

                await self.whatsapp_service.send_text_message(
                    to=sender,
                    text=response_text,
                )

                return

            combined_assessment = (
                aggregation.assessment
            )

            if combined_assessment is None:
                raise RuntimeError(
                    "Accepted aggregation has no assessment."
                )

            # =================================================
            # 4. STRUCTURED ADVISORY
            # =================================================

            advisory = (
                self.image_analysis_service
                .advisory_engine
                .generate(
                    combined_assessment
                )
            )

            # =================================================
            # 5. PREVIOUS SESSION CONTEXT
            # =================================================

            session = (
                await self.image_analysis_service
                .session_service
                .get_session(
                    sender
                )
            )

            session_context = None

            if session is not None:

                session_context = session.get(
                    "context"
                )

                if isinstance(
                    session_context,
                    str,
                ):

                    try:

                        session_context = json.loads(
                            session_context
                        )

                    except json.JSONDecodeError:

                        session_context = None

            conversation_history = (
                await self.image_analysis_service
                .session_service
                .get_history(
                    sender,
                    limit=10,
                )
            )

            # =================================================
            # 6. FARMER-FACING RESPONSE
            # =================================================

            response_text = (
                await self.image_analysis_service
                .advisory_responder
                .generate(
                    advisory=advisory,
                    farmer_query=None,
                    conversation_history=(
                        conversation_history
                    ),
                    session_context=(
                        session_context
                    ),
                )
            )

            response_text = (
                response_text
                or ""
            ).strip()

            if not response_text:
                raise RuntimeError(
                    "Natural-language advisory was empty."
                )

            # Add a concise multi-image evidence statement.
            response_text = (
                f"Multi-image assessment "
                f"({aggregation.agreement_count}/"
                f"{aggregation.image_count} photos agreed):\n\n"
                f"{response_text}"
            )

            # =================================================
            # 7. SAVE ONE COMBINED ASSESSMENT
            # =================================================

            assessment_id = (
                await self.image_analysis_service
                .assessment_service
                .save_assessment(
                    phone_number=sender,
                    assessment=combined_assessment,
                    source="whatsapp",
                )
            )

            # =================================================
            # 8. UPDATE SESSION
            # =================================================

            full_assessment_context = {
                "disease":
                    combined_assessment[
                        "disease"
                    ],

                "confidence":
                    combined_assessment[
                        "confidence"
                    ],

                "severity":
                    combined_assessment[
                        "severity_level"
                    ],

                "affected_area_percentage":
                    combined_assessment[
                        "affected_area_percentage"
                    ],

                "label_index":
                    combined_assessment[
                        "label_index"
                    ],

                "all_scores":
                    combined_assessment[
                        "all_scores"
                    ],

                "image_count":
                    aggregation.image_count,

                "agreement_count":
                    aggregation.agreement_count,

                "agreement_ratio":
                    aggregation.agreement_ratio,

                "description":
                    advisory[
                        "description"
                    ],

                "symptoms":
                    advisory[
                        "symptoms"
                    ],

                "recommended_actions":
                    advisory[
                        "recommended_actions"
                    ],

                "prevention":
                    advisory[
                        "prevention"
                    ],

                "confidence_message":
                    advisory[
                        "confidence_message"
                    ],

                "urgency":
                    advisory[
                        "urgency"
                    ],
            }

            await (
                self.image_analysis_service
                .session_service
                .update_session(
                    sender,
                    disease=(
                        combined_assessment[
                            "disease"
                        ]
                    ),
                    severity=(
                        combined_assessment[
                            "severity_level"
                        ]
                    ),
                    confidence=(
                        combined_assessment[
                            "confidence"
                        ]
                    ),
                    context={
                        "last_assessment":
                            full_assessment_context,

                        "last_advisory":
                            advisory,
                    },
                )
            )

            # =================================================
            # 9. SAVE SYSTEM RESPONSE
            # =================================================

            await (
                self.image_analysis_service
                .session_service
                .save_message(
                    sender,
                    role="system",
                    message_type="text",
                    content=response_text,
                )
            )

            # =================================================
            # 10. LINK IMAGES TO COMBINED ASSESSMENT
            # =================================================

            for batch_image in usable_images:

                await (
                    self.batch_service
                    .mark_image_processed(
                        image_id=int(
                            batch_image[
                                "id"
                            ]
                        ),
                        assessment_id=assessment_id,
                    )
                )

            # =================================================
            # 11. COMPLETE BATCH
            # =================================================

            await self.batch_service.mark_completed(
                batch_id
            )

            # =================================================
            # 12. SEND RESULT
            # =================================================

            await self.whatsapp_service.send_text_message(
                to=sender,
                text=response_text,
            )
            logger.info(
                "Multi-image assessment completed successfully "
                "using %s image(s).",
                aggregation.image_count,
            )

        except Exception:

            # -------------------------------------------------
            # A failed finalization must not leave the batch
            # permanently stuck in processing.
            #
            # The current service supports cancellation rather
            # than a failed state, so close it safely and allow
            # the farmer to start another assessment.
            # -------------------------------------------------

            try:

                await self.batch_service.cancel_batch(
                    batch_id
                )

            except Exception as cleanup_exc:

                logger.warning(
                    "[WhatsApp] Could not clean up a failed image batch. "
                )

            raise