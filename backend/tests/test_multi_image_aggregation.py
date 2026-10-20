import pytest

from app.services.multi_image_aggregation import (
    aggregate_assessments,
)
from cv.config import DISEASE_CLASSES


def make_assessment(
    disease: str,
    confidence: float,
    severity: str = "Moderate",
    affected_area: float = 20.0,
):
    scores = {
        class_name: 0.0
        for class_name in DISEASE_CLASSES
    }

    scores[
        disease
    ] = confidence

    return {
        "disease":
            disease,

        "confidence":
            confidence,

        "severity_level":
            severity,

        "affected_area_percentage":
            affected_area,

        "label_index":
            DISEASE_CLASSES.index(
                disease
            ),

        "all_scores":
            scores,
    }


def test_single_image_can_produce_consensus():

    result = aggregate_assessments(
        [
            make_assessment(
                "Early Blight",
                0.95,
            )
        ]
    )

    assert result.accepted is True
    assert result.status == "consensus"

    assert (
        result.consensus_disease
        == "Early Blight"
    )

    assert result.image_count == 1
    assert result.agreement_count == 1
    assert result.agreement_ratio == 1.0


def test_two_matching_images_produce_consensus():

    result = aggregate_assessments(
        [
            make_assessment(
                "Early Blight",
                0.95,
                affected_area=20.0,
            ),
            make_assessment(
                "Early Blight",
                0.85,
                affected_area=30.0,
            ),
        ]
    )

    assert result.accepted is True

    assert (
        result.consensus_disease
        == "Early Blight"
    )

    assert result.agreement_count == 2
    assert result.agreement_ratio == 1.0

    assert (
        result.assessment[
            "affected_area_percentage"
        ]
        == 25.0
    )


def test_two_conflicting_images_abstain():

    result = aggregate_assessments(
        [
            make_assessment(
                "Early Blight",
                0.95,
            ),
            make_assessment(
                "Late Blight",
                0.92,
            ),
        ]
    )

    assert result.accepted is False

    assert result.status == "uncertain"

    assert (
        result.reason
        == "prediction_disagreement"
    )

    assert result.assessment is None
    assert result.consensus_disease is None


def test_two_of_three_matching_images_produce_consensus():

    result = aggregate_assessments(
        [
            make_assessment(
                "Early Blight",
                0.93,
            ),
            make_assessment(
                "Early Blight",
                0.90,
            ),
            make_assessment(
                "Septoria Leaf Spot",
                0.80,
            ),
        ]
    )

    assert result.accepted is True

    assert (
        result.consensus_disease
        == "Early Blight"
    )

    assert result.agreement_count == 2

    assert result.agreement_ratio == pytest.approx(
        2 / 3,
        abs=0.0001,
    )


def test_three_different_predictions_abstain():

    result = aggregate_assessments(
        [
            make_assessment(
                "Early Blight",
                0.90,
            ),
            make_assessment(
                "Late Blight",
                0.90,
            ),
            make_assessment(
                "Septoria Leaf Spot",
                0.90,
            ),
        ]
    )

    assert result.accepted is False

    assert (
        result.reason
        == "prediction_disagreement"
    )


def test_consensus_probability_is_mean_score():

    result = aggregate_assessments(
        [
            make_assessment(
                "Early Blight",
                0.90,
            ),
            make_assessment(
                "Early Blight",
                0.80,
            ),
        ]
    )

    assert result.accepted is True

    assert (
        result.assessment[
            "confidence"
        ]
        == pytest.approx(
            0.85
        )
    )

    assert (
        result.assessment[
            "all_scores"
        ][
            "Early Blight"
        ]
        == pytest.approx(
            0.85
        )
    )


def test_more_than_three_images_is_rejected():

    assessments = [
        make_assessment(
            "Early Blight",
            0.9,
        )
        for _ in range(
            4
        )
    ]

    with pytest.raises(
        ValueError,
    ):
        aggregate_assessments(
            assessments
        )