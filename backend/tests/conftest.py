"""
Shared pytest fixtures for KILIMO backend tests.
"""

import pytest
import pytest_asyncio

from cv.subject_validator import (
    SubjectValidationResult,
)

from app.main import (
    chat_rate_limiter,
    predict_rate_limiter,
)

@pytest_asyncio.fixture(autouse=True)
async def reset_api_rate_limiters():
    await predict_rate_limiter.clear()
    await chat_rate_limiter.clear()

    yield

    await predict_rate_limiter.clear()
    await chat_rate_limiter.clear()

@pytest.fixture
def supported_subject(monkeypatch):
    """
    Force the application-level subject validator to accept
    synthetic test images.

    Use this fixture only in tests whose purpose is downstream
    behavior such as disease inference, advisory generation,
    session handling, or failure handling.
    """

    from app import main

    result = SubjectValidationResult(
        accepted=True,
        status="supported",
        reason=None,
        message=(
            "Image passed the tomato-subject "
            "validation check."
        ),
        tomato_score=0.99,
        unsupported_threshold=0.20,
        supported_threshold=0.80,
        model_available=True,
    )

    monkeypatch.setattr(
        main.image_analysis_service.subject_validator,
        "validate",
        lambda image: result,
    )

    return result