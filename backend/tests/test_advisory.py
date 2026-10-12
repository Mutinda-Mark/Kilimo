"""
Tests for the advisory engine.
"""

from nlp.advisory import AdvisoryEngine


def make_assessment(
    disease="Early Blight",
    confidence=0.95,
    severity="Moderate",
):
    return {
        "disease": disease,
        "confidence": confidence,
        "severity_level": severity,
        "affected_area_percentage": 25.0,
    }


def test_advisory_returns_disease_information():

    engine = AdvisoryEngine()

    result = engine.generate(
        make_assessment()
    )

    assert result["disease"] == "Early Blight"

    assert "description" in result
    assert "symptoms" in result
    assert "recommended_actions" in result
    assert "prevention" in result


def test_high_confidence_prediction():

    engine = AdvisoryEngine()

    result = engine.generate(
        make_assessment(
            confidence=0.95
        )
    )

    assert (
        result["confidence_message"]
        == "The model is highly confident in this prediction."
    )


def test_low_confidence_prediction():

    engine = AdvisoryEngine()

    result = engine.generate(
        make_assessment(
            confidence=0.50
        )
    )

    assert "lower confidence" in result["confidence_message"]


def test_severe_condition_has_high_urgency():

    engine = AdvisoryEngine()

    result = engine.generate(
        make_assessment(
            severity="Severe"
        )
    )

    assert result["urgency"] == "High"


def test_healthy_result_is_monitoring():

    engine = AdvisoryEngine()

    result = engine.generate(
        make_assessment(
            disease="Healthy",
            confidence=0.95,
            severity="Low",
        )
    )

    assert result["urgency"] == "Monitor"


def test_unknown_disease_raises_error():

    engine = AdvisoryEngine()

    assessment = make_assessment(
        disease="Unknown Disease"
    )

    try:
        engine.generate(assessment)
        assert False, "Expected ValueError"
    except ValueError:
        pass