from __future__ import annotations
import logging


logger = logging.getLogger(__name__)
import time
from typing import Sequence

from google import genai
from google.genai import types

from app.config import settings


class EmbeddingService:
    """
    Generates text embeddings using Google's Gemini embedding API.

    Embeddings are generated at 1536 dimensions to match:

        chunks.embedding VECTOR(1536)

    in PostgreSQL.
    """

    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )

        self.model = "gemini-embedding-001"

    def _embed(
        self,
        contents: str | Sequence[str],
    ) -> list[list[float]]:
        """
        Generate one or more embeddings.

        Includes a small application-level retry for transient
        rate-limit/service errors.
        """

        if isinstance(contents, str):
            texts = [contents]
        else:
            texts = list(contents)

        if not texts:
            raise ValueError("Cannot embed empty input.")

        if any(not text.strip() for text in texts):
            raise ValueError("Cannot embed empty text.")

        max_attempts = 5

        for attempt in range(max_attempts):
            try:
                response = self.client.models.embed_content(
                    model=self.model,
                    contents=texts,
                    config=types.EmbedContentConfig(
                        output_dimensionality=1536,
                    ),
                )

                return [
                    list(embedding.values)
                    for embedding in response.embeddings
                ]

            except Exception as exc:
                error_text = str(exc)

                is_retryable = (
                    "429" in error_text
                    or "RESOURCE_EXHAUSTED" in error_text
                    or "503" in error_text
                    or "UNAVAILABLE" in error_text
                )

                if not is_retryable or attempt == max_attempts - 1:
                    raise

                delay = 2 ** attempt

                logger.warning(
                    f"Embedding request temporarily unavailable. "
                    f"Retrying in {delay}s..."
                )

                time.sleep(delay)

        raise RuntimeError("Embedding request failed.")

    def embed_document(self, text: str) -> list[float]:
        """
        Generate an embedding for one knowledge-base document/chunk.
        """

        return self._embed(text)[0]

    def embed_documents(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple knowledge-base chunks
        in a single API request.
        """

        return self._embed(texts)

    def embed_query(self, text: str) -> list[float]:
        """
        Generate an embedding for a farmer's search/query text.
        """

        return self._embed(text)[0]