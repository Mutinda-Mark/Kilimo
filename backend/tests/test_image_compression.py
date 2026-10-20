from PIL import Image

from app.services.image_compression import (
    MAX_BATCH_IMAGE_DIMENSION,
    compress_batch_image,
    decode_batch_image,
)


def test_compress_batch_image_returns_jpeg_bytes():

    image = Image.new(
        "RGB",
        (
            800,
            600,
        ),
        color=(
            90,
            140,
            80,
        ),
    )

    data, width, height = (
        compress_batch_image(
            image
        )
    )

    assert data
    assert width == 800
    assert height == 600


def test_compress_batch_image_limits_longest_edge():

    image = Image.new(
        "RGB",
        (
            2400,
            1600,
        ),
        color=(
            90,
            140,
            80,
        ),
    )

    data, width, height = (
        compress_batch_image(
            image
        )
    )

    assert data

    assert max(
        width,
        height,
    ) <= MAX_BATCH_IMAGE_DIMENSION


def test_decode_batch_image_round_trip():

    original = Image.new(
        "RGB",
        (
            640,
            480,
        ),
        color=(
            90,
            140,
            80,
        ),
    )

    data, _, _ = (
        compress_batch_image(
            original
        )
    )

    restored = decode_batch_image(
        data
    )

    assert restored.mode == "RGB"

    assert restored.size == (
        640,
        480,
    )