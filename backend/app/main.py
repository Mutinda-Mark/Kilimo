from contextlib import asynccontextmanager
from fastapi import HTTPException, Request, status, FastAPI, File, Form, UploadFile, BackgroundTasks
from pydantic import BaseModel
from PIL import Image, UnidentifiedImageError
import json
from io import BytesIO

from app.config import settings
from app.db import close_pool, get_pool
from app.admin.router import router as admin_router
from app.services.session_service import SessionService
from app.services.chat_service import ChatService
from app.services.image_analysis_service import ImageAnalysisService
from app.services.whatsapp_event_service import WhatsAppEventService
from app.services.assessment_service import AssessmentService
from app.services.whatsapp_processor import WhatsAppProcessor
from app.whatsapp.webhook import (
    extract_messages,
    extract_statuses,
    verify_webhook,
    verify_webhook_signature,
)
from app.whatsapp.service import WhatsAppService
from app.services.whatsapp_batch_service import WhatsAppBatchService
from app.security.rate_limit import (
    InMemoryRateLimiter,
    enforce_rate_limit,
)
from cv.assessor import TomatoAssessor
from cv.config import MAX_IMAGE_FILE_SIZE_BYTES
from cv.subject_validator import TomatoSubjectValidator
from nlp.advisory import AdvisoryEngine
from nlp.responder import AdvisoryResponder


assessor = TomatoAssessor()
subject_validator = TomatoSubjectValidator()
advisory_engine = AdvisoryEngine()
advisory_responder = AdvisoryResponder()
session_service = SessionService()
assessment_service = AssessmentService()
chat_service = ChatService(
    session_service=session_service,
    advisory_responder=advisory_responder,
)
whatsapp_service = WhatsAppService()
image_analysis_service = ImageAnalysisService(
    assessor=assessor,
    subject_validator=subject_validator,
    advisory_engine=advisory_engine,
    advisory_responder=advisory_responder,
    session_service=session_service,
    assessment_service=assessment_service,
)
whatsapp_event_service = WhatsAppEventService()
whatsapp_batch_service = WhatsAppBatchService()
predict_rate_limiter = InMemoryRateLimiter(
    limit=(
        settings.predict_rate_limit_requests
    ),
    window_seconds=(
        settings.predict_rate_limit_window_seconds
    ),
)

