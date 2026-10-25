import hashlib
import hmac
import json

import pytest
import pytest_asyncio

from httpx import (
    ASGITransport,
    AsyncClient,
)

from app.main import (
    app,
    settings,
)
from app.db import get_pool
from app.whatsapp.webhook import (
    extract_messages,
)


TEST_PHONE = "254700000005"

TEST_MESSAGE_ID = (
    "msg-test-whatsapp-789"
)

TEST_APP_SECRET = (
    "test-meta-app-secret"
)


# ============================================================
# TEST SIGNATURE HELPERS
# ============================================================


def encode_payload(
    payload: dict,
) -> bytes:
    """
    Serialize a test webhook payload once.

    The exact resulting bytes are both signed and sent to the
    endpoint so the HMAC covers the same bytes received by
    FastAPI.
    """

    return json.dumps(
        payload,
        separators=(
            ",",
            ":",
        ),
        ensure_ascii=False,
    ).encode(
        "utf-8"
    )


def make_signature(
    raw_body: bytes,
    secret: str = TEST_APP_SECRET,
) -> str:
    """
    Generate a Meta-style X-Hub-Signature-256 header.
    """

    digest = hmac.new(
        key=secret.encode(
            "utf-8"
        ),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    return (
        f"sha256={digest}"
    )


async def post_signed_webhook(
    client: AsyncClient,
    payload: dict,
):
    """
    POST one correctly signed webhook payload.
    """

    raw_body = encode_payload(
        payload
    )

    return await client.post(
        "/webhook/whatsapp",
        content=raw_body,
        headers={
            "Content-Type":
                "application/json",

            "X-Hub-Signature-256":
                make_signature(
                    raw_body
                ),
        },
    )


# ============================================================
# DATABASE CLEANUP
# ============================================================


async def cleanup_whatsapp_test_data():
    """
    Remove WhatsApp records created by this test module.
    """

    pool = await get_pool()

    async with pool.acquire() as conn:

        await conn.execute(
            """
            DELETE FROM whatsapp_messages

            WHERE message_id = $1
            """,
            TEST_MESSAGE_ID,
        )

        await conn.execute(
            """
            DELETE FROM conversation_history

            WHERE phone_number = $1
            """,
            TEST_PHONE,
        )

        await conn.execute(
            """
            DELETE FROM sessions

            WHERE phone_number = $1
            """,
            TEST_PHONE,
        )


@pytest_asyncio.fixture(
    autouse=True
)
async def clean_whatsapp_test_data(
    monkeypatch,
):
    """
    Isolate webhook tests from production Meta credentials.

    The endpoint receives a controlled App Secret only for the
    duration of each test.
    """

    monkeypatch.setattr(
        settings,
        "whatsapp_app_secret",
        TEST_APP_SECRET,
    )

    await cleanup_whatsapp_test_data()

    yield

    await cleanup_whatsapp_test_data()


# ============================================================
# EXTRACTION TESTS
# ============================================================


def test_extract_text_message():
    payload = {
        "object":
            "whatsapp_business_account",

        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "id":
                                        "msg-123",

                                    "from":
                                        TEST_PHONE,

                                    "type":
                                        "text",

                                    "text": {
                                        "body":
                                            "What disease is this?"
                                    },
                                }
                            ]
                        }
                    }
                ]
            }
        ],
    }

    messages = extract_messages(
        payload
    )

    assert len(
        messages
    ) == 1

    assert (
        messages[0][
            "message_id"
        ]
        == "msg-123"
    )

    assert (
        messages[0][
            "from"
        ]
        == TEST_PHONE
    )

    assert (
        messages[0][
            "type"
        ]
        == "text"
    )

    assert (
        messages[0][
            "text"
        ]
        == "What disease is this?"
    )


