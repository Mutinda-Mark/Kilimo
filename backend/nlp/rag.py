from __future__ import annotations

from typing import Any

from nlp.embeddings import EmbeddingService
from app.db import get_pool


class RAGRetriever:
    """
    Retrieves the most relevant knowledge-base chunks using
    PostgreSQL + pgvector cosine similarity.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        self.embedding_service = (
            embedding_service or EmbeddingService()
        )

    async def retrieve(
        self,
        query: str,
        disease: str | None = None,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Retrieve the most relevant knowledge chunks.

        Args:
            query:
                Farmer's question or search query.

            disease:
                Optional predicted disease. If supplied, retrieval
                can prioritize chunks associated with that disease.

            top_k:
                Maximum number of chunks to return.
        """

        if not query.strip():
            raise ValueError("RAG query cannot be empty.")

        if top_k < 1:
            raise ValueError("top_k must be at least 1.")

        query_embedding = self.embedding_service.embed_query(query)

        pool = await get_pool()

        async with pool.acquire() as conn:
            if disease:
                rows = await conn.fetch(
                    """
                    SELECT
                        c.id,
                        c.content,
                        c.disease_tag,
                        d.title,
                        d.source,
                        1 - (c.embedding <=> $1::vector) AS similarity
                    FROM chunks c
                    JOIN documents d
                        ON d.id = c.document_id
                    WHERE
                        c.disease_tag = $2
                    ORDER BY
                        c.embedding <=> $1::vector
                    LIMIT $3
                    """,
                    query_embedding,
                    disease,
                    top_k,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT
                        c.id,
                        c.content,
                        c.disease_tag,
                        d.title,
                        d.source,
                        1 - (c.embedding <=> $1::vector) AS similarity
                    FROM chunks c
                    JOIN documents d
                        ON d.id = c.document_id
                    ORDER BY
                        c.embedding <=> $1::vector
                    LIMIT $2
                    """,
                    query_embedding,
                    top_k,
                )

        return [
            {
                "id": row["id"],
                "content": row["content"],
                "disease_tag": row["disease_tag"],
                "title": row["title"],
                "source": row["source"],
                "similarity": float(row["similarity"]),
            }
            for row in rows
        ]