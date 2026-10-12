"""
Severity estimation utilities.

This module combines:
    1. Leaf segmentation
    2. Grad-CAM activation

to estimate the proportion of the detected leaf region
associated with strong model attention.

IMPORTANT:
This is an estimated severity measure, not ground-truth
biological disease severity. The current classification
dataset contains disease labels but does not contain
human-labelled severity percentages.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np


@dataclass
class SeverityResult:
    """
    Result returned by the severity estimator.
    """

    affected_area_percentage: float
    severity_level: str
    threshold: float
    affected_pixels: int
    leaf_pixels: int


def normalize_heatmap(heatmap: np.ndarray) -> np.ndarray:
    """
    Normalize a Grad-CAM heatmap to the range [0, 1].
    """

    heatmap = np.asarray(heatmap, dtype=np.float32)

    minimum = float(np.min(heatmap))
    maximum = float(np.max(heatmap))

    if maximum - minimum < 1e-8:
        return np.zeros_like(heatmap, dtype=np.float32)

    normalized = (heatmap - minimum) / (maximum - minimum)

    return normalized.astype(np.float32)


def resize_heatmap(
    heatmap: np.ndarray,
    target_shape: tuple[int, int]
) -> np.ndarray:
    """
    Resize Grad-CAM heatmap to match the leaf mask.

    Args:
        heatmap: Grad-CAM heatmap.
        target_shape: (height, width).

    Returns:
        Resized heatmap.
    """

    height, width = target_shape

    resized = cv2.resize(
        heatmap,
        (width, height),
        interpolation=cv2.INTER_LINEAR
    )

    return normalize_heatmap(resized)


def calculate_affected_area(
    leaf_mask: np.ndarray,
    heatmap: np.ndarray,
    activation_threshold: float = 0.5,
) -> tuple[float, int, int]:
    """
    Estimate the proportion of the leaf receiving strong
    Grad-CAM activation.

    Args:
        leaf_mask:
            Binary leaf mask.

        heatmap:
            Grad-CAM heatmap with values between 0 and 1.

        activation_threshold:
            Minimum Grad-CAM activation considered significant.

    Returns:
        affected_area_percentage,
        affected_pixels,
        leaf_pixels
    """

    # Ensure binary mask
    leaf_mask = (leaf_mask > 0).astype(np.uint8)

    # Resize heatmap to mask dimensions
    heatmap = resize_heatmap(
        heatmap,
        leaf_mask.shape
    )

    # Pixels belonging to the leaf
    leaf_pixels = leaf_mask > 0

    total_leaf_pixels = int(np.sum(leaf_pixels))

    if total_leaf_pixels == 0:
        return 0.0, 0, 0

    # Strong Grad-CAM activation
    activated_pixels = heatmap >= activation_threshold

    # Only count activation inside the leaf
    affected_pixels_mask = (
        leaf_pixels & activated_pixels
    )

    affected_pixels = int(
        np.sum(affected_pixels_mask)
    )

    affected_area_percentage = (
        affected_pixels / total_leaf_pixels
    ) * 100.0

    return (
        float(affected_area_percentage),
        affected_pixels,
        total_leaf_pixels,
    )


def classify_severity(
    affected_area_percentage: float,
) -> str:
    """
    Convert estimated affected area into a severity category.

    These thresholds are heuristic and should be calibrated
    against labelled severity data before being presented
    as validated biological severity measurements.

    Current thresholds:

        < 10%   -> Low
        10-30%  -> Moderate
        30-60%  -> High
        > 60%   -> Severe
    """

    if affected_area_percentage < 10:
        return "Low"

    if affected_area_percentage < 30:
        return "Moderate"

    if affected_area_percentage < 60:
        return "High"

    return "Severe"


def estimate_severity(
    leaf_mask: np.ndarray,
    heatmap: np.ndarray,
    activation_threshold: float = 0.5,
) -> SeverityResult:
    """
    Complete severity estimation pipeline.
    """

    (
        affected_percentage,
        affected_pixels,
        leaf_pixels,
    ) = calculate_affected_area(
        leaf_mask=leaf_mask,
        heatmap=heatmap,
        activation_threshold=activation_threshold,
    )

    severity_level = classify_severity(
        affected_percentage
    )

    return SeverityResult(
        affected_area_percentage=affected_percentage,
        severity_level=severity_level,
        threshold=activation_threshold,
        affected_pixels=affected_pixels,
        leaf_pixels=leaf_pixels,
    )


def create_severity_mask(
    leaf_mask: np.ndarray,
    heatmap: np.ndarray,
    activation_threshold: float = 0.5,
) -> np.ndarray:
    """
    Create a binary mask containing the estimated affected region.

    Returns:
        Binary NumPy array:
            1 = estimated affected area
            0 = everything else
    """

    leaf_mask = (leaf_mask > 0).astype(np.uint8)

    heatmap = resize_heatmap(
        heatmap,
        leaf_mask.shape
    )

    affected = (
        (leaf_mask > 0)
        & (heatmap >= activation_threshold)
    )

    return affected.astype(np.uint8)


def create_severity_overlay(
    image: np.ndarray,
    leaf_mask: np.ndarray,
    heatmap: np.ndarray,
    activation_threshold: float = 0.5,
) -> np.ndarray:
    """
    Create an OpenCV visualization of the estimated
    affected region.

    The estimated affected region is highlighted in red.
    """

    if image.dtype != np.uint8:
        image = np.clip(
            image * 255 if image.max() <= 1.0 else image,
            0,
            255
        ).astype(np.uint8)

    output = image.copy()

    affected_mask = create_severity_mask(
        leaf_mask,
        heatmap,
        activation_threshold
    )

    affected_pixels = affected_mask > 0

    # Highlight affected region
    output[affected_pixels] = (
        0.55 * output[affected_pixels]
        + 0.45 * np.array([255, 0, 0])
    ).astype(np.uint8)

    return output