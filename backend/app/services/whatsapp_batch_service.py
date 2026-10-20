"""
Database-backed multi-image WhatsApp assessment batches.
"""

from __future__ import annotations

from typing import Any

from app.db import get_pool


class WhatsAppBatchService:
    """
    Persist and manage WhatsApp multi-image assessment batches.
    """

    DEFAULT_MAX_IMAGES = 3

    # =========================================================
    # ACTIVE BATCH
    # =========================================================

    async def get_active_batch(
        self,
        phone_number: str,
    ) -> dict[str, Any] | None:

        phone_number = (
            phone_number
            or ""
        ).strip()

        if not phone_number:
            raise ValueError(
                "Phone number is required."
            )

        pool = await get_pool()

        async with pool.acquire() as conn:

            row = await conn.fetchrow(
                """
                SELECT
                    id,
                    phone_number,
                    status,
                    max_images,
                    created_at,
                    updated_at,
                    expires_at,
                    completed_at

                FROM whatsapp_assessment_batches

                WHERE
                    phone_number = $1
                    AND status = 'collecting'
                    AND expires_at > now()

                ORDER BY created_at DESC

                LIMIT 1
                """,
                phone_number,
            )

        return (
            dict(row)
            if row is not None
            else None
        )

    async def get_or_create_active_batch(
        self,
        phone_number: str,
    ) -> dict[str, Any]:

        phone_number = (
            phone_number
            or ""
        ).strip()

        if not phone_number:
            raise ValueError(
                "Phone number is required."
            )

        pool = await get_pool()

        async with pool.acquire() as conn:

            async with conn.transaction():

                # Expire stale collecting batches first.
                await conn.execute(
                    """
                    UPDATE whatsapp_assessment_batches

                    SET
                        status = 'expired',
                        updated_at = now()

                    WHERE
                        phone_number = $1
                        AND status = 'collecting'
                        AND expires_at <= now()
                    """,
                    phone_number,
                )

                existing = await conn.fetchrow(
                    """
                    SELECT
                        id,
                        phone_number,
                        status,
                        max_images,
                        created_at,
                        updated_at,
                        expires_at,
                        completed_at

                    FROM whatsapp_assessment_batches

                    WHERE
                        phone_number = $1
                        AND status = 'collecting'
                        AND expires_at > now()

                    ORDER BY created_at DESC

                    LIMIT 1

                    FOR UPDATE
                    """,
                    phone_number,
                )

                if existing is not None:
                    return dict(
                        existing
                    )

                try:

                    created = await conn.fetchrow(
                        """
                        INSERT INTO whatsapp_assessment_batches (
                            phone_number,
                            status,
                            max_images
                        )

                        VALUES (
                            $1,
                            'collecting',
                            $2
                        )

                        RETURNING
                            id,
                            phone_number,
                            status,
                            max_images,
                            created_at,
                            updated_at,
                            expires_at,
                            completed_at
                        """,
                        phone_number,
                        self.DEFAULT_MAX_IMAGES,
                    )

                except Exception:

                    # Another concurrent request may have created
                    # the collecting batch after our SELECT.
                    created = await conn.fetchrow(
                        """
                        SELECT
                            id,
                            phone_number,
                            status,
                            max_images,
                            created_at,
                            updated_at,
                            expires_at,
                            completed_at

                        FROM whatsapp_assessment_batches

                        WHERE
                            phone_number = $1
                            AND status = 'collecting'
                            AND expires_at > now()

                        ORDER BY created_at DESC

                        LIMIT 1
                        """,
                        phone_number,
                    )

                    if created is None:
                        raise

                return dict(
                    created
                )

    # =========================================================
    # IMAGES
    # =========================================================

    async def list_images(
        self,
        batch_id: int,
    ) -> list[dict[str, Any]]:

        pool = await get_pool()

        async with pool.acquire() as conn:

            rows = await conn.fetch(
                """
                SELECT
                    id,
                    batch_id,
                    whatsapp_message_id,
                    media_id,
                    image_position,
                    mime_type,
                    original_file_size,
                    stored_file_size,
                    width,
                    height,
                    status,
                    rejection_reason,
                    tomato_score,
                    image_bytes,
                    assessment_id,
                    created_at,
                    updated_at

                FROM whatsapp_batch_images

                WHERE batch_id = $1

                ORDER BY image_position ASC
                """,
                batch_id,
            )

        return [
            dict(row)
            for row in rows
        ]

    async def count_images(
        self,
        batch_id: int,
    ) -> int:

        pool = await get_pool()

        async with pool.acquire() as conn:

            value = await conn.fetchval(
                """
                SELECT COUNT(*)

                FROM whatsapp_batch_images

                WHERE batch_id = $1
                """,
                batch_id,
            )

        return int(
            value
            or 0
        )

    async def add_image(
        self,
        *,
        batch_id: int,
        whatsapp_message_id: str,
        media_id: str | None,
        mime_type: str | None,
        original_file_size: int | None,
        stored_file_size: int | None,
        width: int | None,
        height: int | None,
        status: str,
        rejection_reason: str | None = None,
        tomato_score: float | None = None,
        image_bytes: bytes | None = None,
    ) -> dict[str, Any]:

        if status not in {
            "accepted",
            "rejected",
        }:
            raise ValueError(
                "Batch image status must be accepted or rejected."
            )

        message_id = (
            whatsapp_message_id
            or ""
        ).strip()

        if not message_id:
            raise ValueError(
                "WhatsApp message ID is required."
            )

        pool = await get_pool()

        async with pool.acquire() as conn:

            async with conn.transaction():

                batch = await conn.fetchrow(
                    """
                    SELECT
                        id,
                        status,
                        max_images

                    FROM whatsapp_assessment_batches

                    WHERE id = $1

                    FOR UPDATE
                    """,
                    batch_id,
                )

                if batch is None:
                    raise ValueError(
                        "Assessment batch does not exist."
                    )

                if batch["status"] != "collecting":
                    raise ValueError(
                        "Assessment batch is not collecting images."
                    )

                current_count = await conn.fetchval(
                    """
                    SELECT COUNT(*)

                    FROM whatsapp_batch_images

                    WHERE batch_id = $1
                    """,
                    batch_id,
                )

                current_count = int(
                    current_count
                    or 0
                )

                max_images = int(
                    batch["max_images"]
                )

                if current_count >= max_images:
                    raise ValueError(
                        "Assessment batch is already full."
                    )

                image_position = (
                    current_count
                    + 1
                )

                row = await conn.fetchrow(
                    """
                    INSERT INTO whatsapp_batch_images (
                        batch_id,
                        whatsapp_message_id,
                        media_id,
                        image_position,
                        mime_type,
                        original_file_size,
                        stored_file_size,
                        width,
                        height,
                        status,
                        rejection_reason,
                        tomato_score,
                        image_bytes
                    )

                    VALUES (
                        $1,
                        $2,
                        $3,
                        $4,
                        $5,
                        $6,
                        $7,
                        $8,
                        $9,
                        $10,
                        $11,
                        $12,
                        $13
                    )

                    ON CONFLICT (whatsapp_message_id)
                    DO NOTHING

                    RETURNING
                        id,
                        batch_id,
                        whatsapp_message_id,
                        media_id,
                        image_position,
                        mime_type,
                        original_file_size,
                        stored_file_size,
                        width,
                        height,
                        status,
                        rejection_reason,
                        tomato_score,
                        assessment_id,
                        created_at,
                        updated_at
                    """,
                    batch_id,
                    message_id,
                    media_id,
                    image_position,
                    mime_type,
                    original_file_size,
                    stored_file_size,
                    width,
                    height,
                    status,
                    rejection_reason,
                    tomato_score,
                    image_bytes,
                )

                if row is None:

                    existing = await conn.fetchrow(
                        """
                        SELECT
                            id,
                            batch_id,
                            whatsapp_message_id,
                            media_id,
                            image_position,
                            mime_type,
                            original_file_size,
                            stored_file_size,
                            width,
                            height,
                            status,
                            rejection_reason,
                            tomato_score,
                            assessment_id,
                            created_at,
                            updated_at

                        FROM whatsapp_batch_images

                        WHERE whatsapp_message_id = $1
                        """,
                        message_id,
                    )

                    if existing is None:
                        raise RuntimeError(
                            "Could not insert or recover batch image."
                        )

                    return dict(
                        existing
                    )

                await conn.execute(
                    """
                    UPDATE whatsapp_assessment_batches

                    SET updated_at = now()

                    WHERE id = $1
                    """,
                    batch_id,
                )

                return dict(
                    row
                )

    # =========================================================
    # FINALIZATION
    # =========================================================

    async def begin_processing(
        self,
        batch_id: int,
    ) -> bool:
        """
        Atomically claim a collecting batch for finalization.

        Returns True only for the worker that performs the
        collecting -> processing transition.
        """

        pool = await get_pool()

        async with pool.acquire() as conn:

            updated = await conn.fetchval(
                """
                UPDATE whatsapp_assessment_batches

                SET
                    status = 'processing',
                    updated_at = now()

                WHERE
                    id = $1
                    AND status = 'collecting'

                RETURNING id
                """,
                batch_id,
            )

        return updated is not None

    async def mark_completed(
        self,
        batch_id: int,
    ) -> None:

        pool = await get_pool()

        async with pool.acquire() as conn:

            await conn.execute(
                """
                UPDATE whatsapp_assessment_batches

                SET
                    status = 'completed',
                    completed_at = now(),
                    updated_at = now()

                WHERE id = $1
                """,
                batch_id,
            )

    async def mark_image_processed(
        self,
        image_id: int,
        assessment_id: int | None,
    ) -> None:

        pool = await get_pool()

        async with pool.acquire() as conn:

            await conn.execute(
                """
                UPDATE whatsapp_batch_images

                SET
                    status = 'processed',
                    assessment_id = $2,
                    updated_at = now()

                WHERE id = $1
                """,
                image_id,
                assessment_id,
            )

    async def cancel_batch(
        self,
        batch_id: int,
    ) -> None:

        pool = await get_pool()

        async with pool.acquire() as conn:

            await conn.execute(
                """
                UPDATE whatsapp_assessment_batches

                SET
                    status = 'cancelled',
                    updated_at = now()

                WHERE
                    id = $1
                    AND status IN (
                        'collecting',
                        'processing'
                    )
                """,
                batch_id,
            )
    async def get_open_batch(
        self,
        phone_number: str,
    ) -> dict[str, Any] | None:

        phone_number = (
            phone_number
            or ""
        ).strip()

        if not phone_number:
            raise ValueError(
                "Phone number is required."
            )

        pool = await get_pool()

        async with pool.acquire() as conn:

            row = await conn.fetchrow(
                """
                SELECT
                    id,
                    phone_number,
                    status,
                    max_images,
                    created_at,
                    updated_at,
                    expires_at,
                    completed_at

                FROM whatsapp_assessment_batches

                WHERE
                    phone_number = $1
                    AND status IN (
                        'collecting',
                        'processing'
                    )

                ORDER BY created_at DESC

                LIMIT 1
                """,
                phone_number,
            )

        return (
            dict(row)
            if row is not None
            else None
        )