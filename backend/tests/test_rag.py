import pytest

from nlp.rag import RAGRetriever


@pytest.mark.asyncio
async def test_rag_retrieves_relevant_disease_chunks():
    retriever = RAGRetriever()

    results = await retriever.retrieve(
        query="What can I do about dark spots spreading on tomato leaves?",
        disease="Early Blight",
        top_k=5,
    )

    assert len(results) > 0

    for result in results:
        assert "id" in result
        assert "content" in result
        assert "disease_tag" in result
        assert "title" in result
        assert "source" in result
        assert "similarity" in result

        assert result["disease_tag"] == "Early Blight"
        assert isinstance(result["content"], str)
        assert result["content"].strip()
        assert 0.0 <= result["similarity"] <= 1.0


@pytest.mark.asyncio
async def test_rag_returns_multiple_relevant_chunks():
    retriever = RAGRetriever()

    results = await retriever.retrieve(
        query="Early blight symptoms management and prevention",
        disease="Early Blight",
        top_k=5,
    )

    assert len(results) >= 2

    similarities = [
        result["similarity"]
        for result in results
    ]

    assert similarities == sorted(
        similarities,
        reverse=True,
    )


@pytest.mark.asyncio
async def test_rag_can_retrieve_without_disease_filter():
    retriever = RAGRetriever()

    results = await retriever.retrieve(
        query="tomato disease prevention",
        top_k=5,
    )

    assert len(results) > 0

    for result in results:
        assert result["content"].strip()
        assert isinstance(
            result["similarity"],
            float,
        )


@pytest.mark.asyncio
async def test_rag_rejects_empty_query():
    retriever = RAGRetriever()

    with pytest.raises(ValueError, match="RAG query cannot be empty"):
        await retriever.retrieve(
            query="",
            disease="Early Blight",
        )


@pytest.mark.asyncio
async def test_rag_rejects_invalid_top_k():
    retriever = RAGRetriever()

    with pytest.raises(
        ValueError,
        match="top_k must be at least 1",
    ):
        await retriever.retrieve(
            query="tomato disease",
            disease="Early Blight",
            top_k=0,
        )