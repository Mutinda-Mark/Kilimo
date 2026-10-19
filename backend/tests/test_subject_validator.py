"""
Tests for the tomato subject-validation component.

These tests currently verify the application contract and threshold
behaviour without claiming that the final trained validator has been
evaluated.
"""

import pytest
import torch

from cv.subject_validator import (
    TomatoSubjectValidator,
)
from tests.image_test_utils import (
    create_valid_test_image,
)


class FixedOutputModel(torch.nn.Module):
    """
    Tiny model used to produce a controlled binary logit.
    """

    def __init__(
        self,
        logit: float,
    ) -> None:

        super().__init__()

        self.logit = float(
            logit
        )

    def forward(
        self,
        tensor: torch.Tensor,
    ) -> torch.Tensor:

        batch_size = tensor.shape[0]

        return torch.full(
            (
                batch_size,
                1,
            ),
            self.logit,
            dtype=torch.float32,
            device=tensor.device,
        )


def _validator_with_logit(
    logit: float,
) -> TomatoSubjectValidator:
    """
    Create a validator whose model returns a fixed logit.
    """

    validator = TomatoSubjectValidator(
        supported_threshold=0.70,
        unsupported_threshold=0.30,
    )

    validator._model = (
        FixedOutputModel(
            logit
        ).to(
            validator.device
        )
    )

    return validator


def test_subject_validator_accepts_supported_score():

    validator = _validator_with_logit(
        2.0
    )

    result = validator.validate(
        create_valid_test_image()
    )

    assert result.accepted is True
    assert result.status == "supported"
    assert result.reason is None
    assert result.tomato_score is not None
    assert result.tomato_score >= 0.70


def test_subject_validator_rejects_unsupported_score():

    validator = _validator_with_logit(
        -2.0
    )

    result = validator.validate(
        create_valid_test_image()
    )

    assert result.accepted is False
    assert result.status == "unsupported"

    assert (
        result.reason
        == "unsupported_subject"
    )

    assert result.tomato_score is not None
    assert result.tomato_score <= 0.30


def test_subject_validator_abstains_on_uncertain_score():

    validator = _validator_with_logit(
        0.0
    )

    result = validator.validate(
        create_valid_test_image()
    )

    assert result.accepted is False
    assert result.status == "uncertain"

    assert (
        result.reason
        == "subject_uncertain"
    )

    assert result.tomato_score == 0.5


def test_subject_validator_requires_pil_image():

    validator = _validator_with_logit(
        2.0
    )

    with pytest.raises(
        TypeError
    ):

        validator.validate(
            b"not a PIL image"
        )


def test_subject_validator_validates_threshold_order():

    with pytest.raises(
        ValueError
    ):

        TomatoSubjectValidator(
            unsupported_threshold=0.80,
            supported_threshold=0.70,
        )