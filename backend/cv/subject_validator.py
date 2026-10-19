"""
Tomato-subject validation for KILIMO.

The subject validator determines whether a technically valid image
appears suitable for the tomato-disease classifier.

This is separate from image-quality validation:

    image quality
        -> "Can this image be analysed technically?"

    subject validation
        -> "Does this image appear to contain a supported tomato leaf?"

The disease classifier must only run after both checks succeed.

A dedicated binary model is used rather than relying on the maximum
softmax score of the closed-set disease classifier.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import torch
from PIL import Image
from torch import nn
from torchvision import models, transforms

from cv.config import (
    IMAGE_SIZE,
    SUBJECT_VALIDATOR_WEIGHTS_PATH,
)


@dataclass
class SubjectValidationResult:
    """
    Result returned by the tomato-subject validator.
    """

    accepted: bool

    status: str

    reason: str | None

    message: str

    tomato_score: float | None

    model_available: bool

    def to_dict(self) -> dict[str, Any]:
        """
        Convert result into a JSON-compatible dictionary.
        """

        return asdict(self)


class TomatoSubjectValidator:
    """
    Determine whether an image appears to contain a supported
    tomato leaf.

    The model is loaded lazily.

    Expected checkpoint:
        cv/weights/tomato_subject_validator.pt

    The checkpoint represents a binary classifier:

        0 -> unsupported image
        1 -> supported tomato leaf

    Thresholds must be selected during evaluation rather than
    treated as universal confidence boundaries.
    """

    def __init__(
        self,
        weights_path: str | Path = SUBJECT_VALIDATOR_WEIGHTS_PATH,
        *,
        supported_threshold: float = 0.70,
        unsupported_threshold: float = 0.30,
        device: str | None = None,
    ) -> None:

        self.weights_path = Path(
            weights_path
        )

        self.supported_threshold = float(
            supported_threshold
        )

        self.unsupported_threshold = float(
            unsupported_threshold
        )

        if not (
            0.0
            <= self.unsupported_threshold
            < self.supported_threshold
            <= 1.0
        ):
            raise ValueError(
                "Subject-validation thresholds must satisfy "
                "0 <= unsupported < supported <= 1."
            )

        self.device = (
            device
            or (
                "cuda"
                if torch.cuda.is_available()
                else "cpu"
            )
        )

        self._model: nn.Module | None = None

        self._transform = transforms.Compose(
            [
                transforms.Resize(
                    256
                ),
                transforms.CenterCrop(
                    IMAGE_SIZE
                ),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[
                        0.485,
                        0.456,
                        0.406,
                    ],
                    std=[
                        0.229,
                        0.224,
                        0.225,
                    ],
                ),
            ]
        )

    def is_ready(self) -> bool:
        """
        Return True when the trained subject-validation
        checkpoint exists.
        """

        return self.weights_path.exists()

    def _build_model(
        self,
    ) -> nn.Module:
        """
        Construct the binary MobileNetV3-Small architecture.
        """

        model = (
            models.mobilenet_v3_small(
                weights=None
            )
        )

        in_features = (
            model.classifier[-1].in_features
        )

        model.classifier[-1] = nn.Linear(
            in_features,
            1,
        )

        return model

    def get_model(
        self,
    ) -> nn.Module:
        """
        Lazily load the trained subject-validation model.
        """

        if self._model is not None:
            return self._model

        if not self.weights_path.exists():

            raise FileNotFoundError(
                "Tomato subject-validator weights were not "
                f"found at '{self.weights_path}'."
            )

        model = self._build_model()

        checkpoint = torch.load(
            self.weights_path,
            map_location=self.device,
        )

        if isinstance(
            checkpoint,
            dict,
        ) and "model_state_dict" in checkpoint:

            state_dict = checkpoint[
                "model_state_dict"
            ]

        else:

            state_dict = checkpoint

        model.load_state_dict(
            state_dict
        )

        model.to(
            self.device
        )

        model.eval()

        self._model = model

        return self._model

    def validate(
        self,
        image: Image.Image,
    ) -> SubjectValidationResult:
        """
        Validate whether an image appears to contain a
        supported tomato leaf.

        Returns one of:

            supported
            unsupported
            uncertain
        """

        if not isinstance(
            image,
            Image.Image,
        ):
            raise TypeError(
                "Subject validation requires a PIL image."
            )

        model = self.get_model()

        tensor = self._transform(
            image.convert(
                "RGB"
            )
        ).unsqueeze(
            0
        ).to(
            self.device
        )

        with torch.no_grad():

            logit = model(
                tensor
            ).squeeze()

            tomato_score = float(
                torch.sigmoid(
                    logit
                ).item()
            )

        tomato_score = round(
            tomato_score,
            4,
        )

        # -----------------------------------------------------
        # Supported
        # -----------------------------------------------------

        if (
            tomato_score
            >= self.supported_threshold
        ):

            return SubjectValidationResult(
                accepted=True,
                status="supported",
                reason=None,
                message=(
                    "Image passed the tomato-subject "
                    "validation check."
                ),
                tomato_score=tomato_score,
                model_available=True,
            )

        # -----------------------------------------------------
        # Unsupported
        # -----------------------------------------------------

        if (
            tomato_score
            <= self.unsupported_threshold
        ):

            return SubjectValidationResult(
                accepted=False,
                status="unsupported",
                reason="unsupported_subject",
                message=(
                    "This image does not appear to contain "
                    "a supported tomato leaf. Please send "
                    "a clear close-up photograph of the "
                    "affected tomato leaf."
                ),
                tomato_score=tomato_score,
                model_available=True,
            )

        # -----------------------------------------------------
        # Uncertain / abstention
        # -----------------------------------------------------

        return SubjectValidationResult(
            accepted=False,
            status="uncertain",
            reason="subject_uncertain",
            message=(
                "I could not confirm that this image is "
                "suitable for tomato disease assessment. "
                "Please retake the photo with one tomato "
                "leaf clearly visible and filling most of "
                "the image."
            ),
            tomato_score=tomato_score,
            model_available=True,
        )