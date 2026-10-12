"""
Administrative reporting service for KILIMO.

Provides read-only operational information used by the
admin dashboard.
"""

from __future__ import annotations

import json
from typing import Any

from app.db import get_pool


class AdminService:
    """Read dashboard statistics from PostgreSQL."""

    async def get_summary(
        self,
    ) -> dict[str, Any]:
        """Return high-level dashboard statistics."""

        pool = await get_pool()

        async with pool.acquire() as conn:

            total_sessions = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM sessions
                """
            )

            total_messages = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM conversation_history
                """
            )

            total_assessments = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM assessments
                """
            )

            active_today = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM sessions
                WHERE last_active_at >= now() - INTERVAL '24 hours'
                """
            )

            average_confidence = await conn.fetchval(
                """
                SELECT AVG(confidence)
                FROM assessments
                """
            )

            latest_assessment = await conn.fetchrow(
                """
                SELECT
                    id,
                    phone_number,
                    disease,
                    confidence,
                    severity,
                    affected_area_percentage,
                    source,
                    created_at
                FROM assessments
                ORDER BY created_at DESC
                LIMIT 1
                """
            )

        return {
            "total_sessions": int(
                total_sessions or 0
            ),
            "total_messages": int(
                total_messages or 0
            ),
            "total_assessments": int(
                total_assessments or 0
            ),
            "active_sessions_24h": int(
                active_today or 0
            ),
            "average_confidence": (
                float(average_confidence)
                if average_confidence is not None
                else None
            ),
            "latest_assessment": (
                dict(latest_assessment)
                if latest_assessment
                else None
            ),
        }

    async def get_assessments(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Return recent historical assessments."""

        pool = await get_pool()

        async with pool.acquire() as conn:

            rows = await conn.fetch(
                """
                SELECT
                    id,
                    phone_number,
                    disease,
                    confidence,
                    severity,
                    affected_area_percentage,
                    label_index,
                    source,
                    created_at
                FROM assessments
                ORDER BY created_at DESC
                LIMIT $1
                OFFSET $2
                """,
                limit,
                offset,
            )

        return [
            dict(row)
            for row in rows
        ]

    async def get_assessment(
        self,
        *,
        assessment_id: int,
    ) -> dict[str, Any] | None:
        """Return one assessment by database ID."""

        pool = await get_pool()

        async with pool.acquire() as conn:

            row = await conn.fetchrow(
                """
                SELECT
                    id,
                    phone_number,
                    disease,
                    confidence,
                    severity,
                    affected_area_percentage,
                    label_index,
                    all_scores,
                    source,
                    created_at
                FROM assessments
                WHERE id = $1
                """,
                assessment_id,
            )

        if row is None:
            return None

        assessment = dict(row)

        # -----------------------------------------------------
        # Normalize JSONB all_scores
        # -----------------------------------------------------
        #
        # Depending on asyncpg / PostgreSQL configuration,
        # JSONB may be returned as either:
        #
        # - a Python dictionary
        # - a JSON-formatted string
        #
        # The frontend expects a dictionary/object.

        all_scores = assessment.get(
            "all_scores"
        )

        if isinstance(
            all_scores,
            str,
        ):
            try:
                all_scores = json.loads(
                    all_scores
                )

            except json.JSONDecodeError:
                all_scores = {}

        if not isinstance(
            all_scores,
            dict,
        ):
            all_scores = {}

        assessment[
            "all_scores"
        ] = all_scores

        return assessment

    async def get_sessions(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Return recent farmer sessions."""

        pool = await get_pool()

        async with pool.acquire() as conn:

            rows = await conn.fetch(
                """
                SELECT
                    phone_number,
                    language,
                    last_disease,
                    last_severity,
                    last_confidence,
                    last_active_at
                FROM sessions
                ORDER BY last_active_at DESC
                LIMIT $1
                OFFSET $2
                """,
                limit,
                offset,
            )

        return [
            dict(row)
            for row in rows
        ]

    async def get_history(
        self,
        *,
        phone_number: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Return conversation history for one farmer."""

        pool = await get_pool()

        async with pool.acquire() as conn:

            rows = await conn.fetch(
                """
                SELECT
                    id,
                    phone_number,
                    role,
                    message_type,
                    content,
                    created_at
                FROM conversation_history
                WHERE phone_number = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                phone_number,
                limit,
            )

        return [
            dict(row)
            for row in reversed(rows)
        ]

    async def get_disease_statistics(
        self,
    ) -> list[dict[str, Any]]:
        """Return assessment counts grouped by disease."""

        pool = await get_pool()

        async with pool.acquire() as conn:

            rows = await conn.fetch(
                """
                SELECT
                    disease,
                    COUNT(*) AS count,
                    AVG(confidence) AS average_confidence,
                    AVG(
                        affected_area_percentage
                    ) AS average_affected_area
                FROM assessments
                GROUP BY disease
                ORDER BY count DESC
                """
            )

        return [
            {
                "disease": row[
                    "disease"
                ],
                "count": int(
                    row["count"]
                ),
                "average_confidence": (
                    float(
                        row[
                            "average_confidence"
                        ]
                    )
                    if row[
                        "average_confidence"
                    ] is not None
                    else None
                ),
                "average_affected_area": (
                    float(
                        row[
                            "average_affected_area"
                        ]
                    )
                    if row[
                        "average_affected_area"
                    ] is not None
                    else None
                ),
            }
            for row in rows
        ]

    async def get_severity_statistics(
        self,
    ) -> list[dict[str, Any]]:
        """Return assessment counts grouped by severity."""

        pool = await get_pool()

        async with pool.acquire() as conn:

            rows = await conn.fetch(
                """
                SELECT
                    severity,
                    COUNT(*) AS count
                FROM assessments
                GROUP BY severity
                ORDER BY count DESC
                """
            )

        return [
            {
                "severity": row["severity"],
                "count": int(row["count"]),
            }
            for row in rows
        ]


    async def get_source_statistics(
        self,
    ) -> list[dict[str, Any]]:
        """Return assessment counts grouped by source."""

        pool = await get_pool()

        async with pool.acquire() as conn:

            rows = await conn.fetch(
                """
                SELECT
                    source,
                    COUNT(*) AS count
                FROM assessments
                GROUP BY source
                ORDER BY count DESC
                """
            )

        return [
            {
                "source": row["source"],
                "count": int(row["count"]),
            }
            for row in rows
        ]


    async def get_assessment_activity(
        self,
        *,
        days: int = 14,
    ) -> list[dict[str, Any]]:
        """
        Return daily assessment activity.

        Missing days are included with a count of zero.
        """

        pool = await get_pool()

        async with pool.acquire() as conn:

            rows = await conn.fetch(
                """
                WITH days AS (
                    SELECT generate_series(
                        CURRENT_DATE - ($1::integer - 1),
                        CURRENT_DATE,
                        INTERVAL '1 day'
                    )::date AS day
                ),
                counts AS (
                    SELECT
                        created_at::date AS day,
                        COUNT(*) AS count
                    FROM assessments
                    WHERE created_at >=
                        CURRENT_DATE - ($1::integer - 1)
                    GROUP BY created_at::date
                )
                SELECT
                    days.day,
                    COALESCE(counts.count, 0) AS count
                FROM days
                LEFT JOIN counts
                    ON counts.day = days.day
                ORDER BY days.day
                """,
                days,
            )

        return [
            {
                "date": row["day"].isoformat(),
                "count": int(row["count"]),
            }
            for row in rows
        ]

    async def get_whatsapp_statistics(
        self,
    ) -> dict[str, Any]:
        """Return WhatsApp processing statistics."""

        pool = await get_pool()

        async with pool.acquire() as conn:

            total = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM whatsapp_messages
                """
            )

            processing = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM whatsapp_messages
                WHERE status = 'processing'
                """
            )

            completed = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM whatsapp_messages
                WHERE status = 'completed'
                """
            )

            failed = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM whatsapp_messages
                WHERE status = 'failed'
                """
            )

            last_24h = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM whatsapp_messages
                WHERE received_at >=
                    now() - INTERVAL '24 hours'
                """
            )

        return {
            "total": int(total or 0),
            "processing": int(processing or 0),
            "completed": int(completed or 0),
            "failed": int(failed or 0),
            "received_24h": int(last_24h or 0),
        }


    async def get_recent_whatsapp_messages(
        self,
        *,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Return recently processed WhatsApp message records."""

        pool = await get_pool()

        async with pool.acquire() as conn:

            rows = await conn.fetch(
                """
                SELECT
                    message_id,
                    phone_number,
                    message_type,
                    status,
                    error_message,
                    received_at,
                    completed_at,
                    updated_at
                FROM whatsapp_messages
                ORDER BY received_at DESC
                LIMIT $1
                """,
                limit,
            )

        return [
            dict(row)
            for row in rows
        ]


    async def get_database_statistics(
        self,
    ) -> dict[str, Any]:
        """Return basic PostgreSQL record counts."""

        pool = await get_pool()

        async with pool.acquire() as conn:

            database_ok = (
                await conn.fetchval(
                    "SELECT 1"
                )
            ) == 1

            sessions = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM sessions
                """
            )

            conversations = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM conversation_history
                """
            )

            assessments = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM assessments
                """
            )

            whatsapp_messages = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM whatsapp_messages
                """
            )

        return {
            "connected": database_ok,
            "sessions": int(sessions or 0),
            "conversation_messages": int(
                conversations or 0
            ),
            "assessments": int(
                assessments or 0
            ),
            "whatsapp_messages": int(
                whatsapp_messages or 0
            ),
        }
