import io

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_predict_rejects_non_image_file():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/predict",
            files={
                "file": (
                    "test.txt",
                    b"This is not an image.",
                    "text/plain",
                )
            },
        )

    assert response.status_code == 400
    assert "must be an image" in response.json()["detail"]


@pytest.mark.asyncio
async def test_predict_rejects_empty_image():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
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

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_predict_rejects_corrupt_image():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/predict",
            files={
                "file": (
                    "corrupt.jpg",
                    b"this is not really a jpeg image",
                    "image/jpeg",
                )
            },
        )

    assert response.status_code == 400
    assert "valid image" in response.json()["detail"]


@pytest.mark.asyncio
async def test_predict_accepts_valid_image_format():
    # Create a tiny valid PNG in memory.
    from PIL import Image

    image = Image.new("RGB", (10, 10), "green")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/predict",
            files={
                "file": (
                    "tomato.png",
                    buffer.getvalue(),
                    "image/png",
                )
            },
        )

    # The request passed image validation. The actual result depends
    # on the installed model/database/LLM environment.
    assert response.status_code != 400