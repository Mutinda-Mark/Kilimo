"""
Production inference module.

Exposes a single `TomatoPredictor` class that accepts:
  - a PIL.Image.Image
  - raw image bytes (e.g. downloaded from the WhatsApp Cloud API)
  - a file path (str or pathlib.Path)

and returns a structured prediction dict:

    {
        "disease":     "Early Blight",       # canonical label
        "confidence":  0.94,                 # 0.0 – 1.0
        "label_index": 0,                    # integer class index
        "all_scores": {                      # softmax probability for every class
            "Early Blight":       0.94,
            "Late Blight":        0.02,
            "Bacterial Spot":     0.01,
            ...
        }
    }

The model is loaded lazily on the first call to `predict()` so that
importing this module at startup (before weights have been downloaded)
does not crash the application.

Usage:
    predictor = TomatoPredictor()          # no weights loaded yet
    result = predictor.predict(image)      # weights loaded here on first call
"""

import io
import logging
from pathlib import Path
from typing import Union

import torch
from PIL import Image
from torchvision import transforms

from cv.config import DEFAULT_WEIGHTS_PATH, DISEASE_CLASSES, IMAGE_SIZE
from cv.model import load_checkpoint

logger = logging.getLogger(__name__)

# ── Preprocessing pipeline ────────────────────────────────────────────────────
#
# MUST match the validation transforms used during training (train_colab.py).
# Using the training augmentation here (random flips, colour jitter) would
# introduce non-determinism into production predictions.
#
# ImageNet mean/std are used because EfficientNet-B0 was pretrained on
# ImageNet; the fine-tuned model inherits those statistics.

_INFERENCE_TRANSFORM = transforms.Compose(
    [
        transforms.Resize(256),
        transforms.CenterCrop(IMAGE_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ]
)

ImageInput = Union[Image.Image, bytes, str, Path]


class TomatoPredictor:
    """
    Lazy-loading wrapper around the trained EfficientNet-B0 classifier.

    Args:
        weights_path: Path to the .pt checkpoint. Defaults to
                      cv/weights/best_model.pt.
        device:       "cpu" or "cuda". Defaults to "cuda" if a GPU is
                      available, otherwise "cpu".
    """

    def __init__(
        self,
        weights_path: Union[str, Path] = DEFAULT_WEIGHTS_PATH,
        device: str | None = None,
    ) -> None:
        self.weights_path = Path(weights_path)
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._model: torch.nn.Module | None = None  # loaded lazily

    # ── Public API ────────────────────────────────────────────────────────────

    def predict(self, image_input: ImageInput) -> dict:
        """
        Run disease classification on a single tomato leaf image.

        Args:
            image_input: A PIL image, raw JPEG/PNG bytes, or a file path.

        Returns:
            dict with keys: disease, confidence, label_index, all_scores.

        Raises:
            FileNotFoundError: If the weights file doesn't exist yet.
            ValueError: If the image cannot be decoded.
        """
        model = self.get_model()
        image = self._to_pil(image_input)
        tensor = self.preprocess(image)          # shape: [1, 3, 224, 224]

        with torch.no_grad():
            logits = model(tensor)                # shape: [1, NUM_CLASSES]
            probabilities = torch.softmax(logits, dim=1).squeeze()  # [NUM_CLASSES]

        confidence, label_index = probabilities.max(dim=0)
        label_index_int = label_index.item()

        return {
            "disease": DISEASE_CLASSES[label_index_int],
            "confidence": round(confidence.item(), 4),
            "label_index": label_index_int,
            "all_scores": {
                cls: round(probabilities[i].item(), 4)
                for i, cls in enumerate(DISEASE_CLASSES)
            },
        }

    def is_ready(self) -> bool:
        """Return True if the weights file exists and can be loaded."""
        return self.weights_path.exists()

    # ── Internal helpers ──────────────────────────────────────────────────────

       # ── Public model / preprocessing helpers ──────────────────────────────────

    def get_model(self) -> torch.nn.Module:
        """
        Load the model on first call (lazy load).

        Returns:
            Loaded EfficientNet-B0 model.
        """

        if self._model is not None:
            return self._model

        if not self.weights_path.exists():
            raise FileNotFoundError(
                f"Model weights not found at '{self.weights_path}'. "
                "Complete Phase 1 training in Google Colab, download "
                "best_model.pt, and place it in cv/weights/."
            )

        logger.info(
            "Loading CNN weights from %s onto %s",
            self.weights_path,
            self.device,
        )

        self._model = load_checkpoint(
            str(self.weights_path),
            device=self.device,
        )

        logger.info("CNN model loaded successfully.")

        return self._model

    @staticmethod
    def _to_pil(image_input: ImageInput) -> Image.Image:
        """Convert any supported input type to a PIL RGB image."""

        if isinstance(image_input, Image.Image):
            return image_input.convert("RGB")

        if isinstance(image_input, bytes):
            try:
                return Image.open(
                    io.BytesIO(image_input)
                ).convert("RGB")

            except Exception as exc:
                raise ValueError(
                    f"Could not decode image bytes: {exc}"
                ) from exc

        if isinstance(image_input, (str, Path)):

            path = Path(image_input)

            if not path.exists():
                raise FileNotFoundError(
                    f"Image file not found: {path}"
                )

            return Image.open(path).convert("RGB")

        raise TypeError(
            f"Unsupported image input type: {type(image_input)}. "
            "Expected PIL.Image, bytes, str, or pathlib.Path."
        )

    @staticmethod
    def preprocess(
        image: Image.Image,
    ) -> torch.Tensor:
        """
        Apply deterministic inference transforms.

        Returns:
            Tensor with shape [1, 3, 224, 224].
        """

        return _INFERENCE_TRANSFORM(
            image
        ).unsqueeze(0)