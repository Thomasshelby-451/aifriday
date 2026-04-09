import os
from dotenv import load_dotenv
load_dotenv()
import io
import uuid
from typing import List, Dict, Any, Tuple

import streamlit as st
import numpy as np
import pandas as pd
from PyPDF2 import PdfReader

import chromadb
from chromadb.api.models.Collection import Collection

try:
	from openai import AzureOpenAI
except Exception:  # pragma: no cover
	AzureOpenAI = None  # type: ignore


# =============================
# Configuration and Constants
# =============================
PERSIST_DIR_DEFAULT = "./chroma_db"
COLLECTION_NAME = "rag_collection"


# =============================
# Azure OpenAI Helpers
# =============================
def get_azure_client() -> AzureOpenAI:
	"""
	Create and return an Azure OpenAI client using environment variables.
	Required env vars:
	- AZURE_OPENAI_API_KEY
	- AZURE_OPENAI_ENDPOINT
	- AZURE_OPENAI_API_VERSION
	"""
	required_vars = [
		"AZURE_OPENAI_API_KEY",
		"AZURE_OPENAI_ENDPOINT",
		"AZURE_OPENAI_API_VERSION",
		"AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME",
		"AZURE_OPENAI_CHAT_DEPLOYMENT_NAME",
	]
	missing = [v for v in required_vars if not os.getenv(v)]
	if missing:
		raise EnvironmentError(
			f"Missing required environment variables: {', '.join(missing)}"
		)

	if AzureOpenAI is None:
		raise RuntimeError(
			"The 'openai' package is not available. Please install it: pip install openai"
		)

	client = AzureOpenAI(
		api_key=os.getenv("AZURE_OPENAI_API_KEY"),
		azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
		api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
	)
	return client


def get_deployment_names() -> Tuple[str, str]:
	"""
	Return (embedding_deployment_name, chat_deployment_name) from env.
	"""
	embedding_name = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME", "").strip()
	chat_name = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", "").strip()
	if not embedding_name or not chat_name:
		raise EnvironmentError(
			"Both AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME and "
			"AZURE_OPENAI_CHAT_DEPLOYMENT_NAME must be set."
		)
	return embedding_name, chat_name


