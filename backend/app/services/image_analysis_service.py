"""
Shared tomato image analysis pipeline for KILIMO.

Used by:
- POST /predict
- WhatsApp image messages

Responsibilities:
1. Create/retrieve farmer session
2. Save image/question history
3. Run CV assessment
4. Generate structured advisory
5. Save full assessment context
6. Retrieve conversation context
7. Generate RAG/Gemini response
8. Save system response
"""

from __future__ import annotations

import json
from typing import Any

from PIL import Image

from app.services.session_service import SessionService
from app.services.assessment_service import AssessmentService
from cv.image_quality import evaluate_image_quality
from cv.assessor import TomatoAssessor
from nlp.advisory import AdvisoryEngine
from nlp.responder import AdvisoryResponder


class ImageAnalysisService:
    """Run the complete KILIMO tomato image advisory pipeline."""

    def __init__(
        self,
        assessor: TomatoAssessor,
        advisory_engine: AdvisoryEngine,
        advisory_responder: AdvisoryResponder,
        session_service: SessionService,
        assessment_service: AssessmentService,
    ) -> None:
        self.assessor = assessor
        self.advisory_engine = advisory_engine
        self.advisory_responder = advisory_responder
        self.session_service = session_service
        self.assessment_service = assessment_service

    async def process_image(
        self,
        image: Image.Image,
        phone_number: str | None = None,
        question: str | None = None,
        image_history_content: str | None = None,
        source: str = "api",
        file_size_bytes: int | None = None,
        mime_type: str | None = None,
    ) -> dict[str, Any]:
        """
        Run the complete tomato image assessment pipeline.

        Args:
            image:
                PIL RGB image.

            phone_number:
                Optional farmer phone number.

            question:
                Optional farmer question/caption.

            image_history_content:
                Text stored alongside the image event in history.

        Returns:
            Dictionary containing:
            - prediction
            - severity
            - advisory
            - response
            - session
        """

        normalized_phone: str | None = None

        # =====================================================
        # 1. Normalize phone number
        # =====================================================

        if phone_number is not None:
            normalized_phone = phone_number.strip()

            if not normalized_phone:
                raise ValueError(
                    "Phone number cannot be empty."
                )

            await self.session_service.get_or_create_session(
                normalized_phone
            )

        # =====================================================
        # 2. Save farmer image/question
        # =====================================================

        if normalized_phone is not None:

            image_content = (
                image_history_content
                or "Farmer uploaded a tomato leaf image."
            )

            await self.session_service.save_message(
                normalized_phone,
                role="farmer",
                message_type="image",
                content=image_content,
            )

            if question and question.strip():
                await self.session_service.save_message(
                    normalized_phone,
                    role="farmer",
                    message_type="text",
                    content=question.strip(),
                )

        # =====================================================
        # 3. Computer vision assessment
        # =====================================================

                # =====================================================
        # 3. Image-quality validation
        # =====================================================

        quality_result = evaluate_image_quality(
            image,
            file_size_bytes=file_size_bytes,
            mime_type=mime_type,
        )

        quality_data = (
            quality_result.to_dict()
        )

        if not quality_result.accepted:

            rejection_message = (
                quality_result.message
            )

            # -------------------------------------------------
            # Save rejection feedback into conversation history
            # -------------------------------------------------

            if normalized_phone is not None:

                await self.session_service.save_message(
                    normalized_phone,
                    role="system",
                    message_type="text",
                    content=rejection_message,
                )

            # -------------------------------------------------
            # IMPORTANT:
            # Return before TomatoAssessor is called.
            # -------------------------------------------------

            return {
                "status": "rejected",
                "quality": quality_data,
                "prediction": None,
                "severity": None,
                "advisory": None,
                "response": rejection_message,
                "assessment_id": None,
                "session": {
                    "phone_number":
                        normalized_phone,

                    "enabled":
                        normalized_phone
                        is not None,
                },
            }

        # =====================================================
        # 4. Computer vision assessment
        # =====================================================

        assessment = self.assessor.assess(
            image
        )

        assessment_data = assessment.to_dict()
        # =====================================================
        # Normalize Healthy predictions
        # =====================================================
        #
        # Severity and affected-area estimation are disease-oriented
        # measurements. If the classifier predicts Healthy, the
        # Grad-CAM activation should not be presented as diseased
        # leaf area.

        if assessment_data["disease"] == "Healthy":
            assessment_data["severity_level"] = "None"
            assessment_data["affected_area_percentage"] = 0.0
        # =====================================================
        # Save historical assessment
        # =====================================================

        source = (source or "api").strip().lower()

        if source not in {
            "api",
            "whatsapp",
        }:
            source = "api"

        assessment_id = (
            await self.assessment_service.save_assessment(
                phone_number=normalized_phone,
                assessment=assessment_data,
                source=source,
            )
        )

        # =====================================================
        # 4. Structured advisory
        # =====================================================

        advisory = self.advisory_engine.generate(
            assessment_data
        )

        # =====================================================
        # 5. Save full assessment into session
        # =====================================================

        if normalized_phone is not None:

            full_assessment_context = {
                "disease": assessment_data[
                    "disease"
                ],

                "confidence": assessment_data[
                    "confidence"
                ],

                "severity": assessment_data[
                    "severity_level"
                ],

                "affected_area_percentage":
                    assessment_data[
                        "affected_area_percentage"
                    ],

                "label_index": assessment_data[
                    "label_index"
                ],

                "all_scores": assessment_data[
                    "all_scores"
                ],

                # Advisory information
                "description": advisory[
                    "description"
                ],

                "symptoms": advisory[
                    "symptoms"
                ],

                "recommended_actions": advisory[
                    "recommended_actions"
                ],

                "prevention": advisory[
                    "prevention"
                ],

                "confidence_message": advisory[
                    "confidence_message"
                ],

                "urgency": advisory[
                    "urgency"
                ],
            }

            await self.session_service.update_session(
                normalized_phone,
                disease=assessment_data[
                    "disease"
                ],
                severity=assessment_data[
                    "severity_level"
                ],
                confidence=assessment_data[
                    "confidence"
                ],
                context={
                    "last_assessment":
                        full_assessment_context,

                    "last_advisory":
                        advisory,
                },
            )

        # =====================================================
        # 6. Retrieve conversation/session context
        # =====================================================

        conversation_history = None
        session_context = None

        if normalized_phone is not None:

            session = (
                await self.session_service.get_session(
                    normalized_phone
                )
            )

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
                await self.session_service.get_history(
                    normalized_phone,
                    limit=10,
                )
            )

        # =====================================================
        # 7. Natural-language response
        # =====================================================

        response_text = (
            await self.advisory_responder.generate(
                advisory=advisory,
                farmer_query=question,
                conversation_history=conversation_history,
                session_context=session_context,
            )
        )

        response_text = (
            response_text or ""
        ).strip()

        if not response_text:
            raise RuntimeError(
                "Natural-language advisory was empty."
            )

        # =====================================================
        # 8. Save system response
        # =====================================================

        if normalized_phone is not None:

            await self.session_service.save_message(
                normalized_phone,
                role="system",
                message_type="text",
                content=response_text,
            )

        # =====================================================
        # 9. Return common result
        # =====================================================

        return {
            "assessment_id": assessment_id,
            "prediction": {
                "disease":
                    assessment_data[
                        "disease"
                    ],

                "confidence":
                    assessment_data[
                        "confidence"
                    ],

                "label_index":
                    assessment_data[
                        "label_index"
                    ],

                "all_scores":
                    assessment_data[
                        "all_scores"
                    ],
            },

            "severity": {
                "level":
                    assessment_data[
                        "severity_level"
                    ],

                "affected_area_percentage":
                    assessment_data[
                        "affected_area_percentage"
                    ],
            },

            "advisory": advisory,

            "response": response_text,

            "session": {
                "phone_number":
                    normalized_phone,

                "enabled":
                    normalized_phone
                    is not None,
            },
        }