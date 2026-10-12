"""
Shared configuration for the computer vision module.

Centralising everything here means the training script (Colab) and the
production inference module (local FastAPI) always agree on class names,
image sizes, and file paths.
"""

from pathlib import Path


# ── Class definitions ────────────────────────────────────────────────────────

# IMPORTANT:
# The order MUST match the order used when training the model.
#
# The current EfficientNet-B0 model was trained using 11 classes.

DISEASE_CLASSES: list[str] = [
    "Bacterial Spot",
    "Early Blight",
    "Late Blight",
    "Leaf Mold",
    "Septoria Leaf Spot",
    "Spider Mites / Two-Spotted Spider Mite",
    "Target Spot",
    "Tomato Yellow Leaf Curl Virus",
    "Tomato Mosaic Virus",
    "Healthy",
    "Powdery Mildew",
]

NUM_CLASSES: int = len(DISEASE_CLASSES)


# ── Dataset folder → canonical class name ───────────────────────────────────

FOLDER_TO_CLASS: dict[str, str] = {

    "Bacterial_spot":
        "Bacterial Spot",

    "Early_blight":
        "Early Blight",

    "Late_blight":
        "Late Blight",

    "Leaf_Mold":
        "Leaf Mold",

    "Septoria_leaf_spot":
        "Septoria Leaf Spot",

    "Spider_mites Two-spotted_spider_mite":
        "Spider Mites / Two-Spotted Spider Mite",

    "Target_Spot":
        "Target Spot",

    "Tomato_Yellow_Leaf_Curl_Virus":
        "Tomato Yellow Leaf Curl Virus",

    "Tomato_mosaic_virus":
        "Tomato Mosaic Virus",

    "healthy":
        "Healthy",

    "powdery_mildew":
        "Powdery Mildew",
}


# ── Model settings ───────────────────────────────────────────────────────────

IMAGE_SIZE: int = 224

MODEL_BACKBONE: str = "efficientnet_b0"


# ── File paths ────────────────────────────────────────────────────────────────

CV_DIR = Path(__file__).parent

WEIGHTS_DIR = CV_DIR / "weights"

DEFAULT_WEIGHTS_PATH = WEIGHTS_DIR / "best_model.pt"