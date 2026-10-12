
from __future__ import annotations
import json

from typing import Any

from app.db import get_pool


class SessionService:
    """Handles farmer sessions and conversation history."""

    async def get_session(self, phone_number: str) -> dict[str, Any] | None:
        """Return an existing farmer session, or None if it does not exist."""
        phone_number = self._validate_phone_number(phone_number)

        pool = await get_pool()

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    phone_number,
                    language,
                    last_disease,
                    last_severity,
                    last_confidence,
                    context,
                    last_active_at
                FROM sessions
                WHERE phone_number = $1
                """,
                phone_number,
            )

        if row is None:
            return None

        return dict(row)

    async def create_session(
        self,
        phone_number: str,
        language: str = "en",
    ) -> dict[str, Any]:
        """Create a new farmer session."""
        phone_number = self._validate_phone_number(phone_number)

        if not language.strip():
            raise ValueError("Language cannot be empty.")

        pool = await get_pool()

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO sessions (
                    phone_number,
                    language
                )
                VALUES ($1, $2)
                ON CONFLICT (phone_number)
                DO UPDATE SET
                    last_active_at = now()
                RETURNING
                    phone_number,
                    language,
                    last_disease,
                    last_severity,
                    last_confidence,
                    context,
                    last_active_at
                """,
                phone_number,
                language.strip(),
            )

        return dict(row)

    async def get_or_create_session(
        self,
        phone_number: str,
        language: str = "en",
    ) -> dict[str, Any]:
        """Return an existing session or create one."""
        session = await self.get_session(phone_number)

        if session is not None:
            return session

        return await self.create_session(
            phone_number=phone_number,
            language=language,
        )

    async def update_session(
        self,
        phone_number: str,
        *,
        disease: str | None = None,
        severity: str | None = None,
        confidence: float | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update the current disease-related context for a farmer."""
        phone_number = self._validate_phone_number(phone_number)

        pool = await get_pool()
        context_json = (
            json.dumps(context)
            if context is not None
            else None
        )
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE sessions
                SET
                    last_disease = COALESCE($2, last_disease),
                    last_severity = COALESCE($3, last_severity),
                    last_confidence = COALESCE($4, last_confidence),
                    context = CASE
                        WHEN $5::jsonb IS NULL THEN context
                        ELSE context || $5::jsonb
                    END,
                    last_active_at = now()
                WHERE phone_number = $1
                RETURNING
                    phone_number,
                    language,
                    last_disease,
                    last_severity,
                    last_confidence,
                    context,
                    last_active_at
                """,
                phone_number,
                disease,
                severity,
                confidence,
                context_json,
            )

        if row is None:
            raise ValueError(
                f"No session exists for phone number: {phone_number}"
            )

        return dict(row)

    async def save_message(
        self,
        phone_number: str,
        *,
        role: str,
        message_type: str,
        content: str | None = None,
    ) -> dict[str, Any]:
        """Save a farmer or system message to conversation history."""
        phone_number = self._validate_phone_number(phone_number)

        if role not in {"farmer", "system"}:
            raise ValueError(
                "Role must be either 'farmer' or 'system'."
            )

        if message_type not in {"text", "image"}:
            raise ValueError(
                "Message type must be either 'text' or 'image'."
            )

        if message_type == "text" and (
            content is None or not content.strip()
        ):
            raise ValueError(
                "Text messages must contain content."
            )

        pool = await get_pool()

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO conversation_history (
                    phone_number,
                    role,
                    message_type,
                    content
                )
                VALUES ($1, $2, $3, $4)
                RETURNING
                    id,
                    phone_number,
                    role,
                    message_type,
                    content,
                    created_at
                """,
                phone_number,
                role,
                message_type,
                content,
            )

        return dict(row)

    async def get_history(
        self,
        phone_number: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Return recent conversation history, oldest message first."""
        phone_number = self._validate_phone_number(phone_number)

        if limit < 1:
            raise ValueError("History limit must be at least 1.")

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
                ORDER BY created_at DESC, id DESC
                LIMIT $2
                """,
                phone_number,
                limit,
            )

        # Database returns newest first; the application receives
        # the selected messages in normal conversational order.
        return [dict(row) for row in reversed(rows)]

    @staticmethod
    def _validate_phone_number(phone_number: str) -> str:
        """Basic validation for the session identifier."""
        if not phone_number or not phone_number.strip():
            raise ValueError("Phone number cannot be empty.")

        phone_number = phone_number.strip()

        if len(phone_number) > 50:
            raise ValueError("Phone number is too long.")

        return phone_number