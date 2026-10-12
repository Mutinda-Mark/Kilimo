"""
Manual Grad-CAM test.

Run:
    python tests/test_gradcam_manual.py

This verifies that:
    image -> EfficientNet -> prediction -> Grad-CAM -> overlay
works with the trained project model.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch
from PIL import Image

from cv.config import DEFAULT_WEIGHTS_PATH
from cv.gradcam import compute_gradcam, create_heatmap_overlay
from cv.model import load_checkpoint
from cv.predictor import TomatoPredictor


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

IMAGE_PATH = Path(
    "tests/sample_images/tomato.jpg"
)


# ------------------------------------------------------------
# Check image
# ------------------------------------------------------------

if not IMAGE_PATH.exists():
    raise FileNotFoundError(
        f"Test image not found: {IMAGE_PATH}\n"
        "Place a tomato leaf image there and run again."
    )


# ------------------------------------------------------------
# Device
# ------------------------------------------------------------

DEVICE = (
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)

print("Using device:", DEVICE)


# ------------------------------------------------------------
# Load model
# ------------------------------------------------------------

model = load_checkpoint(
    str(DEFAULT_WEIGHTS_PATH),
    device=DEVICE,
)

model.eval()

print("Model loaded successfully.")


# ------------------------------------------------------------
# Load image
# ------------------------------------------------------------

image = Image.open(
    IMAGE_PATH
).convert("RGB")


# ------------------------------------------------------------
# Use the same preprocessing as Predictor
# ------------------------------------------------------------

predictor = TomatoPredictor(
    weights_path=DEFAULT_WEIGHTS_PATH,
    device=DEVICE,
)

prediction = predictor.predict(image)

print("\nPrediction")
print("=" * 50)
print("Disease:", prediction["disease"])
print(
    "Confidence:",
    f"{prediction['confidence'] * 100:.2f}%"
)
print(
    "Class index:",
    prediction["label_index"]
)


# ------------------------------------------------------------
# Preprocess image
# ------------------------------------------------------------

input_tensor = predictor.preprocess(
    image
).to(DEVICE)


# ------------------------------------------------------------
# Compute Grad-CAM
# ------------------------------------------------------------

heatmap = compute_gradcam(
    model=model,
    input_tensor=input_tensor,
    target_class=prediction["label_index"],
)

print("\nGrad-CAM")
print("=" * 50)
print("Shape:", heatmap.shape)
print("Data type:", heatmap.dtype)
print("Minimum:", heatmap.min())
print("Maximum:", heatmap.max())


# ------------------------------------------------------------
# Create overlay
# ------------------------------------------------------------

overlay = create_heatmap_overlay(
    pil_image=image,
    heatmap=heatmap,
)


# ------------------------------------------------------------
# Display
# ------------------------------------------------------------

fig, axes = plt.subplots(
    1,
    2,
    figsize=(12, 5),
)

axes[0].imshow(image)
axes[0].set_title(
    f"Original\n{prediction['disease']}"
)
axes[0].axis("off")

axes[1].imshow(overlay)
axes[1].set_title(
    "Grad-CAM"
)
axes[1].axis("off")

plt.tight_layout()
plt.show()