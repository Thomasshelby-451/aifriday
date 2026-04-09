import psycopg2
import httpx

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

class OpenAIChatWrapper:
    def __init__(self, base_url, model, api_key, http_client):
        self.base_url = base_url
        self.model = model
        self.api_key = api_key
        self.client = http_client

    def generate(self, prompt, context_docs):
        # Combine retrieved docs into context
        context_text = "\n\n".join([doc for doc in context_docs])
        full_prompt = f"Answer the following query using the context:\n\nContext:\n{context_text}\n\nQuery:\n{prompt}\n\nAnswer:"
        
        response = self.client.post(
            f"{self.base_url}/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": full_prompt}],
                "temperature": 0.2
            },
        )
        return response.json()["choices"][0]["message"]["content"]

# Initialize embedding + chat models
embedding_model = OpenAIEmbeddingsWrapper(
    base_url="https://genailab.tcs.in",
    model="azure/genailab-maas-text-embedding-3-large",
    api_key="sk-7mnBOjys5IsMNfvbA2FVwg",
    http_client=client
)

chat_model = OpenAIChatWrapper(
    base_url="https://genailab.tcs.in",
    #model="azure_ai/genailab-maas-DeepSeek-V3-0324",  # replace with your deployed GPT model
    model="azure/genailab-maas-gpt-35-turbo",
    api_key="sk-7mnBOjys5IsMNfvbA2FVwg",
    http_client=client
)

# Connect to Postgres
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="Test",
    user="postgres",
    password="Test@123"
)
cur = conn.cursor()

# Insert text + embedding
def insert_text(text: str):
    embedding = embedding_model.embed_text(text)
    cur.execute(
        "INSERT INTO documents2 (content, embedding) VALUES (%s, %s)",
        (text, embedding)
    )
    conn.commit()
    print("✅ Inserted into documents2")

# Retrieve top-k docs
def retrieve_docs(query: str, top_k: int = 3):
    query_embedding = embedding_model.embed_text(query)
    cur.execute(
        "SELECT content, 1 - (embedding <=> %s::vector) AS cosine_similarity "
        "FROM documents2 ORDER BY cosine_similarity DESC LIMIT %s;",
        (query_embedding, top_k)
    )
    results = cur.fetchall()
    return [content for content, _ in results]

# RAG pipeline: retrieve + generate
def rag_query(query: str, top_k: int = 3):
    docs = retrieve_docs(query, top_k)
    answer = chat_model.generate(query, docs)
    print("🤖 RAG Answer:")
    print(answer)
    return answer

# Example usage
if __name__ == "__main__":
    # insert_text("Postgres is a powerful relational database.")
    # insert_text("Azure OpenAI provides embeddings for semantic search.")
    # insert_text("Cosine similarity helps find related text.")
    # insert_text("Semantic search interprets user intent using NLP and ML.")
    
    rag_query("Tell me about semantic search")