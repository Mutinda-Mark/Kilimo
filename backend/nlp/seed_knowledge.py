from __future__ import annotations

import asyncio

from app.db import close_pool, get_pool
from nlp.embeddings import EmbeddingService
from nlp.knowledge import DISEASE_KNOWLEDGE


DOCUMENT_TITLE = "KILIMO Tomato Disease Knowledge Base"
DOCUMENT_SOURCE = "KILIMO structured knowledge base"


def build_chunks() -> list[tuple[str, str]]:
    """
    Convert the structured disease knowledge into RAG chunks.

    Returns:
        List of (disease_name, chunk_text)
    """

    chunks: list[tuple[str, str]] = []

    for disease, knowledge in DISEASE_KNOWLEDGE.items():

        sections = {
            "Description": knowledge["description"],
            "Symptoms": "\n".join(
                f"- {item}"
                for item in knowledge["symptoms"]
            ),
            "Management": "\n".join(
                f"- {item}"
                for item in knowledge["management"]
            ),
            "Prevention": "\n".join(
                f"- {item}"
                for item in knowledge["prevention"]
            ),
        }

        for section_name, content in sections.items():

            chunk_text = (
                f"Disease: {disease}\n"
                f"Section: {section_name}\n\n"
                f"{content}"
            )

            chunks.append((disease, chunk_text))

    return chunks


async def seed_knowledge() -> None:
    embedding_service = EmbeddingService()
    pool = await get_pool()

    try:
        chunks = build_chunks()

        print(f"Prepared {len(chunks)} knowledge chunks.")

        async with pool.acquire() as conn:

            # Remove an existing KILIMO seed so the script is
            # safe to run again during development.
            existing_document_ids = await conn.fetch(
                """
                SELECT id
                FROM documents
                WHERE title = $1
                """,
                DOCUMENT_TITLE,
            )

            if existing_document_ids:
                print("Existing KILIMO knowledge base found.")
                print("Removing it before reseeding...")

                await conn.execute(
                    """
                    DELETE FROM documents
                    WHERE title = $1
                    """,
                    DOCUMENT_TITLE,
                )

            document_id = await conn.fetchval(
                """
                INSERT INTO documents (
                    title,
                    source
                )
                VALUES ($1, $2)
                RETURNING id
                """,
                DOCUMENT_TITLE,
                DOCUMENT_SOURCE,
            )

            print(f"Created document ID: {document_id}")

            texts = [chunk_text for _, chunk_text in chunks]

            print()
            print("Generating embeddings...")
            print(
                "Sending chunks in batches to reduce API requests."
            )

            # Keep the batches small enough to avoid making
            # unnecessarily large embedding requests.
            batch_size = 10

            for start in range(0, len(chunks), batch_size):

                batch = chunks[start:start + batch_size]
                batch_texts = [
                    chunk_text
                    for _, chunk_text in batch
                ]

                batch_number = (
                    start // batch_size
                ) + 1

                total_batches = (
                    (len(chunks) + batch_size - 1)
                    // batch_size
                )

                print(
                    f"Embedding batch "
                    f"{batch_number}/{total_batches}..."
                )

                embeddings = (
                    embedding_service.embed_documents(
                        batch_texts
                    )
                )

                for (disease, chunk_text), embedding in zip(
                    batch,
                    embeddings,
                ):
                    await conn.execute(
                        """
                        INSERT INTO chunks (
                            document_id,
                            content,
                            embedding,
                            disease_tag
                        )
                        VALUES ($1, $2, $3, $4)
                        """,
                        document_id,
                        chunk_text,
                        embedding,
                        disease,
                    )

                print(
                    f"Inserted {len(batch)} chunks."
                )

        print()
        print("Knowledge base seeded successfully.")
        print(f"Total chunks: {len(chunks)}")

    finally:
        await close_pool()


if __name__ == "__main__":
    asyncio.run(seed_knowledge())