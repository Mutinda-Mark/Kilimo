import asyncio

from nlp.rag import RAGRetriever


async def main() -> None:
    retriever = RAGRetriever()

    results = await retriever.retrieve(
        query="What can I do about dark spots spreading on tomato leaves?",
        disease="Early Blight",
        top_k=5,
    )

    print()
    print("===== RAG RESULTS =====")

    for result in results:
        print()
        print("Disease:", result["disease_tag"])
        print("Section:", result["title"])
        print("Similarity:", result["similarity"])
        print("Content:")
        print(result["content"])


if __name__ == "__main__":
    asyncio.run(main())