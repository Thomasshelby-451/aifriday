import os
import httpx
import streamlit as st
from langchain_openai import ChatOpenAI

# Load API key from environment variable
api_key = os.getenv("sk-7mnBOjys5IsMNfvbA2FVwg")

# Custom HTTP client (avoid disabling SSL in production!)
client = httpx.Client(verify=False)

# Initialize ChatOpenAI
llm = ChatOpenAI(
    base_url="https://genailab.tcs.in",
    model="azure_ai/genailab-maas-DeepSeek-V3-0324",
    api_key="sk-7mnBOjys5IsMNfvbA2FVwg",
    http_client=client
)

# Streamlit UI
st.set_page_config(page_title="LangChain + Streamlit Demo", layout="centered")
st.title("💬 Chat with LangChain + OpenAI")

# Input box
user_input = st.text_area("Enter your prompt:", height=150)

# Button to trigger response
if st.button("Generate Response"):
    if user_input.strip():
        response = llm.invoke(user_input)
        st.write("### Response:")
        st.write(response.content)
    else:
        st.warning("Please enter a prompt before clicking Generate.")
