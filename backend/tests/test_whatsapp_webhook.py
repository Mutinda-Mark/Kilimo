import pytest
import pytest_asyncio

from httpx import ASGITransport, AsyncClient

from app.main import app
from app.db import get_pool
from app.whatsapp.webhook import extract_messages


TEST_PHONE = "254700000005"
TEST_MESSAGE_ID = "msg-test-whatsapp-789"


async def cleanup_whatsapp_test_data():
    """Remove WhatsApp records created by this test module."""

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
async def clean_whatsapp_test_data():
    await cleanup_whatsapp_test_data()

    yield

    await cleanup_whatsapp_test_data()


def test_extract_text_message():
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "id": "msg-123",
                                    "from": TEST_PHONE,
                                    "type": "text",
                                    "text": {
                                        "body": "What disease is this?"
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

    assert len(messages) == 1

    assert (
        messages[0]["message_id"]
        == "msg-123"
    )

    assert (
        messages[0]["from"]
        == TEST_PHONE
    )

    assert (
        messages[0]["type"]
        == "text"
    )

    assert (
        messages[0]["text"]
        == "What disease is this?"
    )


def test_extract_image_message():
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "id": "msg-456",
                                    "from": TEST_PHONE,
                                    "type": "image",
                                    "image": {
                                        "id": "media-123",
                                        "mime_type": "image/jpeg",
                                        "caption": "Please check this leaf",
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

    assert len(messages) == 1

    assert (
        messages[0]["message_id"]
        == "msg-456"
    )

    assert (
        messages[0]["from"]
        == TEST_PHONE
    )

    assert (
        messages[0]["type"]
        == "image"
    )

    assert (
        messages[0]["media_id"]
        == "media-123"
    )

    assert (
        messages[0]["mime_type"]
        == "image/jpeg"
    )

    assert (
        messages[0]["caption"]
        == "Please check this leaf"
    )


def test_extract_empty_payload():
    payload = {
        "object": "whatsapp_business_account",
        "entry": [],
    }

    messages = extract_messages(
        payload
    )

    assert messages == []


@pytest.mark.asyncio
async def test_whatsapp_webhook_accepts_payload(
    monkeypatch,
):
    """
    Current webhook behavior:

    - accept incoming Meta payload
    - claim message ID
    - schedule processing
    - return 200 quickly

    The response no longer echoes raw messages.
    """

    async def fake_process_message(
        message,
    ):
        """
        Avoid real Gemini / WhatsApp calls in this test.
        """

        return None

    monkeypatch.setattr(
        "app.main.whatsapp_processor.process_message",
        fake_process_message,
    )

    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "id": TEST_MESSAGE_ID,
                                    "from": TEST_PHONE,
                                    "type": "text",
                                    "text": {
                                        "body": "Hello KILIMO"
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

        response = await client.post(
            "/webhook/whatsapp",
            json=payload,
        )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["status"]
        == "received"
    )

    assert (
        data["message_count"]
        == 1
    )

    assert (
        data["scheduled_count"]
        == 1
    )

    assert (
        data["duplicate_count"]
        == 0
    )

    assert (
        data["status_count"]
        == 0
    )

    # Confirm message was claimed in the database.

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
        row["message_id"]
        == TEST_MESSAGE_ID
    )

    assert (
        row["phone_number"]
        == TEST_PHONE
    )

    assert (
        row["message_type"]
        == "text"
    )

    # Because the processing function is mocked, the record
    # remains in its initially claimed state.

    assert (
        row["status"]
        == "processing"
    )


@pytest.mark.asyncio
async def test_whatsapp_webhook_ignores_duplicate_message(
    monkeypatch,
):
    """
    The same Meta message ID must not be scheduled twice.
    """

    async def fake_process_message(
        message,
    ):
        return None

    monkeypatch.setattr(
        "app.main.whatsapp_processor.process_message",
        fake_process_message,
    )

    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "id": TEST_MESSAGE_ID,
                                    "from": TEST_PHONE,
                                    "type": "text",
                                    "text": {
                                        "body": "Hello KILIMO"
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

        first_response = await client.post(
            "/webhook/whatsapp",
            json=payload,
        )

        second_response = await client.post(
            "/webhook/whatsapp",
            json=payload,
        )

    assert (
        first_response.status_code
        == 200
    )

    assert (
        second_response.status_code
        == 200
    )

    first_data = first_response.json()
    second_data = second_response.json()

    assert (
        first_data["scheduled_count"]
        == 1
    )

    assert (
        first_data["duplicate_count"]
        == 0
    )

    assert (
        second_data["scheduled_count"]
        == 0
    )

    assert (
        second_data["duplicate_count"]
        == 1
    )


@pytest.mark.asyncio
async def test_whatsapp_webhook_rejects_invalid_json():
    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.post(
            "/webhook/whatsapp",
            content=b"not-json",
            headers={
                "Content-Type": "application/json",
            },
        )

    assert response.status_code == 400

    assert (
        "Invalid JSON payload"
        in response.json()["detail"]
    )