def test_extract_image_message():
    payload = {
        "object":
            "whatsapp_business_account",

        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "id":
                                        "msg-456",

                                    "from":
                                        TEST_PHONE,

                                    "type":
                                        "image",

                                    "image": {
                                        "id":
                                            "media-123",

                                        "mime_type":
                                            "image/jpeg",

                                        "caption":
                                            "Please check this leaf",
                                    },
                                }
                            ]
                        }
                    }
                ]
            }
        ],
    }

    messages = extract_messages(
        payload
    )

    assert len(
        messages
    ) == 1

    assert (
        messages[0][
            "message_id"
        ]
        == "msg-456"
    )

    assert (
        messages[0][
            "from"
        ]
        == TEST_PHONE
    )

    assert (
        messages[0][
            "type"
        ]
        == "image"
    )

    assert (
        messages[0][
            "media_id"
        ]
        == "media-123"
    )

    assert (
        messages[0][
            "mime_type"
        ]
        == "image/jpeg"
    )

    assert (
        messages[0][
            "caption"
        ]
        == "Please check this leaf"
    )


def test_extract_empty_payload():
    payload = {
        "object":
            "whatsapp_business_account",

        "entry": [],
    }

    messages = extract_messages(
        payload
    )

    assert messages == []


# ============================================================
# VALID SIGNED WEBHOOK
# ============================================================


@pytest.mark.asyncio
async def test_whatsapp_webhook_accepts_signed_payload(
    monkeypatch,
):
    """
    A correctly signed Meta payload should:

    - pass webhook authentication;
    - claim the message ID;
    - schedule processing;
    - return HTTP 200.
    """

    async def fake_process_message(
        message,
    ):
        """
        Avoid real Gemini / WhatsApp calls.
        """

        return None

    monkeypatch.setattr(
        (
            "app.main.whatsapp_processor"
            ".process_message"
        ),
        fake_process_message,
    )

    payload = {
        "object":
            "whatsapp_business_account",

        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "id":
                                        TEST_MESSAGE_ID,

                                    "from":
                                        TEST_PHONE,

                                    "type":
                                        "text",

                                    "text": {
                                        "body":
                                            "Hello KILIMO"
                                    },
                                }
                            ]
                        }
                    }
                ]
            }
        ],
    }

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = (
            await post_signed_webhook(
                client,
                payload,
            )
        )

    assert (
        response.status_code
        == 200
    )

    data = response.json()

    assert (
        data[
            "status"
        ]
        == "received"
    )

    assert (
        data[
            "message_count"
        ]
        == 1
    )

    assert (
        data[
            "scheduled_count"
        ]
        == 1
    )

    assert (
        data[
            "duplicate_count"
        ]
        == 0
    )

    assert (
        data[
            "status_count"
        ]
        == 0
    )

    # --------------------------------------------------------
    # Confirm the message was claimed in PostgreSQL.
    # --------------------------------------------------------

    pool = await get_pool()

    async with pool.acquire() as conn:

        row = await conn.fetchrow(
            """
            SELECT
                message_id,
                phone_number,
                message_type,
                status

            FROM whatsapp_messages

            WHERE message_id = $1
            """,
            TEST_MESSAGE_ID,
        )

    assert row is not None

    assert (
        row[
            "message_id"
        ]
        == TEST_MESSAGE_ID
    )

    assert (
        row[
            "phone_number"
        ]
        == TEST_PHONE
    )

    assert (
        row[
            "message_type"
        ]
        == "text"
    )

    # The processor is mocked, so the record remains in the
    # initially claimed processing state.

    assert (
        row[
            "status"
        ]
        == "processing"
    )


# ============================================================
# IDEMPOTENCY WITH SIGNED DELIVERY
# ============================================================


