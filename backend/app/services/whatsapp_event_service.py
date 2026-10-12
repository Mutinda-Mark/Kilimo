"""
Database-backed WhatsApp webhook idempotency.

Meta may deliver the same WhatsApp webhook more than once.

This service ensures that a single WhatsApp message ID is not
processed multiple times by KILIMO.
"""

from __future__ import annotations

from app.db import get_pool


class WhatsAppEventService:
    """
    Track processing state of incoming WhatsApp messages.
    """

    async def claim_message(
        self,
        message_id: str,
        phone_number: str | None = None,
        message_type: str | None = None,
    ) -> bool:
        """
        Attempt to claim a WhatsApp message for processing.

        Returns:
            True:
                This worker successfully claimed the message.

            False:
                The message is already being processed or has
                already been completed.

        Failed messages may be reclaimed if Meta redelivers them.
        """

        message_id = (
            message_id or ""
        ).strip()

        if not message_id:
            return False

        pool = await get_pool()

        async with pool.acquire() as conn:

            # -------------------------------------------------
            # Try inserting a brand-new message first
            # -------------------------------------------------

            inserted = await conn.fetchval(
                """
                INSERT INTO whatsapp_messages (
                    message_id,
                    phone_number,
                    message_type,
                    status
                )
                VALUES ($1, $2, $3, 'processing')

                ON CONFLICT (message_id)
                DO NOTHING

                RETURNING message_id
                """,
                message_id,
                phone_number,
                message_type,
            )

            if inserted is not None:
                return True

            # -------------------------------------------------
            # Message already exists.
            #
            # Only allow another attempt if the previous
            # processing attempt explicitly failed.
            # -------------------------------------------------

            reclaimed = await conn.fetchval(
                """
                UPDATE whatsapp_messages

                SET
                    status = 'processing',
                    error_message = NULL,
                    updated_at = now()

                WHERE
                    message_id = $1
                    AND status = 'failed'

                RETURNING message_id
                """,
                message_id,
            )

            return reclaimed is not None

    async def mark_completed(
        self,
        message_id: str,
    ) -> None:
        """Mark message processing as successfully completed."""

        pool = await get_pool()

        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE whatsapp_messages

                SET
                    status = 'completed',
                    completed_at = now(),
                    updated_at = now(),
                    error_message = NULL

                WHERE message_id = $1
                """,
                message_id,
            )

    async def mark_failed(
        self,
        message_id: str,
        error_message: str,
    ) -> None:
        """Mark a WhatsApp message processing attempt as failed."""

        safe_error = (
            str(error_message)[:1000]
            if error_message
            else "Unknown processing error."
        )

        pool = await get_pool()

        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE whatsapp_messages

                SET
                    status = 'failed',
                    error_message = $2,
                    updated_at = now()

                WHERE message_id = $1
                """,
                message_id,
                safe_error,
            )