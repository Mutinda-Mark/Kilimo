"""
KILIMO administrative API endpoints.
"""

from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from cv.config import (
    IMAGE_SIZE,
    MODEL_BACKBONE,
    NUM_CLASSES,
)

from app.admin.security import require_admin
from app.services.admin_service import AdminService


router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[
        Depends(require_admin)
    ],
)


admin_service = AdminService()


@router.get("/summary")
async def admin_summary():
    """
    High-level KILIMO dashboard statistics.
    """

    return await admin_service.get_summary()


@router.get("/assessments")
async def admin_assessments(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
):
    """
    Recent tomato disease assessments.
    """

    assessments = (
        await admin_service.get_assessments(
            limit=limit,
            offset=offset,
        )
    )

    return {
        "count": len(
            assessments
        ),
        "limit": limit,
        "offset": offset,
        "assessments": assessments,
    }

@router.get(
    "/assessments/{assessment_id}"
)
async def admin_assessment_detail(
    assessment_id: int,
):
    """
    Return one historical tomato disease assessment.
    """

    assessment = (
        await admin_service.get_assessment(
            assessment_id=assessment_id,
        )
    )

    if assessment is None:
        raise HTTPException(
            status_code=404,
            detail="Assessment not found.",
        )

    return assessment

@router.get("/sessions")
async def admin_sessions(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
):
    """
    Recent farmer sessions.
    """

    sessions = (
        await admin_service.get_sessions(
            limit=limit,
            offset=offset,
        )
    )

    return {
        "count": len(
            sessions
        ),
        "limit": limit,
        "offset": offset,
        "sessions": sessions,
    }


@router.get(
    "/sessions/{phone_number}/history"
)
async def admin_session_history(
    phone_number: str,
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
):
    """
    Conversation history for one farmer.
    """

    history = (
        await admin_service.get_history(
            phone_number=phone_number,
            limit=limit,
        )
    )

    return {
        "phone_number": phone_number,
        "count": len(
            history
        ),
        "history": history,
    }

@router.get("/analytics/severity")
async def admin_severity_statistics():
    """
    Assessment counts grouped by severity.
    """

    data = (
        await admin_service
        .get_severity_statistics()
    )

    return {
        "count": len(data),
        "severities": data,
    }


@router.get("/analytics/sources")
async def admin_source_statistics():
    """
    Assessment counts grouped by input source.
    """

    data = (
        await admin_service
        .get_source_statistics()
    )

    return {
        "count": len(data),
        "sources": data,
    }


@router.get("/analytics/activity")
async def admin_assessment_activity(
    days: int = Query(
        default=14,
        ge=7,
        le=90,
    ),
):
    """
    Daily assessment activity.
    """

    data = (
        await admin_service
        .get_assessment_activity(
            days=days,
        )
    )

    return {
        "days": days,
        "activity": data,
    }

@router.get("/system/database")
async def admin_database_statistics():
    """
    Database connectivity and record counts.
    """

    return await admin_service.get_database_statistics()


@router.get("/system/whatsapp")
async def admin_whatsapp_statistics():
    """
    WhatsApp webhook processing statistics.
    """

    return await admin_service.get_whatsapp_statistics()


@router.get("/system/whatsapp/recent")
async def admin_recent_whatsapp_messages(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
):
    """
    Recently processed WhatsApp messages.
    """

    messages = (
        await admin_service
        .get_recent_whatsapp_messages(
            limit=limit,
        )
    )

    return {
        "count": len(messages),
        "messages": messages,
    }


@router.get("/system/model")
async def admin_model_information():
    """
    Computer-vision model configuration.
    """

    return {
        "backbone": MODEL_BACKBONE,
        "num_classes": NUM_CLASSES,
        "image_size": IMAGE_SIZE,
        "task": (
            "Tomato leaf disease classification"
        ),
        "status": "configured",
    }

@router.get("/diseases")
async def admin_disease_statistics():
    """
    Disease frequency and average confidence/severity data.
    """

    diseases = (
        await admin_service
        .get_disease_statistics()
    )

    return {
        "count": len(
            diseases
        ),
        "diseases": diseases,
    }