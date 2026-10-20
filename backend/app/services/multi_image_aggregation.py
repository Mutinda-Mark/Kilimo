"""
Aggregation of multiple KILIMO tomato disease predictions.

This module contains no WhatsApp, database, or image-decoding logic.
It receives already-computed disease assessments and determines
whether they form a sufficiently consistent multi-image result.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any

from cv.config import DISEASE_CLASSES


@dataclass
class MultiImageAggregationResult:
    """
    Result of combining multiple disease assessments.
    """

    accepted: bool

    status: str

    reason: str | None

    message: str

    image_count: int

    agreement_count: int

    agreement_ratio: float

    consensus_disease: str | None

    assessment: dict[str, Any] | None

    individual_predictions: list[dict[str, Any]]

    def to_dict(
        self,
    ) -> dict[str, Any]:

        return asdict(
            self
        )


def _normalize_scores(
    assessment: dict[str, Any],
) -> dict[str, float]:
    """
    Convert an assessment's all_scores value into a canonical
    disease-name -> score dictionary.

    KILIMO tests historically contain both dictionary and list
    representations, so aggregation supports both.
    """

    raw_scores = assessment.get(
        "all_scores"
    )

    if isinstance(
        raw_scores,
        dict,
    ):

        return {
            disease: float(
                raw_scores.get(
                    disease,
                    0.0,
                )
            )
            for disease in DISEASE_CLASSES
        }

    if isinstance(
        raw_scores,
        (
            list,
            tuple,
        ),
    ):

        if len(
            raw_scores
        ) != len(
            DISEASE_CLASSES
        ):
            raise ValueError(
                "Prediction score vector does not match "
                "the configured disease classes."
            )

        return {
            disease: float(
                raw_scores[index]
            )
            for index, disease
            in enumerate(
                DISEASE_CLASSES
            )
        }

    raise ValueError(
        "Assessment does not contain valid all_scores."
    )


def _choose_severity(
    assessments: list[dict[str, Any]],
    consensus_disease: str,
) -> tuple[str, float]:
    """
    Combine severity from images supporting the consensus.

    Healthy predictions always use None / 0 affected area.

    For disease predictions:
    - affected area is averaged;
    - severity is selected by majority;
    - ties choose the more conservative/higher severity.
    """

    if consensus_disease == "Healthy":
        return (
            "None",
            0.0,
        )

    agreeing = [
        assessment
        for assessment in assessments
        if assessment.get(
            "disease"
        ) == consensus_disease
    ]

    if not agreeing:
        raise ValueError(
            "No assessments support the consensus disease."
        )

    affected_values = [
        float(
            assessment.get(
                "affected_area_percentage",
                0.0,
            )
            or 0.0
        )
        for assessment in agreeing
    ]

    affected_area = (
        sum(
            affected_values
        )
        / len(
            affected_values
        )
    )

    severity_values = [
        str(
            assessment.get(
                "severity_level",
                "Unknown",
            )
        )
        for assessment in agreeing
    ]

    severity_counts = Counter(
        severity_values
    )

    highest_count = max(
        severity_counts.values()
    )

    tied = [
        severity
        for severity, count
        in severity_counts.items()
        if count == highest_count
    ]

    severity_rank = {
        "None": 0,
        "Low": 1,
        "Moderate": 2,
        "Medium": 2,
        "High": 3,
        "Severe": 4,
        "Unknown": -1,
    }

    severity = max(
        tied,
        key=lambda value: (
            severity_rank.get(
                value,
                -1,
            )
        ),
    )

    return (
        severity,
        round(
            affected_area,
            2,
        ),
    )


def aggregate_assessments(
    assessments: list[dict[str, Any]],
) -> MultiImageAggregationResult:
    """
    Aggregate one to three tomato disease assessments.

    Agreement policy:

        1 image:
            that image is sufficient.

        2 images:
            both must predict the same disease.

        3 images:
            at least two must predict the same disease.

    A disagreement produces an explicit abstention result.
    """

    if not assessments:
        raise ValueError(
            "At least one assessment is required."
        )

    if len(
        assessments
    ) > 3:
        raise ValueError(
            "KILIMO supports at most three images "
            "per multi-image assessment."
        )

    individual_predictions: list[
        dict[str, Any]
    ] = []

    diseases: list[str] = []

    normalized_score_sets: list[
        dict[str, float]
    ] = []

    for position, assessment in enumerate(
        assessments,
        start=1,
    ):

        disease = str(
            assessment.get(
                "disease"
            )
            or ""
        ).strip()

        if disease not in DISEASE_CLASSES:
            raise ValueError(
                "Assessment contains an unknown disease class: "
                f"{disease!r}"
            )

        scores = _normalize_scores(
            assessment
        )

        diseases.append(
            disease
        )

        normalized_score_sets.append(
            scores
        )

        individual_predictions.append(
            {
                "image_position":
                    position,

                "disease":
                    disease,

                "confidence":
                    float(
                        assessment.get(
                            "confidence",
                            0.0,
                        )
                        or 0.0
                    ),

                "severity":
                    assessment.get(
                        "severity_level"
                    ),

                "affected_area_percentage":
                    assessment.get(
                        "affected_area_percentage"
                    ),
            }
        )

    disease_counts = Counter(
        diseases
    )

    consensus_disease, agreement_count = (
        disease_counts.most_common(
            1
        )[0]
    )

    image_count = len(
        assessments
    )

    # ---------------------------------------------------------
    # Required agreement
    # ---------------------------------------------------------

    if image_count == 1:
        required_agreement = 1

    elif image_count == 2:
        required_agreement = 2

    else:
        required_agreement = 2

    agreement_ratio = (
        agreement_count
        / image_count
    )

    # ---------------------------------------------------------
    # Abstain when images disagree too strongly
    # ---------------------------------------------------------

    if agreement_count < required_agreement:

        return MultiImageAggregationResult(
            accepted=False,
            status="uncertain",
            reason="prediction_disagreement",
            message=(
                "The photos produced different disease "
                "indications, so KILIMO cannot give a reliable "
                "combined result. Please send clearer photos "
                "of the same affected tomato leaf or plant."
            ),
            image_count=image_count,
            agreement_count=agreement_count,
            agreement_ratio=round(
                agreement_ratio,
                4,
            ),
            consensus_disease=None,
            assessment=None,
            individual_predictions=(
                individual_predictions
            ),
        )

    # ---------------------------------------------------------
    # Mean probability for every disease class
    # ---------------------------------------------------------

    mean_scores = {}

    for disease in DISEASE_CLASSES:

        mean_scores[
            disease
        ] = (
            sum(
                score_set[
                    disease
                ]
                for score_set
                in normalized_score_sets
            )
            / image_count
        )

    mean_scores = {
        disease: round(
            score,
            6,
        )
        for disease, score
        in mean_scores.items()
    }

    consensus_confidence = float(
        mean_scores[
            consensus_disease
        ]
    )

    label_index = (
        DISEASE_CLASSES.index(
            consensus_disease
        )
    )

    severity, affected_area = (
        _choose_severity(
            assessments,
            consensus_disease,
        )
    )

    aggregate_assessment = {
        "disease":
            consensus_disease,

        "confidence":
            consensus_confidence,

        "severity_level":
            severity,

        "affected_area_percentage":
            affected_area,

        "label_index":
            label_index,

        "all_scores":
            mean_scores,

        "image_count":
            image_count,

        "agreement_count":
            agreement_count,

        "agreement_ratio":
            round(
                agreement_ratio,
                4,
            ),
    }

    return MultiImageAggregationResult(
        accepted=True,
        status="consensus",
        reason=None,
        message=(
            "The multi-image assessment produced "
            "a consistent result."
        ),
        image_count=image_count,
        agreement_count=agreement_count,
        agreement_ratio=round(
            agreement_ratio,
            4,
        ),
        consensus_disease=consensus_disease,
        assessment=aggregate_assessment,
        individual_predictions=(
            individual_predictions
        ),
    )