chat_rate_limiter = InMemoryRateLimiter(
    limit=(
        settings.chat_rate_limit_requests
    ),
    window_seconds=(
        settings.chat_rate_limit_window_seconds
    ),
)
whatsapp_processor = WhatsAppProcessor(
    whatsapp_service=whatsapp_service,
    chat_service=chat_service,
    image_analysis_service=image_analysis_service,
    event_service=whatsapp_event_service,
    batch_service=whatsapp_batch_service,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await get_pool()
    except Exception as exc:
        print(f"[startup] Could not connect to database: {exc}")

    yield

    await close_pool()

app = FastAPI(
    title="Tomato Disease Advisory Backend",
    version="0.5.0",
    lifespan=lifespan,
)
app.include_router(
    admin_router
)

@app.get("/webhook/whatsapp")
async def verify_whatsapp_webhook(
    request: Request,
):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    result = verify_webhook(
        mode=mode,
        token=token,
        challenge=challenge,
        expected_token=settings.whatsapp_verify_token,
    )

    if result is None:
        raise HTTPException(
            status_code=403,
            detail="Webhook verification failed.",
        )

    return int(result) if result.isdigit() else result


@app.post("/webhook/whatsapp")
async def receive_whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Receive Meta WhatsApp webhook events.

    The endpoint intentionally performs only lightweight work:

    1. Parse payload
    2. Log delivery statuses
    3. Deduplicate incoming farmer messages
    4. Schedule heavy processing
    5. Return HTTP 200 quickly

    CV, Gemini and media downloading are handled after the
    response through WhatsAppProcessor.
    """

    # =========================================================
    # 1. Read raw request body
    # =========================================================

    raw_body = await request.body()

    # =========================================================
    # 2. Verify Meta webhook signature
    # =========================================================

    signature_header = request.headers.get(
        "X-Hub-Signature-256"
    )

    signature_valid = (
        verify_webhook_signature(
            raw_body=raw_body,
            signature_header=signature_header,
            app_secret=settings.whatsapp_app_secret,
        )
    )

    if not signature_valid:

        print(
            "[WhatsApp] Rejected webhook with invalid "
            "or missing signature."
        )

        raise HTTPException(
            status_code=401,
            detail="Invalid webhook signature.",
        )

    # =========================================================
    # 3. Parse authenticated JSON payload
    # =========================================================

    try:

        payload = json.loads(
            raw_body
        )

    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
    ) as exc:

        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload.",
        ) from exc

    if not isinstance(
        payload,
        dict,
    ):

        raise HTTPException(
            status_code=400,
            detail="Webhook payload must be a JSON object.",
        )

    # =========================================================
    # 4. Extract events
    # =========================================================

    messages = extract_messages(
        payload
    )

    statuses = extract_statuses(
        payload
    )

    # =========================================================
    # 5. Log outbound delivery statuses
    # =========================================================

    if statuses:

        print(
            "\n========== WHATSAPP STATUSES =========="
        )

        for status in statuses:

            print(
                f"Message ID: "
                f"{status.get('message_id')}"
            )

            print(
                f"Recipient: "
                f"{status.get('recipient_id')}"
            )

            print(
                f"Status: "
                f"{status.get('status')}"
            )

            errors = status.get(
                "errors",
                [],
            )

            if errors:

                print(
                    "ERRORS:"
                )

                print(
                    errors
                )

        print(
            "=======================================\n"
        )

    # =========================================================
    # 6 . Claim and schedule incoming farmer messages
    # =========================================================

    scheduled_count = 0
    duplicate_count = 0

    for message in messages:

        message_id = (
            message.get("message_id")
            or ""
        ).strip()

        sender = (
            message.get("from")
            or ""
        ).strip()

        message_type = (
            message.get("type")
            or ""
        ).strip()

        if not message_id:

            print(
                "[WhatsApp] Ignoring message "
                "without message_id."
            )

            continue

        # -----------------------------------------------------
        # Database-backed idempotency check
        # -----------------------------------------------------

        claimed = (
            await whatsapp_event_service.claim_message(
                message_id=message_id,
                phone_number=sender,
                message_type=message_type,
            )
        )

        if not claimed:

            duplicate_count += 1

            print(
                "[WhatsApp] Duplicate message ignored: "
                f"{message_id}"
            )

            continue

        # -----------------------------------------------------
        # Schedule expensive work AFTER HTTP acknowledgement
        # -----------------------------------------------------

        background_tasks.add_task(
            whatsapp_processor.process_message,
            message,
        )

        scheduled_count += 1

        print(
            "[WhatsApp] Scheduled message: "
            f"{message_id}"
        )

    # =========================================================
    # 7. Return quickly to Meta
    # =========================================================

    return {
        "status": "received",
        "message_count": len(messages),
        "scheduled_count": scheduled_count,
        "duplicate_count": duplicate_count,
        "status_count": len(statuses),
    }

@app.get("/")
async def root():
    return {
        "message": "Tomato Disease Advisory Backend",
        "version": "0.5.0",
    }


@app.get("/health")
async def health_check():
    db_ok = False

    try:
        pool = await get_pool()

        async with pool.acquire() as conn:
            db_ok = (await conn.fetchval("SELECT 1")) == 1

    except Exception:
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "unreachable",
        "environment": settings.environment,
    }


@app.post("/predict")
async def predict(
    request: Request,
    file: UploadFile = File(...),
    question: str | None = Form(default=None),
    phone_number: str | None = Form(default=None),
):
    await enforce_rate_limit(
        request=request,
        limiter=predict_rate_limiter,
        scope="predict",
    )
    """
    Upload a tomato leaf image and generate a KILIMO advisory.

    If phone_number is supplied, the assessment is stored in the
    farmer's session and conversation history.
    """

    # =========================================================
    # 1. Validate uploaded file
    # =========================================================

    if (
        not file.content_type
        or not file.content_type.startswith(
            "image/"
        )
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Uploaded file must be an image."
            ),
        )

    # =========================================================
    # 2. Read and validate image
    # =========================================================

    try:
        image_bytes = await file.read(
            MAX_IMAGE_FILE_SIZE_BYTES + 1
        )

        if not image_bytes:
            raise HTTPException(
                status_code=400,
                detail="Uploaded image is empty.",
            )

        if (
            len(image_bytes)
            > MAX_IMAGE_FILE_SIZE_BYTES
        ):
            raise HTTPException(
                status_code=413,
                detail=(
                    "Uploaded image exceeds the "
                    "maximum allowed size of 8 MB."
                ),
            )

        image = Image.open(
            BytesIO(image_bytes)
        ).convert(
            "RGB"
        )

    except HTTPException:
        raise

    except UnidentifiedImageError as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                "The uploaded file is not "
                "a valid image."
            ),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                "Could not process uploaded "
                f"image: {exc}"
            ),
        ) from exc

    # =========================================================
    # 3. Run shared KILIMO image pipeline
    # =========================================================

    try:
        result = (
            await image_analysis_service.process_image(
                image=image,
                phone_number=phone_number,
                question=question,
                image_history_content=(
                    file.filename
                    or "Uploaded tomato leaf image"
                ),
                source="api",
                file_size_bytes=len(
                    image_bytes
                ),
                mime_type=file.content_type,
            )
        )

        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Disease detection model "
                "is not available."
            ),
        ) from exc

    except Exception as exc:

        print(
            "IMAGE ANALYSIS ERROR:"
        )

        print(
            repr(exc)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not complete tomato "
                "image assessment."
            ),
        ) from exc
# =============================================================
# Farmer conversation
# =============================================================

class ChatRequest(BaseModel):
    phone_number: str
    question: str


@app.post("/chat")
async def chat(request: ChatRequest, http_request: Request):
    phone_number = (
        request.phone_number or ""
    ).strip()

    question = (
        request.question or ""
    ).strip()

    await enforce_rate_limit(
        request=http_request,
        limiter=chat_rate_limiter,
        scope="chat",
    )

    if not phone_number:
        raise HTTPException(
            status_code=400,
            detail="Phone number is required.",
        )

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    try:
        result = await chat_service.process_message(
            phone_number=phone_number,
            question=question,
        )

        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        print("CHAT ERROR:")
        print(repr(exc))

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to process chat message."
            ),
        ) from exc
