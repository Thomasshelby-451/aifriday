from langchain_openai import ChatOpenAI
import os
import httpx

# Create an HTTP client with SSL verification disabled
client = httpx.Client(verify=False)

# Initialize the ChatOpenAI client
llm = ChatOpenAI(
    base_url="https://genailab.tcs.in",
    model="azure_ai/genailab-maas-DeepSeek-V3-0324",
    api_key="sk-7mnBOjys5IsMNfvbA2FVwg",  # Will be provided during event
    http_client=client
)

# Invoke the model
response = llm.invoke("Hi")
print(response)