"""
Advisory generation layer.

Combines the computer-vision assessment with structured
disease knowledge to produce a farmer-oriented advisory.
"""

from typing import Any

from nlp.knowledge import DISEASE_KNOWLEDGE


class AdvisoryEngine:
    """Generate structured advisory information."""

    def generate(
        self,
        assessment: dict[str, Any],
    ) -> dict[str, Any]:

        disease = assessment["disease"]
        confidence = float(
            assessment["confidence"]
        )

        severity = assessment["severity_level"]

        knowledge = DISEASE_KNOWLEDGE.get(disease)

        if knowledge is None:
            raise ValueError(
                f"No advisory information available for: {disease}"
            )

        confidence_message = self._confidence_message(
            confidence
        )

        urgency = self._urgency(
            disease=disease,
            severity=severity,
        )

        return {
            "disease": disease,
            "confidence": confidence,
            "severity": severity,
            "affected_area_percentage": assessment[
                "affected_area_percentage"
            ],
            "description": knowledge["description"],
            "symptoms": knowledge["symptoms"],
            "recommended_actions": knowledge["management"],
            "prevention": knowledge["prevention"],
            "confidence_message": confidence_message,
            "urgency": urgency,
        }

    @staticmethod
    def _confidence_message(
        confidence: float,
    ) -> str:

        if confidence >= 0.90:
            return (
                "The model is highly confident in this prediction."
            )

        if confidence >= 0.70:
            return (
                "The model has moderate confidence in this prediction."
            )

        return (
            "The model has lower confidence. "
            "Consider checking the plant manually or consulting "
            "an agricultural extension officer."
        )

    @staticmethod
    def _urgency(
        disease: str,
        severity: str,
    ) -> str:

        if disease == "Healthy":
            return "Monitor"

        if severity == "Severe":
            return "High"

        if severity == "High":
            return "High"

        if severity == "Moderate":
            return "Medium"

        return "Low"