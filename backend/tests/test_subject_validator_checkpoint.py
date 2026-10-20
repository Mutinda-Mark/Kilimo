"""
Smoke tests for the trained KILIMO tomato subject-validator
checkpoint.

These tests verify production integration properties only.

They do not evaluate subject-validator accuracy. Final model
performance was evaluated separately using the frozen V3
held-out test split.
"""

from PIL import Image

from cv.subject_validator import (
    TomatoSubjectValidator,
)


def test_subject_validator_checkpoint_exists():

    validator = (
        TomatoSubjectValidator()
    )

    assert (
        validator.is_ready()
        is True
    )


def test_subject_validator_checkpoint_loads():

    validator = (
        TomatoSubjectValidator()
    )

    model = (
        validator.get_model()
    )

    assert model is not None


def test_subject_validator_returns_valid_score():

    validator = (
        TomatoSubjectValidator()
    )

    # Synthetic image used only as a runtime smoke test.
    # No semantic classification expectation is asserted.
    image = Image.new(
        "RGB",
        (
            512,
            512,
        ),
        color=(
            80,
            130,
            70,
        ),
    )

    result = (
        validator.validate(
            image
        )
    )

    assert (
        0.0
        <= result.tomato_score
        <= 1.0
    )

    assert result.status in {
        "supported",
        "unsupported",
        "uncertain",
    }

    assert (
        result.unsupported_threshold
        == 0.20
    )

    assert (
        result.supported_threshold
        == 0.80
    )