# =============================
# Core RAG Functions
# =============================
def extract_text(uploaded_files: List[io.BytesIO]) -> Dict[str, str]:
	"""
	Extract text from a list of uploaded files (PDF, TXT, CSV).
	Returns a dict mapping file name to extracted text.
	"""
	result: Dict[str, str] = {}
	for uf in uploaded_files:
		name = getattr(uf, "name", "uploaded_file")
		name_lower = name.lower()
		try:
			if name_lower.endswith(".pdf"):
				reader = PdfReader(uf)
				pages_text = []
				for page in reader.pages:
					page_text = page.extract_text() or ""
					pages_text.append(page_text)
				result[name] = "\n".join(pages_text).strip()
			elif name_lower.endswith(".txt"):
				content = uf.read().decode("utf-8", errors="ignore")
				result[name] = content.strip()
			elif name_lower.endswith(".csv"):
				df = pd.read_csv(uf)
				text = df.to_csv(index=False)
				result[name] = text.strip()
			else:
				# Fallback: try utf-8 decode
				content = uf.read().decode("utf-8", errors="ignore")
				result[name] = content.strip()
		finally:
			try:
				uf.seek(0)
			except Exception:
				pass
	return result


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
	"""
	Split text into character-based chunks with overlap.
	"""
	if not text:
		return []

	if overlap >= chunk_size:
		overlap = max(0, chunk_size // 4)

	chunks: List[str] = []
	start = 0
	text_len = len(text)
	while start < text_len:
		end = min(start + chunk_size, text_len)
		chunk = text[start:end]
		chunks.append(chunk)
		if end == text_len:
			break
		start = end - overlap
		if start < 0:
			start = 0
	return chunks


def generate_embeddings(client: AzureOpenAI, model: str, texts: List[str], batch_size: int = 64) -> List[List[float]]:
	"""
	Generate embeddings for a list of texts using Azure OpenAI embeddings.
	Processes inputs in batches for efficiency.
	"""
	all_vectors: List[List[float]] = []
	for i in range(0, len(texts), batch_size):
		batch = texts[i : i + batch_size]
		resp = client.embeddings.create(model=model, input=batch)
		# The SDK returns embeddings in the same order as input
		vectors = [d.embedding for d in resp.data]
		all_vectors.extend(vectors)
	return all_vectors


def get_chromadb_collection(persist_dir: str, collection_name: str = COLLECTION_NAME) -> Collection:
	"""
	Initialize (or reuse) a ChromaDB persistent client and return a collection.
	"""
	client = chromadb.PersistentClient(path=persist_dir)
	collection = client.get_or_create_collection(name=collection_name)
	return collection


def store_in_chromadb(
	collection: Collection,
	file_to_chunks: Dict[str, List[str]],
	embeddings: List[List[float]],
) -> Tuple[int, List[Dict[str, Any]]]:
	"""
	Store chunks and embeddings in ChromaDB. Returns count stored and a flat metadata list.
	Assumes embeddings correspond to all chunks across files in order.
	"""
	ids: List[str] = []
	documents: List[str] = []
	metadatas: List[Dict[str, Any]] = []

	all_chunks: List[Tuple[str, int, str]] = []  # (file_name, chunk_idx, text)
	for file_name, chunks in file_to_chunks.items():
		for idx, ch in enumerate(chunks):
			all_chunks.append((file_name, idx, ch))

	if len(all_chunks) != len(embeddings):
		raise ValueError("Embeddings count does not match number of chunks.")

	for (file_name, idx, ch), emb in zip(all_chunks, embeddings):
		doc_id = str(uuid.uuid4())
		ids.append(doc_id)
		documents.append(ch)
		metadatas.append(
			{
				"file_name": file_name,
				"chunk_index": idx,
				"text_length": len(ch),
			}
		)

	collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
	return len(ids), metadatas


def query_chromadb(
	collection: Collection,
	client: AzureOpenAI,
	embedding_model: str,
	query: str,
	top_k: int = 4,
) -> Dict[str, Any]:
	"""
	Embed the query and retrieve top_k similar chunks from ChromaDB.
	Returns ChromaDB query results.
	"""
	q_vec = generate_embeddings(client, embedding_model, [query])[0]
	results = collection.query(query_embeddings=[q_vec], n_results=top_k)
	return results


def build_prompt(context_chunks: List[str], question: str) -> str:
	context = "\n\n---\n\n".join(context_chunks)
	prompt = (
		"Answer the question based only on the context below.\n\n"
		f"Context:\n{context}\n\n"
		f"Question: {question}\n\n"
		"Answer:"
	)
	return prompt


def generate_answer(
	client: AzureOpenAI,
	chat_deployment: str,
	prompt: str,
	system_prompt: str = "You are a helpful assistant. Answer concisely and accurately.",
) -> str:
	"""
	Generate an answer from the Azure Chat model given a prompt.
	"""
	resp = client.chat.completions.create(
		model=chat_deployment,
		messages=[
			{"role": "system", "content": system_prompt},
			{"role": "user", "content": prompt},
		],
		temperature=0.2,
		max_tokens=600,
	)
	answer = (resp.choices[0].message.content or "").strip()
	return answer


# =============================
# Streamlit UI
# =============================
st.set_page_config(page_title="Simple RAG with Azure OpenAI + ChromaDB", layout="wide")
st.title("RAG App (Azure OpenAI + ChromaDB)")
st.caption("No LangChain. Simple and modular. Upload files, process, then ask questions.")

with st.sidebar:
	st.header("Settings")
	persist_dir = st.text_input("ChromaDB persist directory", value=PERSIST_DIR_DEFAULT)
	chunk_size = st.slider("Chunk size (chars)", min_value=500, max_value=1000, value=800, step=50)
	chunk_overlap = st.slider("Chunk overlap (chars)", min_value=50, max_value=200, value=100, step=10)
	top_k = st.slider("Top K results", min_value=1, max_value=10, value=4, step=1)

# Session state
if "file_texts" not in st.session_state:
	st.session_state.file_texts = {}  # file -> text
if "file_chunks" not in st.session_state:
	st.session_state.file_chunks = {}  # file -> [chunks]
if "chunk_embeddings" not in st.session_state:
	st.session_state.chunk_embeddings = []  # list of vectors
if "collection_ready" not in st.session_state:
	st.session_state.collection_ready = False
if "client_ok" not in st.session_state:
	st.session_state.client_ok = False
if "collection" not in st.session_state:
	st.session_state.collection = None  # type: ignore

uploaded_files = st.file_uploader("Upload documents (PDF, TXT, CSV)", type=["pdf", "txt", "csv"], accept_multiple_files=True)
process_btn = st.button("Process Documents", type="primary", use_container_width=True)

col_left, col_right = st.columns(2)

with col_left:
	st.subheader("Extracted Text Preview")
	if st.session_state.file_texts:
		for fname, text in st.session_state.file_texts.items():
			st.markdown(f"**{fname}**")
			st.code(text[:1000] + ("..." if len(text) > 1000 else ""))
	else:
		st.info("No text extracted yet. Upload files and click 'Process Documents'.")

with col_right:
	st.subheader("Chunked Text Preview")
	if st.session_state.file_chunks:
		total_chunks = sum(len(v) for v in st.session_state.file_chunks.values())
		st.write(f"Total chunks: {total_chunks}")
		# Show up to first 5 chunks
		show_count = 0
		for fname, chunks in st.session_state.file_chunks.items():
			for idx, ch in enumerate(chunks[:5]):
				st.markdown(f"**{fname} - chunk {idx}**")
				st.code(ch[:500] + ("..." if len(ch) > 500 else ""))
				show_count += 1
				if show_count >= 5:
					break
			if show_count >= 5:
				break
	else:
		st.info("No chunks yet. Process documents to see chunk previews.")


# Processing flow
if process_btn:
	if not uploaded_files:
		st.warning("Please upload at least one file before processing.")
	else:
		with st.spinner("Initializing Azure OpenAI and ChromaDB..."):
			try:
				client = get_azure_client()
				emb_model, chat_model = get_deployment_names()
				st.session_state.client_ok = True
			except Exception as e:
				st.session_state.client_ok = False
				st.error(f"Azure OpenAI initialization error: {e}")

			try:
				collection = get_chromadb_collection(persist_dir, COLLECTION_NAME)
				st.session_state.collection = collection
			except Exception as e:
				st.error(f"ChromaDB initialization error: {e}")
				st.stop()

		if st.session_state.client_ok and st.session_state.collection is not None:
			with st.spinner("Extracting text from documents..."):
				try:
					file_texts = extract_text(uploaded_files)
					# Clean and filter out empty
					file_texts = {k: v.strip() for k, v in file_texts.items() if v and v.strip()}
					st.session_state.file_texts = file_texts
					if not file_texts:
						st.warning("No text extracted from uploaded files.")
				except Exception as e:
					st.error(f"Error during text extraction: {e}")
					st.stop()

			if st.session_state.file_texts:
				with st.spinner("Chunking text..."):
					try:
						file_chunks: Dict[str, List[str]] = {}
						for fname, text in st.session_state.file_texts.items():
							file_chunks[fname] = chunk_text(text, chunk_size=chunk_size, overlap=chunk_overlap)
						st.session_state.file_chunks = file_chunks
					except Exception as e:
						st.error(f"Error during chunking: {e}")
						st.stop()

				all_chunks_flat: List[str] = []
				for chunks in st.session_state.file_chunks.values():
					all_chunks_flat.extend(chunks)

				if not all_chunks_flat:
					st.warning("No chunks were generated from the extracted text.")
				else:
					with st.spinner("Generating embeddings and storing in ChromaDB..."):
						try:
							vectors = generate_embeddings(client, emb_model, all_chunks_flat, batch_size=64)
							st.session_state.chunk_embeddings = vectors

							# For UI: show first few embedding values
							if vectors:
								example_vec = vectors[0]
								st.write("Example embedding (first 12 values):")
								st.code(np.array(example_vec[:12]).round(4).tolist())

							count, _ = store_in_chromadb(
								st.session_state.collection,
								st.session_state.file_chunks,
								vectors,
							)
							st.success(f"Stored {count} chunks in ChromaDB.")
							st.session_state.collection_ready = True
						except Exception as e:
							st.error(f"Error during embedding/store: {e}")
							st.stop()

st.markdown("---")
st.subheader("Ask a question")
user_question = st.text_input("Your question", placeholder="Ask about the uploaded documents...")
ask_btn = st.button("Get Answer", type="primary")

if ask_btn:
	if not user_question.strip():
		st.warning("Please enter a question.")
	else:
		if not st.session_state.client_ok:
			try:
				client = get_azure_client()
				emb_model, chat_model = get_deployment_names()
				st.session_state.client_ok = True
			except Exception as e:
				st.error(f"Azure OpenAI initialization error: {e}")
				st.stop()
		else:
			client = get_azure_client()
			emb_model, chat_model = get_deployment_names()

		if not st.session_state.collection:
			try:
				st.session_state.collection = get_chromadb_collection(persist_dir, COLLECTION_NAME)
			except Exception as e:
				st.error(f"ChromaDB initialization error: {e}")
				st.stop()

		with st.spinner("Retrieving relevant chunks..."):
			try:
				results = query_chromadb(
					st.session_state.collection,
					client,
					emb_model,
					user_question,
					top_k=top_k,
				)
			except Exception as e:
				st.error(f"Error during retrieval: {e}")
				st.stop()

		# Display retrieved results
		st.markdown("**Top matches:**")
		retrieved_chunks: List[str] = []
		if results and results.get("documents"):
			docs = results["documents"][0] if results["documents"] else []
			metas = results["metadatas"][0] if results["metadatas"] else []
			dists = results.get("distances", [[]])
			dists = dists[0] if dists else []

			for i, (doc, meta) in enumerate(zip(docs, metas)):
				dist_val = dists[i] if i < len(dists) else None
				retrieved_chunks.append(doc)
				file_name = meta.get("file_name", "unknown")
				chunk_index = meta.get("chunk_index", -1)
				score_str = f"distance={dist_val:.4f}" if isinstance(dist_val, (float, int)) else "distance=N/A"
				st.markdown(f"- {file_name} (chunk {chunk_index}) — {score_str}")
				st.code(doc[:800] + ("..." if len(doc) > 800 else ""))
		else:
			st.info("No results retrieved from the vector database.")

		with st.spinner("Generating answer..."):
			try:
				prompt = build_prompt(retrieved_chunks, user_question)
				answer = generate_answer(client, chat_model, prompt)
				st.markdown("**Answer:**")
				st.write(answer if answer else "No answer generated.")
			except Exception as e:
				st.error(f"Error generating answer: {e}")


# Footer
st.markdown("---")
st.caption(
	"Built with Streamlit, Azure OpenAI, and ChromaDB. "
	"Environment vars required: AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_VERSION, "
	"AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME, AZURE_OPENAI_CHAT_DEPLOYMENT_NAME."
)

