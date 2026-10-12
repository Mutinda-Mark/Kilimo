"""
Assessment persistence service.

Stores every tomato image assessment performed by KILIMO.

This is separate from session context:

- session context stores the latest assessment
- assessments table stores historical assessments
"""

from __future__ import annotations

import json
from typing import Any

from app.db import get_pool


class AssessmentService:
    """Persist and retrieve tomato disease assessments."""

    async def save_assessment(
        self,
        *,
        phone_number: str | None,
        assessment: dict[str, Any],
        source: str = "api",
    ) -> int:
        """
        Save one completed tomato disease assessment.

        Returns the database assessment ID.
        """

        disease = str(
            assessment["disease"]
        )

        confidence = float(
            assessment["confidence"]
        )

        severity = str(
            assessment["severity_level"]
        )

        affected_area = float(
            assessment["affected_area_percentage"]
        )

        label_index = assessment.get(
            "label_index"
        )

        all_scores = assessment.get(
            "all_scores",
            {},
        )

        pool = await get_pool()

        async with pool.acquire() as conn:

            assessment_id = await conn.fetchval(
                """
                INSERT INTO assessments (
                    phone_number,
                    disease,
                    confidence,
                    severity,
                    affected_area_percentage,
                    label_index,
                    all_scores,
                    source
                )
                VALUES (
                    $1,
                    $2,
                    $3,
                    $4,
                    $5,
                    $6,
                    $7::jsonb,
                    $8
                )
                RETURNING id
                """,
                phone_number,
                disease,
                confidence,
                severity,
                affected_area,
                label_index,
                json.dumps(all_scores),
                source,
            )

        return int(
            assessment_id
        )