@pytest.mark.asyncio
async def test_whatsapp_webhook_ignores_duplicate_signed_message(
    monkeypatch,
):
    """
    Meta may redeliver an authenticated webhook.

    The same WhatsApp message ID must not be scheduled twice.
    """

    async def fake_process_message(
        message,
    ):
        return None

    monkeypatch.setattr(
        (
            "app.main.whatsapp_processor"
            ".process_message"
        ),
        fake_process_message,
    )

    payload = {
        "object":
            "whatsapp_business_account",

        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "id":
                                        TEST_MESSAGE_ID,

                                    "from":
                                        TEST_PHONE,

                                    "type":
                                        "text",

                                    "text": {
                                        "body":
                                            "Hello KILIMO"
                                    },
                                }
                            ]
                        }
                    }
                ]
            }
        ],
    }

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        first_response = (
            await post_signed_webhook(
                client,
                payload,
            )
        )

        second_response = (
            await post_signed_webhook(
                client,
                payload,
            )
        )

    assert (
        first_response.status_code
        == 200
    )

    assert (
        second_response.status_code
        == 200
    )

    first_data = (
        first_response.json()
    )

    second_data = (
        second_response.json()
    )

    assert (
        first_data[
            "scheduled_count"
        ]
        == 1
    )

    assert (
        first_data[
            "duplicate_count"
        ]
        == 0
    )

    assert (
        second_data[
            "scheduled_count"
        ]
        == 0
    )

    assert (
        second_data[
            "duplicate_count"
        ]
        == 1
    )


# ============================================================
# MISSING SIGNATURE
# ============================================================


@pytest.mark.asyncio
async def test_whatsapp_webhook_rejects_missing_signature():

    payload = {
        "object":
            "whatsapp_business_account",

        "entry": [],
    }

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.post(
            "/webhook/whatsapp",
            json=payload,
        )

    assert (
        response.status_code
        == 401
    )

    assert (
        response.json()[
            "detail"
        ]
        == "Invalid webhook signature."
    )


# ============================================================
# INCORRECT SIGNATURE
# ============================================================


@pytest.mark.asyncio
async def test_whatsapp_webhook_rejects_wrong_signature():

    raw_body = encode_payload(
        {
            "object":
                "whatsapp_business_account",

            "entry": [],
        }
    )

    wrong_signature = make_signature(
        raw_body,
        secret="incorrect-secret",
    )

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.post(
            "/webhook/whatsapp",
            content=raw_body,
            headers={
                "Content-Type":
                    "application/json",

                "X-Hub-Signature-256":
                    wrong_signature,
            },
        )

    assert (
        response.status_code
        == 401
    )


# ============================================================
# TAMPERED BODY
# ============================================================


@pytest.mark.asyncio
async def test_whatsapp_webhook_rejects_tampered_payload():

    original_body = encode_payload(
        {
            "object":
                "whatsapp_business_account",

            "entry": [],
        }
    )

    signature = make_signature(
        original_body
    )

    # Change the body after signing it.
    tampered_body = encode_payload(
        {
            "object":
                "whatsapp_business_account",

            "entry": [
                {
                    "tampered":
                        True
                }
            ],
        }
    )

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.post(
            "/webhook/whatsapp",
            content=tampered_body,
            headers={
                "Content-Type":
                    "application/json",

                "X-Hub-Signature-256":
                    signature,
            },
        )

    assert (
        response.status_code
        == 401
    )


# ============================================================
# SIGNED INVALID JSON
# ============================================================


@pytest.mark.asyncio
async def test_whatsapp_webhook_rejects_signed_invalid_json():

    raw_body = (
        b"not-json"
    )

    signature = make_signature(
        raw_body
    )

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.post(
            "/webhook/whatsapp",
            content=raw_body,
            headers={
                "Content-Type":
                    "application/json",

                "X-Hub-Signature-256":
                    signature,
            },
        )

    assert (
        response.status_code
        == 400
    )

    assert (
        "Invalid JSON payload"
        in response.json()[
            "detail"
        ]
    )

@pytest.mark.asyncio
async def test_public_whatsapp_send_test_endpoint_is_removed():

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.post(
            "/test-whatsapp-send",
            params={
                "phone_number":
                    TEST_PHONE,
            },
        )

    assert (
        response.status_code
        == 404
    )