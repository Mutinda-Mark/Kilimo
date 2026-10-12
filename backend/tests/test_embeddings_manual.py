from nlp.embeddings import EmbeddingService


service = EmbeddingService()

query = "What should I do if my tomato plants have late blight?"

embedding = service.embed_query(query)

print("Query embedding generated successfully.")
print("Dimensions:", len(embedding))
print("First 5 values:", embedding[:5])