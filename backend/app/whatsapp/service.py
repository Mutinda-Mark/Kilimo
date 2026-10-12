"""
WhatsApp Cloud API service for KILIMO.

Responsibilities:

- Parse WhatsApp webhook payloads
- Send text messages
- Retrieve WhatsApp media information
- Download WhatsApp media bytes

This service does not perform tomato disease analysis.
Image analysis is handled separately by the CV pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from app.config import settings
from app.whatsapp.webhook import extract_messages


@dataclass
class WhatsAppMedia:
    """
    Downloaded WhatsApp media object.
    """

    media_id: str
    content: bytes
    mime_type: str | None
    file_size: int


class WhatsAppService:
    """
    Interface between KILIMO and Meta's WhatsApp Cloud API.
    """

    def __init__(self) -> None:
        self.api_version = settings.whatsapp_api_version
        self.phone_number_id = settings.whatsapp_phone_number_id
        self.access_token = settings.whatsapp_access_token

        if not self.phone_number_id:
            raise ValueError(
                "WHATSAPP_PHONE_NUMBER_ID is not configured."
            )

        if not self.access_token:
            raise ValueError(
                "WHATSAPP_ACCESS_TOKEN is not configured."
            )

    # =========================================================
    # WEBHOOK PARSING
    # =========================================================

    def parse_webhook(
        self,
        payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Parse incoming WhatsApp webhook messages.
        """

        return extract_messages(payload)

    # =========================================================
    # AUTHENTICATION
    # =========================================================

    def _headers(self) -> dict[str, str]:
        """
        Build authorization headers for Meta Graph API requests.
        """

        return {
            "Authorization": (
                f"Bearer {self.access_token}"
            ),
        }

    # =========================================================
    # SEND TEXT MESSAGE
    # =========================================================

    async def send_text_message(
        self,
        to: str,
        text: str,
    ) -> dict[str, Any]:
        """
        Send one WhatsApp text message.
        """

        to = (to or "").strip()
        text = (text or "").strip()

        if not to:
            raise ValueError(
                "WhatsApp recipient number is required."
            )

        if not text:
            raise ValueError(
                "WhatsApp message text cannot be empty."
            )

        url = (
            f"https://graph.facebook.com/"
            f"{self.api_version}/"
            f"{self.phone_number_id}/messages"
        )

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": text,
            },
        }

        headers = {
            **self._headers(),
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(
            timeout=30.0,
        ) as client:

            response = await client.post(
                url,
                headers=headers,
                json=payload,
            )

        if response.is_error:
            raise RuntimeError(
                "WhatsApp API message send failed. "
                f"Status={response.status_code}, "
                f"body={response.text}"
            )

        return response.json()

    # =========================================================
    # GET MEDIA METADATA
    # =========================================================

    async def get_media_info(
        self,
        media_id: str,
    ) -> dict[str, Any]:
        """
        Ask Meta for the temporary download URL associated
        with a WhatsApp media ID.
        """

        media_id = (media_id or "").strip()

        if not media_id:
            raise ValueError(
                "WhatsApp media ID is required."
            )

        url = (
            f"https://graph.facebook.com/"
            f"{self.api_version}/"
            f"{media_id}"
        )

        params = {
            "phone_number_id": (
                self.phone_number_id
            ),
        }

        async with httpx.AsyncClient(
            timeout=30.0,
        ) as client:

            response = await client.get(
                url,
                headers=self._headers(),
                params=params,
            )

        if response.is_error:
            raise RuntimeError(
                "Unable to retrieve WhatsApp media URL. "
                f"Status={response.status_code}, "
                f"body={response.text}"
            )

        data = response.json()

        media_url = data.get("url")

        if not media_url:
            raise RuntimeError(
                "Meta did not return a media download URL."
            )

        return data

    # =========================================================
    # DOWNLOAD MEDIA
    # =========================================================

    async def download_media(
        self,
        media_id: str,
    ) -> WhatsAppMedia:
        """
        Download WhatsApp media into memory.

        Returns raw bytes rather than writing the image to disk.
        """

        media_info = await self.get_media_info(
            media_id
        )

        media_url = media_info.get("url")

        if not media_url:
            raise RuntimeError(
                "WhatsApp media URL is missing."
            )

        async with httpx.AsyncClient(
            timeout=60.0,
            follow_redirects=True,
        ) as client:

            response = await client.get(
                media_url,
                headers=self._headers(),
            )

        if response.is_error:
            raise RuntimeError(
                "Unable to download WhatsApp media. "
                f"Status={response.status_code}, "
                f"body={response.text[:500]}"
            )

        content = response.content

        if not content:
            raise RuntimeError(
                "Downloaded WhatsApp media is empty."
            )

        mime_type = (
            media_info.get("mime_type")
            or response.headers.get(
                "Content-Type"
            )
        )

        return WhatsAppMedia(
            media_id=media_id,
            content=content,
            mime_type=mime_type,
            file_size=len(content),
        )