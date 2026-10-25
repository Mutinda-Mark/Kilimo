"""
Image compression utilities for temporary WhatsApp batch storage.
"""

from __future__ import annotations

from io import BytesIO

from PIL import Image


MAX_BATCH_IMAGE_DIMENSION: int = 1280
BATCH_JPEG_QUALITY: int = 82


def compress_batch_image(
    image: Image.Image,
) -> tuple[bytes, int, int]:
    """
    Compress an image for temporary multi-image batch storage.

    Returns:
        compressed_bytes,
        stored_width,
        stored_height
    """

    if not isinstance(
        image,
        Image.Image,
    ):
        raise TypeError(
            "Batch image compression requires a PIL image."
        )

    working = image.convert(
        "RGB"
    )

    working.thumbnail(
        (
            MAX_BATCH_IMAGE_DIMENSION,
            MAX_BATCH_IMAGE_DIMENSION,
        ),
        Image.Resampling.LANCZOS,
    )

    output = BytesIO()

    working.save(
        output,
        format="JPEG",
        quality=BATCH_JPEG_QUALITY,
        optimize=True,
    )

    data = output.getvalue()

    return (
        data,
        working.width,
        working.height,
    )


def decode_batch_image(
    image_bytes: bytes,
) -> Image.Image:
    """
    Decode compressed batch-image bytes back into an RGB PIL image.
    """

    if not image_bytes:
        raise ValueError(
            "Stored batch image is empty."
        )

    with Image.open(
        BytesIO(
            image_bytes
        )
    ) as decoded:

        decoded.load()

        return decoded.convert(
            "RGB"
        )