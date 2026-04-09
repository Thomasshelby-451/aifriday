

import streamlit as st
from pdfminer.high_level import extract_text
import tempfile
import httpx

# Disable SSL verification (not recommended for production)
client = httpx.Client(verify=False)

# --- LLM and Embedding setup (direct calls, no LangChain) ---
class ChatOpenAIWrapper:
    def __init__(self, base_url, model, api_key, http_client):
        self.base_url = base_url
        self.model = model
        self.api_key = api_key
        self.client = http_client

    def invoke(self, prompt):
        response = self.client.post(
            f"{self.base_url}/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        return response.json()["choices"][0]["message"]["content"]

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

# Initialize wrappers
llm = ChatOpenAIWrapper(
    base_url="https://genailab.tcs.in",
    model="azure_ai/genailab-maas-DeepSeek-V3-0324",
    api_key="sk-7mnBOjys5IsMNfvbA2FVwg",
    http_client=client
)

embedding_model = OpenAIEmbeddingsWrapper(
    base_url="https://genailab.tcs.in",
    model="azure/genailab-maas-text-embedding-3-large",
    api_key="sk-7mnBOjys5IsMNfvbA2FVwg",
    http_client=client
)

# --- Simple text splitter ---
def simple_text_splitter(text, chunk_size=1000, overlap=200):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

# --- Streamlit UI ---
st.set_page_config(page_title="PDF Summarizer without LangChain")
st.title("📄 PDF Summarizer (Direct API Calls)")

upload_file = st.file_uploader("Upload a PDF", type="pdf")

if upload_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(upload_file.read())
        temp_file_path = temp_file.name

    # Step 1: Extract text
    raw_text = extract_text(temp_file_path)

    # Step 2: Chunking
    chunks = simple_text_splitter(raw_text)

    st.subheader("Original Document (first 1000 chars)")
    st.text(raw_text[:1000])

    # Step 3: Summarization
    if st.button("Summarize Document"):
        summary_prompt = "Summarize the following document:\n\n" + raw_text[:3000]
        summary = llm.invoke(summary_prompt)
        st.subheader("📌 Summary")
        st.write(summary)

    # Step 4: Embeddings
    if st.button("Generate Embeddings"):
        embedding_vector = embedding_model.embed_text(raw_text[:1000])
        st.subheader("🔢 Embedding Vector (first 20 dimensions)")
        st.write(embedding_vector[:20])