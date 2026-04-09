import re
import json
import httpx
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

# -------------------------------
# Guardrail Functions
# -------------------------------
def mask_sensitive(text: str) -> str:
    text = re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[REDACTED_IP]', text)
    text = re.sub(r'\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', '[REDACTED_HOST]', text)
    return text

def input_guardrail(state):
    user_input = state["translated_input"]
    sanitized = mask_sensitive(user_input)
    return {"sanitized_input": sanitized}

def output_guardrail(state):
    raw_output = state["raw_output"]
    try:
        parsed = json.loads(raw_output)
        safe_output = json.dumps(parsed, indent=2)
    except Exception:
        safe_output = json.dumps({"response": raw_output})
    safe_output = mask_sensitive(safe_output)
    return {"final_output": safe_output}

# -------------------------------
# Custom LLM Setup
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
# Translation Node
# -------------------------------
translation_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a language detector and translator. "
     "1. Detect the language of the user input. "
     "2. If it's not English, translate it to English. "
     "3. Respond ONLY in valid JSON with keys: "
     "\"detected_language\" and \"translated_text\". "
     "Do not include explanations. "
     "Example output: {{\"detected_language\": \"Spanish\", \"translated_text\": \"List the servers with IP ...\"}}"),
    ("user", "{input}")
])

def translate_input(state):
    chain = translation_prompt | llm
    response = chain.invoke({"input": state["input"]})

    detected_language = "unknown"
    translated_text = state["input"]

    try:
        parsed = json.loads(response.content.strip())
        detected_language = parsed.get("detected_language", "unknown")
        translated_text = parsed.get("translated_text", state["input"])
    except Exception:
        # fallback: assume English if parsing fails
        detected_language = "English"
        translated_text = state["input"]

    print(f"Detected language: {detected_language}")
    return {"translated_input": translated_text, "detected_language": detected_language}

# -------------------------------
# Main LLM Call Node
# -------------------------------
main_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. Always respond in JSON format."),
    ("user", "{sanitized_input}")
])

def call_llm(state):
    chain = main_prompt | llm
    response = chain.invoke({"sanitized_input": state["sanitized_input"]})
    return {"raw_output": response.content}

# -------------------------------
# Build LangGraph Pipeline
# -------------------------------
workflow = StateGraph(dict)

workflow.add_node("translate_input", translate_input)
workflow.add_node("input_guardrail", input_guardrail)
workflow.add_node("llm_call", call_llm)
workflow.add_node("output_guardrail", output_guardrail)

workflow.set_entry_point("translate_input")
workflow.add_edge("translate_input", "input_guardrail")
workflow.add_edge("input_guardrail", "llm_call")
workflow.add_edge("llm_call", "output_guardrail")
workflow.add_edge("output_guardrail", END)

app = workflow.compile()

# -------------------------------
# Example Usage
# -------------------------------
user_query = "Liste los servidores con IP 192.168.1.10 y host test.example.com"
result = app.invoke({"input": user_query})
print(result["final_output"])