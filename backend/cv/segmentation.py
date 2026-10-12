"""
Leaf segmentation utilities.

This module creates an approximate mask of the tomato leaf
from the input image. The mask is later used to estimate
the proportion of the leaf receiving strong Grad-CAM activation.

Note:
This is an image-processing based segmentation approach.
It is not a trained semantic segmentation model.
"""

from __future__ import annotations

from typing import Tuple

import cv2
import numpy as np
from PIL import Image


def segment_leaf(image: Image.Image) -> np.ndarray:
    """
    Create an approximate binary mask for the tomato leaf.

    Args:
        image: PIL RGB image.

    Returns:
        Binary NumPy array of shape (H, W).
        Leaf pixels = 1
        Background = 0
    """

    # Convert PIL image to RGB NumPy array
    rgb = np.array(image.convert("RGB"))

    # Convert RGB -> HSV
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)

    # Extract HSV channels
    hue = hsv[:, :, 0]
    saturation = hsv[:, :, 1]
    value = hsv[:, :, 2]

    # Basic green-leaf detection.
    #
    # OpenCV hue range is 0-179.
    green_mask = (
        (hue >= 20)
        & (hue <= 100)
        & (saturation >= 30)
        & (value >= 30)
    )

    mask = green_mask.astype(np.uint8) * 255

    # Remove small noise
    kernel = np.ones((5, 5), np.uint8)

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        kernel,
        iterations=1
    )

    # Fill small gaps inside the leaf
    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel,
        iterations=2
    )

    # Keep the largest connected region.
    # This helps remove small background objects/noise.
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        mask,
        connectivity=8
    )

    if num_labels > 1:
        largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])

        mask = np.where(
            labels == largest_label,
            255,
            0
        ).astype(np.uint8)

    return (mask > 0).astype(np.uint8)


def calculate_leaf_area(mask: np.ndarray) -> int:
    """
    Calculate the number of pixels belonging to the leaf.
    """

    return int(np.sum(mask > 0))


def calculate_leaf_percentage(mask: np.ndarray) -> float:
    """
    Calculate the percentage of the image occupied by the leaf.
    """

    total_pixels = mask.shape[0] * mask.shape[1]

    if total_pixels == 0:
        return 0.0

    leaf_pixels = calculate_leaf_area(mask)

    return (leaf_pixels / total_pixels) * 100.0


def resize_mask(
    mask: np.ndarray,
    size: Tuple[int, int] = (224, 224)
) -> np.ndarray:
    """
    Resize a segmentation mask.

    Args:
        mask: Binary mask.
        size: (width, height).

    Returns:
        Resized binary mask.
    """

    resized = cv2.resize(
        mask.astype(np.uint8),
        size,
        interpolation=cv2.INTER_NEAREST
    )

    return (resized > 0).astype(np.uint8)


def create_mask_overlay(
    image: Image.Image,
    mask: np.ndarray
) -> Image.Image:
    """
    Create a visualization showing the detected leaf region.

    The mask is displayed as a semi-transparent overlay.
    """

    rgb = np.array(image.convert("RGB"))

    # Resize mask if necessary
    if mask.shape[:2] != rgb.shape[:2]:
        mask = resize_mask(
            mask,
            (rgb.shape[1], rgb.shape[0])
        )

    overlay = rgb.copy()

    # Highlight leaf pixels
    leaf_pixels = mask > 0

    # Blend the original image with a green overlay
    overlay[leaf_pixels] = (
        0.65 * overlay[leaf_pixels]
        + 0.35 * np.array([0, 255, 0])
    ).astype(np.uint8)

    return Image.fromarray(overlay)