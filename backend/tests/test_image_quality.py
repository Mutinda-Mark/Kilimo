"""
Tests for the Sprint III image-quality gate.
"""

import numpy as np
from PIL import Image

from cv.image_quality import evaluate_image_quality


def _checkerboard_image(
    width: int = 512,
    height: int = 512,
) -> Image.Image:
    """
    Generate a high-detail synthetic image.

    This is useful for testing the quality algorithm without
    depending on external image files.
    """

    y, x = np.indices(
        (
            height,
            width,
        )
    )

    pattern = (
        (
            (x // 16)
            + (y // 16)
        )
        % 2
    )

    array = np.where(
        pattern[..., None] == 0,
        np.array(
            [40, 130, 50],
            dtype=np.uint8,
        ),
        np.array(
            [180, 220, 170],
            dtype=np.uint8,
        ),
    )

    return Image.fromarray(
        array.astype(
            np.uint8
        ),
        mode="RGB",
    )


def test_accepts_clear_image():

    image = _checkerboard_image()

    result = evaluate_image_quality(
        image,
        mime_type="image/jpeg",
        file_size_bytes=100_000,
    )

    assert result.accepted is True
    assert result.status == "accepted"
    assert result.reason is None


def test_rejects_blurred_or_featureless_image():

    image = Image.new(
        "RGB",
        (
            512,
            512,
        ),
        color=(
            120,
            120,
            120,
        ),
    )

    result = evaluate_image_quality(
        image,
        mime_type="image/jpeg",
        file_size_bytes=100_000,
    )

    assert result.accepted is False
    assert result.reason == "blur"


def test_rejects_dark_image():

    image = Image.new(
        "RGB",
        (
            512,
            512,
        ),
        color=(
            5,
            5,
            5,
        ),
    )

    result = evaluate_image_quality(
        image,
        mime_type="image/jpeg",
        file_size_bytes=100_000,
    )

    assert result.accepted is False
    assert result.reason == "too_dark"


def test_rejects_overexposed_image():

    image = Image.new(
        "RGB",
        (
            512,
            512,
        ),
        color=(
            250,
            250,
            250,
        ),
    )

    result = evaluate_image_quality(
        image,
        mime_type="image/jpeg",
        file_size_bytes=100_000,
    )

    assert result.accepted is False
    assert result.reason == "too_bright"


def test_rejects_small_image():

    image = Image.new(
        "RGB",
        (
            100,
            100,
        ),
        color=(
            100,
            150,
            100,
        ),
    )

    result = evaluate_image_quality(
        image,
        mime_type="image/jpeg",
        file_size_bytes=10_000,
    )

    assert result.accepted is False
    assert result.reason == "low_resolution"


def test_rejects_unsupported_mime_type():

    image = _checkerboard_image()

    result = evaluate_image_quality(
        image,
        mime_type="image/gif",
        file_size_bytes=100_000,
    )

    assert result.accepted is False
    assert result.reason == "unsupported_format"


def test_rejects_oversized_file():

    image = _checkerboard_image()

    result = evaluate_image_quality(
        image,
        mime_type="image/jpeg",
        file_size_bytes=20 * 1024 * 1024,
    )

    assert result.accepted is False
    assert result.reason == "file_too_large"