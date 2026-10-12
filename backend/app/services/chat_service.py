
from __future__ import annotations
import json
from typing import Any

from app.services.session_service import SessionService
from nlp.responder import AdvisoryResponder


class ChatService:
    """
    Shared text conversation service for KILIMO.

    Used by:
    - POST /chat
    - WhatsApp text messages

    This service does NOT perform a new disease diagnosis.

    Disease diagnosis happens through the image/CV pipeline.
    Text chat may only reuse a previous image assessment.
    """

    def __init__(
        self,
        session_service: SessionService,
        advisory_responder: AdvisoryResponder,
    ) -> None:
        self.session_service = session_service
        self.advisory_responder = advisory_responder

    async def process_message(
        self,
        phone_number: str,
        question: str,
    ) -> dict[str, Any]:

        phone_number = (phone_number or "").strip()
        question = (question or "").strip()

        if not phone_number:
            raise ValueError("Phone number is required.")

        if not question:
            raise ValueError("Question cannot be empty.")

        # -----------------------------------------------------
        # 1. Get or create farmer session
        # -----------------------------------------------------

        await self.session_service.get_or_create_session(
            phone_number
        )

        # -----------------------------------------------------
        # 2. Save farmer message
        # -----------------------------------------------------

        await self.session_service.save_message(
            phone_number=phone_number,
            role="farmer",
            message_type="text",
            content=question,
        )

        # -----------------------------------------------------
        # 3. Load farmer session
        # -----------------------------------------------------

        session_record = await self.session_service.get_session(
            phone_number
        )

        if session_record is None:
            raise RuntimeError(
                "Farmer session could not be loaded."
            )

        session = dict(session_record)

        # -----------------------------------------------------
        # 4. Load stored session context
        # -----------------------------------------------------

        context = session.get(
            "context"
        )

        # ---------------------------------------------------------
        # PostgreSQL JSONB may be returned either as a dictionary
        # or as JSON text depending on driver/configuration.
        # ---------------------------------------------------------

        if isinstance(
            context,
            str,
        ):
            try:

                context = json.loads(
                    context
                )

            except json.JSONDecodeError:

                context = {}

        elif not isinstance(
            context,
            dict,
        ):

            context = {}

        # -----------------------------------------------------
        # 5. Get conversation history
        # -----------------------------------------------------

        history_records = (
            await self.session_service.get_history(
                phone_number,
                limit=10,
            )
        )

        conversation_history = [
            dict(record)
            for record in history_records
        ]

        # -----------------------------------------------------
        # 6. Build advisory object
        # -----------------------------------------------------

        advisory = self._build_advisory(
            session=session,
            context=context,
        )

        print(
            "\n========== CHAT ADVISORY =========="
        )
        print(advisory)
        print(
            "===================================\n"
        )

        # -----------------------------------------------------
        # 7. Generate answer using responder + RAG
        # -----------------------------------------------------

        response_text = (
            await self.advisory_responder.generate(
                advisory=advisory,
                farmer_query=question,
                conversation_history=conversation_history,
                session_context=context,
            )
        )

        response_text = (
            response_text or ""
        ).strip()

        if not response_text:
            response_text = (
                "I could not generate a response. "
                "Please try again."
            )

        # -----------------------------------------------------
        # 8. Save KILIMO response
        # -----------------------------------------------------

        await self.session_service.save_message(
            phone_number=phone_number,
            role="system",
            message_type="text",
            content=response_text,
        )

        # -----------------------------------------------------
        # 9. Return response
        # -----------------------------------------------------

        return {
            "response": response_text,
            "session": {
                "phone_number": phone_number,
                "last_disease": session.get(
                    "last_disease"
                ),
                "last_severity": session.get(
                    "last_severity"
                ),
                "last_confidence": session.get(
                    "last_confidence"
                ),
            },
            "context": context,
        }

    def _build_advisory(
        self,
        session: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Build the advisory structure expected by AdvisoryResponder.

        Priority:

        1. Full last_assessment stored in context
        2. Disease information stored in session columns
        3. Safe no-diagnosis advisory
        """

        # =====================================================
        # CASE 1:
        # Full previous image assessment exists
        # =====================================================

        last_assessment = context.get(
            "last_assessment"
        )

        if isinstance(last_assessment, dict):

            disease = (
                last_assessment.get("disease")
                or "Unknown"
            )

            confidence = self._safe_float(
                last_assessment.get("confidence"),
                default=0.0,
            )

            severity = (
                last_assessment.get("severity")
                or "Unknown"
            )

            affected_area = self._safe_float(
                last_assessment.get(
                    "affected_area_percentage"
                ),
                default=0.0,
            )

            return {
                "disease": disease,
                "confidence": confidence,
                "severity": severity,
                "affected_area_percentage":
                    affected_area,

                "description": (
                    last_assessment.get(
                        "description"
                    )
                    or ""
                ),

                "symptoms": (
                    last_assessment.get(
                        "symptoms"
                    )
                    or []
                ),

                "recommended_actions": (
                    last_assessment.get(
                        "recommended_actions"
                    )
                    or []
                ),

                "prevention": (
                    last_assessment.get(
                        "prevention"
                    )
                    or []
                ),

                "confidence_message": (
                    last_assessment.get(
                        "confidence_message"
                    )
                    or (
                        "This information comes from "
                        "the farmer's previous tomato "
                        "leaf assessment."
                    )
                ),

                "urgency": (
                    last_assessment.get(
                        "urgency"
                    )
                    or "Low"
                ),
            }

        # =====================================================
        # CASE 2:
        # Session remembers a previous disease
        # =====================================================

        last_disease = session.get(
            "last_disease"
        )

        if last_disease:

            confidence = self._safe_float(
                session.get(
                    "last_confidence"
                ),
                default=0.0,
            )

            severity = (
                session.get(
                    "last_severity"
                )
                or "Unknown"
            )

            return {
                "disease": last_disease,

                "confidence": confidence,

                "severity": severity,

                "affected_area_percentage": 0.0,

                "description": "",

                "symptoms": [],

                "recommended_actions": [],

                "prevention": [],

                "confidence_message": (
                    "This disease information comes "
                    "from the farmer's previous image "
                    "assessment."
                ),

                "urgency": "Low",
            }

        # =====================================================
        # CASE 3:
        # No disease assessment exists
        # =====================================================

        return {
            "disease": "Unknown",

            "confidence": 0.0,

            "severity": "Unknown",

            "affected_area_percentage": 0.0,

            "description": (
                "No tomato disease image assessment "
                "has been performed yet."
            ),

            "symptoms": [],

            "recommended_actions": [],

            "prevention": [],

            "confidence_message": (
                "No image-based diagnosis is available. "
                "If the farmer wants a tomato disease "
                "assessment, ask them to send a clear "
                "photo of the affected tomato leaf."
            ),

            "urgency": "Low",
        }

    @staticmethod
    def _safe_float(
        value: Any,
        default: float = 0.0,
    ) -> float:
        """
        Safely convert database/context values to floats.

        Prevents errors such as:

        float(None)
        """

        if value is None:
            return default

        try:
            return float(value)

        except (TypeError, ValueError):
            return default