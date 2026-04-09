#LLM with stream lit with chat bot

import streamlit as st
from langchain_openai import ChatOpenAI
import httpx

# HTTP client setup
client = httpx.Client(verify=False)

# LLM setup
llm = ChatOpenAI(
    base_url="https://genailab.tcs.in",
    model="azure_ai/genailab-maas-DeepSeek-V3-0324",
    api_key="sk-7mnBOjys5IsMNfvbA2FVwg",
    http_client=client
)

# Streamlit UI
st.set_page_config(page_title="Chatbot")
st.title("💬 AI Chatbot")

# Chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Display past messages
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
if prompt := st.chat_input("Type your message..."):
    # Show user message
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get LLM response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = llm.invoke(prompt)
            st.markdown(response.content)

    # Save assistant response
    st.session_state["messages"].append({"role": "assistant", "content": response.content})
