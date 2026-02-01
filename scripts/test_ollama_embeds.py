from langchain_community.embeddings import OllamaEmbeddings

# Initialize embeddings
embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434"
)

# Generate embedding for a single text
text = "This is a document about machine learning"
vector = embeddings.embed_query(text)
print(f"Generated {len(vector)} dimensional vector")

# Generate embeddings for multiple texts
texts = ["doc 1", "doc 2", "doc 3"]
vectors = embeddings.embed_documents(texts)
print(f"Generated {len(vectors)} embeddings")
