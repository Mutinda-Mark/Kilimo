"""
Tomato assessment pipeline.

Combines:
    - Disease classification
    - Confidence score
    - Grad-CAM
    - Leaf segmentation
    - Severity estimation

This module provides one high-level interface that can
later be called by the FastAPI backend.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from PIL import Image

from cv.gradcam import compute_gradcam
from cv.predictor import TomatoPredictor
from cv.segmentation import segment_leaf
from cv.severity import estimate_severity


@dataclass
class TomatoAssessment:
    """
    Complete assessment returned by the system.
    """

    disease: str
    confidence: float
    label_index: int

    affected_area_percentage: float
    severity_level: str

    leaf_pixels: int
    affected_pixels: int

    activation_threshold: float

    all_scores: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the assessment into a JSON-compatible dictionary.
        """

        return asdict(self)


class TomatoAssessor:
    """
    High-level tomato disease assessment service.

    The predictor is loaded once and reused for subsequent
    assessments.
    """

    def __init__(
        self,
        predictor: TomatoPredictor | None = None,
        activation_threshold: float = 0.5,
    ) -> None:

        self.predictor = predictor or TomatoPredictor()

        self.activation_threshold = activation_threshold

    def assess(
        self,
        image: Image.Image,
    ) -> TomatoAssessment:
        """
        Run the complete tomato assessment pipeline.

        Args:
            image:
                PIL RGB image.

        Returns:
            TomatoAssessment containing disease,
            confidence and severity information.
        """

        # --------------------------------------------------
        # 1. Disease prediction
        # --------------------------------------------------

        prediction = self.predictor.predict(image)

        disease = prediction["disease"]
        confidence = float(prediction["confidence"])
        label_index = int(prediction["label_index"])
        all_scores = prediction["all_scores"]

        # --------------------------------------------------
        # 2. Access loaded model
        # --------------------------------------------------

        model = self.predictor.get_model()

        # --------------------------------------------------
        # 3. Prepare image for Grad-CAM
        # --------------------------------------------------

        input_tensor = self.predictor.preprocess(image)

        # --------------------------------------------------
        # 4. Generate Grad-CAM
        # --------------------------------------------------

        heatmap = compute_gradcam(
            model=model,
            input_tensor=input_tensor,
            target_class=label_index,
        )

        # --------------------------------------------------
        # 5. Segment leaf
        # --------------------------------------------------

        leaf_mask = segment_leaf(image)

        # --------------------------------------------------
        # 6. Estimate severity
        # --------------------------------------------------

        severity = estimate_severity(
            leaf_mask=leaf_mask,
            heatmap=heatmap,
            activation_threshold=self.activation_threshold,
        )

        # --------------------------------------------------
        # 7. Return combined result
        # --------------------------------------------------

        return TomatoAssessment(
            disease=disease,
            confidence=confidence,
            label_index=label_index,
            affected_area_percentage=(
                severity.affected_area_percentage
            ),
            severity_level=severity.severity_level,
            leaf_pixels=severity.leaf_pixels,
            affected_pixels=severity.affected_pixels,
            activation_threshold=severity.threshold,
            all_scores=all_scores,
        )