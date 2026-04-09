import httpx
import chromadb

# Disable SSL verification (not recommended for production)
client = httpx.Client(verify=False)

class OpenAIEmbeddingsWrapper:
    def __init__(self, base_url, model, api_key, http_client):
        self.base_url = base_url
        self.model = model
        self.api_key = api_key
        self.client = http_client

    def embed_text(self, text):
        response = self.client.post(
            f"{self.base_url}/v1/embeddings",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "input": text},
        )
        return response.json()["data"][0]["embedding"]

# Initialize embedding model
embedding_model = OpenAIEmbeddingsWrapper(
    base_url="https://genailab.tcs.in",
    model="azure/genailab-maas-text-embedding-3-large",  # deployment name
    api_key="sk-7mnBOjys5IsMNfvbA2FVwg",
    http_client=client
)

# Connect to ChromaDB (local persistent storage)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="documents2")

# Insert text + embedding
def insert_text(text: str):
    embedding = embedding_model.embed_text(text)
    collection.add(
        ids=[f"id_{hash(text)}"],  # unique ID
        documents=[text],
        embeddings=[embedding]
    )
    print("✅ Inserted into ChromaDB")

# Search by cosine similarity
def search_text(query: str, top_k: int = 3):
    query_embedding = embedding_model.embed_text(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    print("🔎 Search Results:")
    for doc, score in zip(results["documents"][0], results["distances"][0]):
        print(f"- {doc} (distance: {score:.4f})")
    return results

# Example usage
if __name__ == "__main__":
    insert_text("Postgres is a powerful relational database.")
    insert_text("Azure OpenAI provides embeddings for semantic search.")
    insert_text("Cosine similarity helps find related text.")
    insert_text("Semantic search interprets user intent and relationships between words.")
    insert_text("Semantic search is an advanced search technology that focuses on understanding the meaning and context behind a user's query, rather than relying solely on exact keyword matches. By leveraging Natural Language Processing (NLP), machine learning, and knowledge graphs, semantic search interprets user intent and relationships between words to deliver more accurate and relevant results.")
    search_text("Tell me about semantic search")