"""
Background processing for incoming WhatsApp farmer messages.

The actual webhook endpoint should acknowledge Meta quickly.

Heavy work such as:
- CV inference
- image downloads
- RAG
- Gemini generation

happens here after the HTTP response is sent.
"""

from __future__ import annotations

from io import BytesIO
from typing import Any

from PIL import Image, UnidentifiedImageError

from app.services.chat_service import ChatService
from app.services.image_analysis_service import ImageAnalysisService
from app.services.whatsapp_event_service import WhatsAppEventService
from app.whatsapp.service import WhatsAppService


class WhatsAppProcessor:
    """Process one already-claimed WhatsApp farmer message."""

    def __init__(
        self,
        whatsapp_service: WhatsAppService,
        chat_service: ChatService,
        image_analysis_service: ImageAnalysisService,
        event_service: WhatsAppEventService,
    ) -> None:

        self.whatsapp_service = whatsapp_service
        self.chat_service = chat_service
        self.image_analysis_service = image_analysis_service
        self.event_service = event_service

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
            # TEXT MESSAGE
            # =================================================

            if message_type == "text":

                await self._process_text(
                    sender=sender,
                    message=message,
                )

            # =================================================
            # IMAGE MESSAGE
            # =================================================

            elif message_type == "image":

                await self._process_image(
                    sender=sender,
                    message=message,
                )

            # =================================================
            # UNSUPPORTED MESSAGE
            # =================================================

            else:

                print(
                    f"[WhatsApp] Unsupported message type: "
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
            # Successfully completed
            # =================================================

            await self.event_service.mark_completed(
                message_id
            )

        except Exception as exc:

            print(
                "\n========== WHATSAPP PROCESSING ERROR =========="
            )

            print(
                f"Message ID: {message_id}"
            )

            print(
                repr(exc)
            )

            print(
                "===============================================\n"
            )

            if message_id:

                try:
                    await self.event_service.mark_failed(
                        message_id=message_id,
                        error_message=str(exc),
                    )

                except Exception as db_exc:
                    print(
                        "[WhatsApp] Could not mark "
                        f"message failed: {db_exc}"
                    )

            # Try sending a generic fallback only when a sender
            # is known.
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

                    print(
                        "[WhatsApp] Could not send "
                        f"fallback response: {send_exc}"
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

        print(
            f"[WhatsApp] Text from {sender}: "
            f"{incoming_text}"
        )

        result = await self.chat_service.process_message(
            phone_number=sender,
            question=incoming_text,
        )

        response_text = result["response"]

        print(
            "\n========== KILIMO RESPONSE =========="
        )

        print(
            response_text
        )

        print(
            "=====================================\n"
        )

        send_result = (
            await self.whatsapp_service.send_text_message(
                to=sender,
                text=response_text,
            )
        )

        print(
            "[WhatsApp] Text response sent:"
        )

        print(
            send_result
        )

    # =========================================================
    # IMAGE PROCESSING
    # =========================================================

    async def _process_image(
        self,
        sender: str,
        message: dict[str, Any],
    ) -> None:

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

        print(
            "\n========== WHATSAPP IMAGE =========="
        )

        print(
            f"Sender: {sender}"
        )

        print(
            f"Media ID: {media_id}"
        )

        print(
            f"MIME type: {mime_type}"
        )

        print(
            f"Caption: {caption}"
        )

        print(
            "====================================\n"
        )

        # -----------------------------------------------------
        # Download from Meta
        # -----------------------------------------------------

        media = (
            await self.whatsapp_service.download_media(
                media_id
            )
        )

        print(
            "\n========== MEDIA DOWNLOADED =========="
        )

        print(
            f"Media ID: {media.media_id}"
        )

        print(
            f"MIME type: {media.mime_type}"
        )

        print(
            f"Size: {media.file_size} bytes"
        )

        print(
            "======================================\n"
        )

        # -----------------------------------------------------
        # Convert to PIL
        # -----------------------------------------------------

        try:

            with Image.open(
                BytesIO(
                    media.content
                )
            ) as decoded_image:

                # Force the image to be decoded now so corrupt
                # image data fails before the inference pipeline.
                decoded_image.load()

                image = decoded_image.convert(
                    "RGB"
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

        # -----------------------------------------------------
        # Run shared KILIMO image pipeline
        # -----------------------------------------------------

        result = (
            await self.image_analysis_service.process_image(
                image=image,
                phone_number=sender,

                question=(
                    caption
                    if caption
                    else None
                ),

                image_history_content=(
                    "Farmer uploaded an image for assessment."
                ),

                source="whatsapp",

                file_size_bytes=media.file_size,

                mime_type=(
                    media.mime_type
                    or mime_type
                    or None
                ),
            )
        )

        # -----------------------------------------------------
        # Image rejected by quality gate
        # -----------------------------------------------------

        if result.get("status") == "rejected":

            quality = (
                result.get("quality")
                or {}
            )

            print(
                "\n========== IMAGE QUALITY REJECTED =========="
            )

            print(
                "Reason:",
                quality.get("reason"),
            )

            print(
                "Blur score:",
                quality.get("blur_score"),
            )

            print(
                "Brightness score:",
                quality.get("brightness_score"),
            )

            print(
                "Dimensions:",
                f"{quality.get('width')}x"
                f"{quality.get('height')}",
            )

            print(
                "============================================\n"
            )

            await self.whatsapp_service.send_text_message(
                to=sender,
                text=result["response"],
            )

            return

        prediction = result["prediction"]
        severity = result["severity"]

        print(
            "\n========== TOMATO ASSESSMENT =========="
        )

        print(
            "Disease:",
            prediction["disease"],
        )

        print(
            "Confidence:",
            prediction["confidence"],
        )

        print(
            "Severity:",
            severity["level"],
        )

        print(
            "Affected area:",
            severity[
                "affected_area_percentage"
            ],
        )

        print(
            "=======================================\n"
        )

        # -----------------------------------------------------
        # Send generated advisory
        # -----------------------------------------------------

        response_text = result["response"]

        send_result = (
            await self.whatsapp_service.send_text_message(
                to=sender,
                text=response_text,
            )
        )

        print(
            "\n========== WHATSAPP ADVISORY SENT =========="
        )

        print(
            send_result
        )

        print(
            "============================================\n"
        )