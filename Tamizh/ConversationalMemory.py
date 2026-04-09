import streamlit as st
import httpx
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage

# -------------------------------
# LLM Setup
# -------------------------------
client = httpx.Client(verify=False)

llm = ChatOpenAI(
    base_url="https://genailab.tcs.in",
    model="azure_ai/genailab-maas-DeepSeek-V3-0324",
    api_key="sk-7mnBOjys5IsMNfvbA2FVwg",
    http_client=client,
    temperature=0
)

# -------------------------------
# Prompt Template
# -------------------------------
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("placeholder", "{history}"),
    ("user", "{input}")
])

# -------------------------------
# Streamlit UI
# -------------------------------
st.title("💬 Conversational Memory Chatbot")

# Initialize session state for history
if "history" not in st.session_state:
    st.session_state["history"] = []

# Chat input box
user_input = st.chat_input("Type your message...")

if user_input:
    # Build chain
    chain = prompt | llm
    response = chain.invoke({"history": st.session_state["history"], "input": user_input})

    # Update history
    st.session_state["history"].append(HumanMessage(content=user_input))
    st.session_state["history"].append(AIMessage(content=response.content))

# Display conversation
for msg in st.session_state["history"]:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.write(msg.content)
    elif isinstance(msg, AIMessage):
        with st.chat_message("assistant"):
            st.write(msg.content)