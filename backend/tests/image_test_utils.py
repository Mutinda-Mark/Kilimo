"""
Reusable image utilities for KILIMO backend tests.

These helpers generate synthetic images with enough visual detail
to pass the Sprint III technical image-quality gate.

They are intended only for software-path testing.

They are NOT tomato-disease evaluation images and should never
be used to evaluate model accuracy or image-quality thresholds.
"""

from __future__ import annotations

from io import BytesIO

import numpy as np
from PIL import Image


def create_valid_test_image(
    width: int = 512,
    height: int = 512,
) -> Image.Image:
    """
    Create a synthetic RGB image with:

    - sufficient resolution
    - normal brightness
    - strong edge detail
    - supported RGB content

    The alternating blocks ensure the image does not appear
    featureless to the blur detector.
    """

    y, x = np.indices(
        (
            height,
            width,
        )
    )

    checkerboard = (
        (
            (x // 16)
            + (y // 16)
        )
        % 2
    )

    dark_green = np.array(
        [40, 115, 50],
        dtype=np.uint8,
    )

    light_green = np.array(
        [180, 220, 170],
        dtype=np.uint8,
    )

    array = np.where(
        checkerboard[..., None] == 0,
        dark_green,
        light_green,
    )

    return Image.fromarray(
        array.astype(np.uint8)
    ).convert("RGB")


def create_valid_test_image_bytes(
    image_format: str = "JPEG",
) -> bytes:
    """
    Return a quality-gate-compatible synthetic image as bytes.

    Args:
        image_format:
            PIL output format, normally JPEG or PNG.

    Returns:
        Encoded image bytes.
    """

    image = create_valid_test_image()

    buffer = BytesIO()

    normalized_format = (
        image_format
        or "JPEG"
    ).strip().upper()

    if normalized_format == "JPEG":

        image.save(
            buffer,
            format="JPEG",
            quality=95,
        )

    elif normalized_format == "PNG":

        image.save(
            buffer,
            format="PNG",
        )

    elif normalized_format == "WEBP":

        image.save(
            buffer,
            format="WEBP",
            quality=95,
        )

    else:

        raise ValueError(
            f"Unsupported test image format: "
            f"{image_format}"
        )

    return buffer.getvalue()