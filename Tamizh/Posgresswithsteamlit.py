import os
import httpx
import streamlit as st
import psycopg2
from langchain_openai import ChatOpenAI

# --- LLM Setup ---
api_key = os.getenv("OPENAI_API_KEY")
client = httpx.Client(verify=False)

llm = ChatOpenAI(
    base_url="https://genailab.tcs.in",
    model="azure_ai/genailab-maas-DeepSeek-V3-0324",
    api_key="sk-7mnBOjys5IsMNfvbA2FVwg",
    http_client=client
)

# --- PostgreSQL Connection ---
try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="Test",   # replace with your database name
        user="postgres",           # replace with your username
        password="Test@123"   # replace with your password
    )
    cursor = conn.cursor()
except Exception as e:
    st.error(f"Database connection failed: {e}")
    conn, cursor = None, None

# --- Streamlit UI ---
st.title("LangChain + Streamlit Chat + PostgreSQL Embeddings Viewer")

user_input = st.text_area("Enter your prompt:")

if st.button("Send"):
    if user_input.strip():
        # Get LLM response
        response = llm.invoke(user_input)
        st.write("### LLM Response:")
        st.write(response.content)

        # Retrieve records from embeddings table
        if cursor:
            try:
                cursor.execute("SELECT text_input, embedding FROM embeddings;")
                rows = cursor.fetchall()

                st.write("### Records from embeddings table:")
                for text_input, embedding in rows:
                    st.write(f"**Text:** {text_input} | **Embedding:** {embedding}")
            except Exception as e:
                st.error(f"Error retrieving data: {e}")
    else:
        st.warning("Please enter a prompt.")
