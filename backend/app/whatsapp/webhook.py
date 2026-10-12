from __future__ import annotations

from typing import Any


def extract_messages(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Extract incoming WhatsApp messages from a Meta webhook payload.

    The function intentionally only extracts information we need.
    It does not process the message or call the CV/LLM pipeline.
    """

    messages: list[dict[str, Any]] = []

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})

            for message in value.get("messages", []):
                message_type = message.get("type")

                base_message = {
                    "message_id": message.get("id"),
                    "from": message.get("from"),
                    "type": message_type,
                }

                if message_type == "text":
                    text_data = message.get("text", {})

                    base_message["text"] = text_data.get("body")

                elif message_type == "image":
                    image_data = message.get("image", {})

                    base_message["media_id"] = image_data.get("id")
                    base_message["mime_type"] = image_data.get("mime_type")
                    base_message["caption"] = image_data.get("caption")

                messages.append(base_message)

    return messages

def verify_webhook(
    mode: str | None,
    token: str | None,
    challenge: str | None,
    expected_token: str,
) -> str | None:
    """
    Verify a WhatsApp webhook subscription request.

    Returns the challenge when verification succeeds.
    Returns None when verification fails.
    """

    if mode != "subscribe":
        return None

    if not token:
        return None

    if token != expected_token:
        return None

    return challenge

def extract_statuses(payload: dict[str, Any]) -> list[dict[str, Any]]:
    statuses = []

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})

            for status in value.get("statuses", []):
                statuses.append({
                    "message_id": status.get("id"),
                    "recipient_id": status.get("recipient_id"),
                    "status": status.get("status"),
                    "timestamp": status.get("timestamp"),
                    "errors": status.get("errors", []),
                })

    return statuses