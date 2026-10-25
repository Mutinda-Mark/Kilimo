import pytest

from httpx import (
    ASGITransport,
    AsyncClient,
)

from app.main import (
    app,
    image_analysis_service,
)
from cv.config import (
    MAX_IMAGE_FILE_SIZE_BYTES,
)


@pytest.mark.asyncio
async def test_predict_rejects_oversized_image_upload():

    oversized_content = (
        b"x"
        * (
            MAX_IMAGE_FILE_SIZE_BYTES
            + 1
        )
    )

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.post(
            "/predict",
            files={
                "file": (
                    "large.jpg",
                    oversized_content,
                    "image/jpeg",
                )
            },
        )

    assert (
        response.status_code
        == 413
    )

    assert (
        "maximum allowed size"
        in response.json()[
            "detail"
        ]
    )


@pytest.mark.asyncio
async def test_predict_rejects_empty_image_upload():

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.post(
            "/predict",
            files={
                "file": (
                    "empty.jpg",
                    b"",
                    "image/jpeg",
                )
            },
        )

    assert (
        response.status_code
        == 400
    )

    assert (
        response.json()[
            "detail"
        ]
        == "Uploaded image is empty."
    )


@pytest.mark.asyncio
async def test_predict_rejects_non_image_content_type():

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.post(
            "/predict",
            files={
                "file": (
                    "document.txt",
                    b"hello",
                    "text/plain",
                )
            },
        )

    assert (
        response.status_code
        == 400
    )

    assert (
        response.json()[
            "detail"
        ]
        == (
            "Uploaded file must be an image."
        )
    )


@pytest.mark.asyncio
async def test_predict_passes_file_metadata_to_pipeline(
    monkeypatch,
):

    from tests.image_test_utils import (
        create_valid_test_image_bytes,
    )

    image_bytes = (
        create_valid_test_image_bytes(
            image_format="JPEG"
        )
    )

    received = {}

    async def fake_process_image(
        *,
        image,
        phone_number=None,
        question=None,
        image_history_content=None,
        source="api",
        file_size_bytes=None,
        mime_type=None,
    ):
        received[
            "file_size_bytes"
        ] = file_size_bytes

        received[
            "mime_type"
        ] = mime_type

        received[
            "source"
        ] = source

        return {
            "status":
                "accepted"
        }

    monkeypatch.setattr(
        image_analysis_service,
        "process_image",
        fake_process_image,
    )

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.post(
            "/predict",
            files={
                "file": (
                    "tomato.jpg",
                    image_bytes,
                    "image/jpeg",
                )
            },
        )

    assert (
        response.status_code
        == 200
    )

    assert (
        response.json()[
            "status"
        ]
        == "accepted"
    )

    assert (
        received[
            "file_size_bytes"
        ]
        == len(
            image_bytes
        )
    )

    assert (
        received[
            "mime_type"
        ]
        == "image/jpeg"
    )

    assert (
        received[
            "source"
        ]
        == "api"
    )