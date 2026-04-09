from langchain_openai import ChatOpenAI
import os
import httpx

# Disable SSL verification (not recommended for production)
client = httpx.Client(verify=False)

llm = ChatOpenAI(
    base_url="https://genailab.tcs.in",
    model="azure_ai/genailab-maas-DeepSeek-V3-0324",
    api_key="sk-7mnBOjys5IsMNfvbA2FVwg",  
    http_client=client
)

response = llm.invoke("explain about you")
print(response)