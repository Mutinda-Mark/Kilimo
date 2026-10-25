"""
Database integration tests for WhatsApp multi-image batches.

These tests use the configured PostgreSQL database and verify the
real persistence/state-transition behaviour of WhatsAppBatchService.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.db import get_pool
from app.services.whatsapp_batch_service import (
    WhatsAppBatchService,
)


@pytest.mark.asyncio
async def test_whatsapp_batch_database_lifecycle():
    """
    Verify the real database-backed lifecycle:

    collecting
        -> image stored
        -> processing
        -> completed
    """

    service = WhatsAppBatchService()

    unique_id = uuid4().hex

    phone_number = (
        f"test-batch-{unique_id}"
    )

    message_id = (
        f"wamid-test-{unique_id}"
    )

    batch_id = None

    try:
        # =====================================================
        # 1. CREATE ACTIVE BATCH
        # =====================================================

        batch = (
            await service.get_or_create_active_batch(
                phone_number
            )
        )

        batch_id = int(
            batch["id"]
        )

        assert batch[
            "phone_number"
        ] == phone_number

        assert batch[
            "status"
        ] == "collecting"

        assert int(
            batch["max_images"]
        ) == 3

        # =====================================================
        # 2. SAME FARMER REUSES SAME COLLECTING BATCH
        # =====================================================

        same_batch = (
            await service.get_or_create_active_batch(
                phone_number
            )
        )

        assert int(
            same_batch["id"]
        ) == batch_id

        # =====================================================
        # 3. OPEN-BATCH LOOKUP
        # =====================================================

        open_batch = (
            await service.get_open_batch(
                phone_number
            )
        )

        assert open_batch is not None

        assert int(
            open_batch["id"]
        ) == batch_id

        assert (
            open_batch["status"]
            == "collecting"
        )

        # =====================================================
        # 4. STORE ACCEPTED IMAGE
        # =====================================================

        test_image_bytes = (
            b"kilimo-test-image-bytes"
        )

        stored = await service.add_image(
            batch_id=batch_id,
            whatsapp_message_id=message_id,
            media_id=(
                f"media-{unique_id}"
            ),
            mime_type="image/jpeg",
            original_file_size=50_000,
            stored_file_size=len(
                test_image_bytes
            ),
            width=640,
            height=480,
            status="accepted",
            rejection_reason=None,
            tomato_score=0.98,
            image_bytes=test_image_bytes,
        )

        assert int(
            stored["batch_id"]
        ) == batch_id

        assert (
            stored["whatsapp_message_id"]
            == message_id
        )

        assert (
            stored["image_position"]
            == 1
        )

        assert (
            stored["status"]
            == "accepted"
        )

        # =====================================================
        # 5. IMAGE COUNT
        # =====================================================

        image_count = (
            await service.count_images(
                batch_id
            )
        )

        assert image_count == 1

        # =====================================================
        # 6. RETRIEVE STORED IMAGE
        # =====================================================

        images = (
            await service.list_images(
                batch_id
            )
        )

        assert len(
            images
        ) == 1

        image_record = images[
            0
        ]

        assert (
            image_record[
                "image_position"
            ]
            == 1
        )

        assert (
            image_record[
                "tomato_score"
            ]
            == pytest.approx(
                0.98
            )
        )

        assert (
            bytes(
                image_record[
                    "image_bytes"
                ]
            )
            == test_image_bytes
        )

        # =====================================================
        # 7. COLLECTING -> PROCESSING
        # =====================================================

        claimed = (
            await service.begin_processing(
                batch_id
            )
        )

        assert claimed is True

        # A second worker must not be able to claim it.
        claimed_again = (
            await service.begin_processing(
                batch_id
            )
        )

        assert claimed_again is False

        # =====================================================
        # 8. PROCESSING IS STILL AN OPEN BATCH
        # =====================================================

        processing_batch = (
            await service.get_open_batch(
                phone_number
            )
        )

        assert (
            processing_batch
            is not None
        )

        assert (
            processing_batch[
                "status"
            ]
            == "processing"
        )

        # =====================================================
        # 9. PROCESSING -> COMPLETED
        # =====================================================

        await service.mark_completed(
            batch_id
        )

        # =====================================================
        # 10. COMPLETED BATCH IS NO LONGER OPEN
        # =====================================================

        closed_batch = (
            await service.get_open_batch(
                phone_number
            )
        )

        assert closed_batch is None

        # =====================================================
        # 11. VERIFY DATABASE STATUS DIRECTLY
        # =====================================================

        pool = await get_pool()

        async with pool.acquire() as conn:

            status = await conn.fetchval(
                """
                SELECT status

                FROM whatsapp_assessment_batches

                WHERE id = $1
                """,
                batch_id,
            )

        assert status == "completed"

    finally:
        # =====================================================
        # CLEANUP
        # =====================================================
        #
        # whatsapp_batch_images uses ON DELETE CASCADE, so
        # deleting the batch removes its test image as well.
        # =====================================================

        if batch_id is not None:

            pool = await get_pool()

            async with pool.acquire() as conn:

                await conn.execute(
                    """
                    DELETE FROM whatsapp_assessment_batches

                    WHERE id = $1
                    """,
                    batch_id,
                )