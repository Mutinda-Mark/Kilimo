"""
Image-quality validation for KILIMO.

This module performs technical suitability checks before an image is
passed to the tomato disease classifier.

It does NOT determine whether the image contains a tomato leaf.
Subject suitability is handled separately by the tomato-leaf validation
module.

Checks currently include:
- supported MIME type, when available
- maximum file size, when available
- minimum pixel dimensions
- excessive darkness
- excessive brightness
- image blur / lack of edge detail

Images that fail these checks should not be passed to EfficientNet-B0.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
from PIL import Image

from cv.config import (
    MAX_IMAGE_BRIGHTNESS,
    MAX_IMAGE_FILE_SIZE_BYTES,
    MIN_IMAGE_BLUR_SCORE,
    MIN_IMAGE_BRIGHTNESS,
    MIN_IMAGE_HEIGHT,
    MIN_IMAGE_WIDTH,
    SUPPORTED_IMAGE_MIME_TYPES,
)


@dataclass
class ImageQualityResult:
    """
    Result returned by the image-quality validator.
    """

    accepted: bool
    status: str
    reason: str | None
    message: str

    width: int
    height: int

    brightness_score: float
    blur_score: float

    file_size_bytes: int | None = None
    mime_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the result into a JSON-compatible dictionary.
        """

        return asdict(self)


def _calculate_brightness(
    grayscale: np.ndarray,
) -> float:
    """
    Calculate mean grayscale intensity on a 0-255 scale.
    """

    return float(
        grayscale.mean()
    )


def _calculate_blur_score(
    grayscale: np.ndarray,
) -> float:
    """
    Estimate image sharpness using the variance of a discrete
    Laplacian response.

    Images containing more edge detail normally produce larger values.
    Very blurred or featureless images normally produce smaller values.

    This score is an operational quality metric rather than a calibrated
    measure of photographic quality.
    """

    if (
        grayscale.shape[0] < 3
        or grayscale.shape[1] < 3
    ):
        return 0.0

    center = grayscale[1:-1, 1:-1]

    laplacian = (
        grayscale[:-2, 1:-1]
        + grayscale[2:, 1:-1]
        + grayscale[1:-1, :-2]
        + grayscale[1:-1, 2:]
        - (4.0 * center)
    )

    return float(
        laplacian.var()
    )


def evaluate_image_quality(
    image: Image.Image,
    *,
    file_size_bytes: int | None = None,
    mime_type: str | None = None,
) -> ImageQualityResult:
    """
    Determine whether an image is technically suitable for
    disease inference.

    Args:
        image:
            Decoded PIL image.

        file_size_bytes:
            Original uploaded/downloaded image size when known.

        mime_type:
            MIME type reported by the input channel when known.

    Returns:
        ImageQualityResult describing whether the image should
        proceed to disease inference.
    """

    if not isinstance(
        image,
        Image.Image,
    ):
        raise TypeError(
            "Image-quality validation requires a PIL image."
        )

    normalized_mime = (
        mime_type.split(";")[0].strip().lower()
        if mime_type
        else None
    )

    width, height = image.size

    # ---------------------------------------------------------
    # 1. MIME type
    # ---------------------------------------------------------

    if (
        normalized_mime is not None
        and normalized_mime
        not in SUPPORTED_IMAGE_MIME_TYPES
    ):
        return ImageQualityResult(
            accepted=False,
            status="rejected",
            reason="unsupported_format",
            message=(
                "I couldn't analyse this image format. "
                "Please send a JPEG, PNG, or WebP photograph "
                "of the affected tomato leaf."
            ),
            width=width,
            height=height,
            brightness_score=0.0,
            blur_score=0.0,
            file_size_bytes=file_size_bytes,
            mime_type=normalized_mime,
        )

    # ---------------------------------------------------------
    # 2. File size
    # ---------------------------------------------------------

    if (
        file_size_bytes is not None
        and file_size_bytes
        > MAX_IMAGE_FILE_SIZE_BYTES
    ):
        return ImageQualityResult(
            accepted=False,
            status="rejected",
            reason="file_too_large",
            message=(
                "This image is too large to process reliably. "
                "Please send a smaller photograph of the "
                "affected tomato leaf."
            ),
            width=width,
            height=height,
            brightness_score=0.0,
            blur_score=0.0,
            file_size_bytes=file_size_bytes,
            mime_type=normalized_mime,
        )

    # ---------------------------------------------------------
    # 3. Minimum dimensions
    # ---------------------------------------------------------

    if (
        width < MIN_IMAGE_WIDTH
        or height < MIN_IMAGE_HEIGHT
    ):
        return ImageQualityResult(
            accepted=False,
            status="rejected",
            reason="low_resolution",
            message=(
                "This image is too small for a reliable "
                "assessment. Please send a clearer, "
                "higher-resolution photo of the affected leaf."
            ),
            width=width,
            height=height,
            brightness_score=0.0,
            blur_score=0.0,
            file_size_bytes=file_size_bytes,
            mime_type=normalized_mime,
        )

    # ---------------------------------------------------------
    # Convert once for brightness / blur analysis
    # ---------------------------------------------------------

    grayscale = np.asarray(
        image.convert("L"),
        dtype=np.float32,
    )

    brightness_score = round(
        _calculate_brightness(
            grayscale
        ),
        2,
    )

    # ---------------------------------------------------------
    # 4. Excessively dark
    # ---------------------------------------------------------

    if (
        brightness_score
        < MIN_IMAGE_BRIGHTNESS
    ):
        return ImageQualityResult(
            accepted=False,
            status="rejected",
            reason="too_dark",
            message=(
                "This photo is too dark for a reliable "
                "assessment. Please retake it in better "
                "lighting and make sure the leaf is clearly "
                "visible."
            ),
            width=width,
            height=height,
            brightness_score=brightness_score,
            blur_score=0.0,
            file_size_bytes=file_size_bytes,
            mime_type=normalized_mime,
        )

    # ---------------------------------------------------------
    # 5. Excessively bright
    # ---------------------------------------------------------

    if (
        brightness_score
        > MAX_IMAGE_BRIGHTNESS
    ):
        return ImageQualityResult(
            accepted=False,
            status="rejected",
            reason="too_bright",
            message=(
                "This photo is too bright for a reliable "
                "assessment. Please avoid strong direct light "
                "or glare and retake the image."
            ),
            width=width,
            height=height,
            brightness_score=brightness_score,
            blur_score=0.0,
            file_size_bytes=file_size_bytes,
            mime_type=normalized_mime,
        )

    blur_score = round(
        _calculate_blur_score(
            grayscale
        ),
        2,
    )

    # ---------------------------------------------------------
    # 6. Blur
    # ---------------------------------------------------------

    if blur_score < MIN_IMAGE_BLUR_SCORE:

        return ImageQualityResult(
            accepted=False,
            status="rejected",
            reason="blur",
            message=(
                "This photo appears too blurry for a reliable "
                "assessment. Please retake it with the camera "
                "steady and make sure the affected leaf is "
                "in focus."
            ),
            width=width,
            height=height,
            brightness_score=brightness_score,
            blur_score=blur_score,
            file_size_bytes=file_size_bytes,
            mime_type=normalized_mime,
        )

    # ---------------------------------------------------------
    # Accepted
    # ---------------------------------------------------------

    return ImageQualityResult(
        accepted=True,
        status="accepted",
        reason=None,
        message=(
            "Image passed the technical quality checks."
        ),
        width=width,
        height=height,
        brightness_score=brightness_score,
        blur_score=blur_score,
        file_size_bytes=file_size_bytes,
        mime_type=normalized_mime,
    )