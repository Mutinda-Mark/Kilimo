"""
Tests for cv/predictor.py.

Tests cover:
1. Configuration and class consistency
2. Image input handling
3. Image preprocessing
4. Behaviour when weights are unavailable
5. Prediction using the trained 11-class model
6. Model caching
"""

import io

import pytest
import torch
from PIL import Image

from cv.config import DEFAULT_WEIGHTS_PATH, DISEASE_CLASSES, NUM_CLASSES
from cv.predictor import TomatoPredictor


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_green_pil_image(
    width: int = 256,
    height: int = 256,
) -> Image.Image:
    """Create a simple RGB image for predictor input tests."""
    import numpy as np

    rgb = np.zeros((height, width, 3), dtype=np.uint8)
    rgb[:, :, 1] = 120

    return Image.fromarray(rgb, mode="RGB")


def make_image_bytes(
    width: int = 256,
    height: int = 256,
) -> bytes:
    """Return JPEG bytes of a simple RGB image."""
    buf = io.BytesIO()

    make_green_pil_image(width, height).save(
        buf,
        format="JPEG",
    )

    return buf.getvalue()


# ── Configuration Tests ───────────────────────────────────────────────────────

class TestPredictorConfiguration:

    def test_config_class_count(self):
        """The production model must use exactly 11 classes."""
        assert NUM_CLASSES == 11
        assert len(DISEASE_CLASSES) == 11

    def test_config_class_order(self):
        """Class order must match the order used during model training."""

        expected = [
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

        assert DISEASE_CLASSES == expected


# ── Input Handling Tests ──────────────────────────────────────────────────────

class TestPredictorInputHandling:

    def test_to_pil_from_bytes(self):
        """_to_pil() accepts raw image bytes."""

        image = TomatoPredictor._to_pil(
            make_image_bytes()
        )

        assert image.mode == "RGB"
        assert image.size == (256, 256)

    def test_to_pil_from_pil(self):
        """_to_pil() accepts PIL images."""

        original = make_green_pil_image()

        result = TomatoPredictor._to_pil(original)

        assert result.mode == "RGB"
        assert result.size == original.size

    def test_to_pil_from_path(self, tmp_path):
        """_to_pil() accepts image file paths."""

        image_path = tmp_path / "test.jpg"

        make_green_pil_image().save(image_path)

        result = TomatoPredictor._to_pil(image_path)

        assert result.mode == "RGB"
        assert result.size == (256, 256)

    def test_to_pil_invalid_type_raises(self):
        """Unsupported input types raise TypeError."""

        with pytest.raises(TypeError):
            TomatoPredictor._to_pil(12345)

    def test_to_pil_bad_bytes_raises(self):
        """Invalid image bytes raise ValueError."""

        with pytest.raises(ValueError):
            TomatoPredictor._to_pil(b"not an image")


# ── Preprocessing Tests ───────────────────────────────────────────────────────

class TestPredictorPreprocessing:

    def test_preprocess_output_shape(self):
        """preprocess() returns a [1, 3, 224, 224] tensor."""

        tensor = TomatoPredictor.preprocess(
            make_green_pil_image()
        )

        assert tensor.shape == torch.Size(
            [1, 3, 224, 224]
        )

    def test_preprocess_returns_tensor(self):
        """preprocess() returns a PyTorch tensor."""

        tensor = TomatoPredictor.preprocess(
            make_green_pil_image()
        )

        assert isinstance(tensor, torch.Tensor)


# ── Tests Without Model Weights ───────────────────────────────────────────────

class TestPredictorWithoutWeights:

    def test_is_ready_false_when_no_weights(self, tmp_path):
        """is_ready() is False when weights are unavailable."""

        predictor = TomatoPredictor(
            weights_path=tmp_path / "nonexistent.pt"
        )

        assert predictor.is_ready() is False

    def test_predict_raises_file_not_found_without_weights(
        self,
        tmp_path,
    ):
        """predict() raises a clear error when weights are missing."""

        predictor = TomatoPredictor(
            weights_path=tmp_path / "nonexistent.pt"
        )

        with pytest.raises(
            FileNotFoundError,
            match="best_model.pt",
        ):
            predictor.predict(
                make_green_pil_image()
            )


# ── Tests With Model Weights ──────────────────────────────────────────────────

WEIGHTS_AVAILABLE = DEFAULT_WEIGHTS_PATH.exists()


@pytest.mark.skipif(
    not WEIGHTS_AVAILABLE,
    reason="best_model.pt not available",
)
class TestPredictorWithWeights:

    @pytest.fixture(scope="class")
    def predictor(self):
        return TomatoPredictor()

    def test_is_ready_true(self, predictor):
        """Predictor reports that the model is ready."""

        assert predictor.is_ready() is True

    def test_predict_from_pil(self, predictor):
        """Predictor accepts PIL images."""

        result = predictor.predict(
            make_green_pil_image()
        )

        _assert_valid_result(result)

    def test_predict_from_bytes(self, predictor):
        """Predictor accepts raw image bytes."""

        result = predictor.predict(
            make_image_bytes()
        )

        _assert_valid_result(result)

    def test_predict_from_path(self, predictor, tmp_path):
        """Predictor accepts file paths."""

        image_path = tmp_path / "leaf.jpg"

        make_green_pil_image().save(image_path)

        result = predictor.predict(image_path)

        _assert_valid_result(result)

    def test_prediction_contains_all_classes(self, predictor):
        """Prediction contains a score for every trained class."""

        result = predictor.predict(
            make_green_pil_image()
        )

        assert len(result["all_scores"]) == 11

        assert set(result["all_scores"].keys()) == set(
            DISEASE_CLASSES
        )

    def test_scores_are_valid_probabilities(self, predictor):
        """All class probabilities are between 0 and 1 and sum to 1."""

        result = predictor.predict(
            make_green_pil_image()
        )

        scores = list(
            result["all_scores"].values()
        )

        assert all(
            0.0 <= score <= 1.0
            for score in scores
        )

        assert abs(sum(scores) - 1.0) < 1e-3

    def test_model_is_cached(self, predictor):
        """Repeated predictions reuse the loaded model."""

        predictor.predict(
            make_green_pil_image()
        )

        model_ref = predictor._model

        predictor.predict(
            make_green_pil_image()
        )

        assert predictor._model is model_ref


# ── Shared Validation ─────────────────────────────────────────────────────────

def _assert_valid_result(result: dict) -> None:
    """Validate the structure of a prediction result."""

    assert "disease" in result
    assert "confidence" in result
    assert "label_index" in result
    assert "all_scores" in result

    assert result["disease"] in DISEASE_CLASSES

    assert 0.0 <= result["confidence"] <= 1.0

    assert 0 <= result["label_index"] < NUM_CLASSES

    assert set(result["all_scores"].keys()) == set(
        DISEASE_CLASSES
    )

    total = sum(
        result["all_scores"].values()
    )

    assert abs(total - 1.0) < 1e-3