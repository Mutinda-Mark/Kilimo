"""
Grad-CAM heatmap computation and overlay generation.

This module explains which regions of a tomato leaf image contributed
most strongly to the EfficientNet-B0 disease classification.

Grad-CAM is used for visual explanation. It is NOT treated as a direct
measurement of disease area. The severity estimation module combines
the Grad-CAM activation with a leaf mask and applies calibrated
thresholds.
"""

import io
import logging

import cv2
import numpy as np
import torch
from PIL import Image

from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget


logger = logging.getLogger(__name__)


def compute_gradcam(
    model: torch.nn.Module,
    input_tensor: torch.Tensor,
    target_class: int | None = None,
) -> np.ndarray:
    """
    Compute a Grad-CAM heatmap for one image.

    Args:
        model:
            Trained EfficientNet-B0 in evaluation mode.

        input_tensor:
            Preprocessed image tensor with shape:
            [1, 3, 224, 224].

        target_class:
            Class index to explain.
            If None, the predicted class is explained.

    Returns:
        A float32 NumPy array of shape [224, 224],
        with values normalized to [0, 1].
    """

    if not hasattr(model, "features"):
        raise RuntimeError(
            "The supplied model does not contain a 'features' "
            "module. Grad-CAM is configured for EfficientNet-B0."
        )

    if input_tensor.ndim != 4 or input_tensor.shape[0] != 1:
        raise ValueError(
            "Grad-CAM expects a single image tensor with shape "
            "[1, 3, H, W]."
        )

    model.eval()

    # EfficientNet-B0 final convolutional feature block.
    target_layers = [model.features[-1]]

    if target_class is not None:
        targets = [
            ClassifierOutputTarget(target_class)
        ]
    else:
        targets = None

    try:
        with GradCAM(
            model=model,
            target_layers=target_layers,
        ) as cam:

            grayscale_cam = cam(
                input_tensor=input_tensor,
                targets=targets,
            )

    except Exception as exc:
        logger.exception("Grad-CAM computation failed.")
        raise RuntimeError(
            f"Unable to compute Grad-CAM: {exc}"
        ) from exc

    heatmap = grayscale_cam[0]

    heatmap = np.asarray(
        heatmap,
        dtype=np.float32,
    )

    # Ensure numerical stability.
    heatmap = np.nan_to_num(
        heatmap,
        nan=0.0,
        posinf=1.0,
        neginf=0.0,
    )

    # Normalize to [0, 1].
    min_value = heatmap.min()
    max_value = heatmap.max()

    if max_value > min_value:
        heatmap = (
            heatmap - min_value
        ) / (
            max_value - min_value
        )
    else:
        heatmap = np.zeros_like(
            heatmap,
            dtype=np.float32,
        )

    logger.debug(
        "Grad-CAM generated: shape=%s min=%.4f max=%.4f",
        heatmap.shape,
        heatmap.min(),
        heatmap.max(),
    )

    return heatmap


def create_heatmap_overlay(
    pil_image: Image.Image,
    heatmap: np.ndarray,
    heatmap_alpha: float = 0.45,
) -> Image.Image:
    """
    Create a Grad-CAM heatmap overlay.

    Args:
        pil_image:
            Original PIL image.

        heatmap:
            Grad-CAM heatmap with values in [0, 1].

        heatmap_alpha:
            Strength of the heatmap overlay.

    Returns:
        RGB PIL image containing the heatmap overlay.
    """

    if not 0.0 <= heatmap_alpha <= 1.0:
        raise ValueError(
            "heatmap_alpha must be between 0.0 and 1.0."
        )

    if heatmap.ndim != 2:
        raise ValueError(
            "Heatmap must have shape [H, W]."
        )

    height, width = heatmap.shape

    image = pil_image.convert("RGB").resize(
        (width, height),
        Image.BILINEAR,
    )

    image_array = (
        np.asarray(
            image,
            dtype=np.float32,
        ) / 255.0
    )

    overlay = show_cam_on_image(
        img=image_array,
        mask=heatmap,
        use_rgb=True,
        colormap=cv2.COLORMAP_JET,
        image_weight=1.0 - heatmap_alpha,
    )

    return Image.fromarray(overlay)


def pil_to_jpeg_bytes(
    pil_image: Image.Image,
    quality: int = 85,
) -> bytes:
    """
    Convert a PIL image into JPEG bytes.
    """

    if not 1 <= quality <= 95:
        raise ValueError(
            "JPEG quality must be between 1 and 95."
        )

    buffer = io.BytesIO()

    pil_image.convert("RGB").save(
        buffer,
        format="JPEG",
        quality=quality,
    )

    return buffer.getvalue()