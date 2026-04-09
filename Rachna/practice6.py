#Incident Ticketing +basic dashboard+ filter

import streamlit as st
import pandas as pd
from langchain_openai import ChatOpenAI
import httpx

# --- Setup LLM ---
client = httpx.Client(verify=False)
llm = ChatOpenAI(
    base_url="https://genailab.tcs.in",
    model="azure_ai/genailab-maas-DeepSeek-V3-0324",
    api_key="sk-7mnBOjys5IsMNfvbA2FVwg",
    http_client=client
)

# --- Simulated raw alerts ---
raw_alerts = [
    {"timestamp": "2026-04-08 00:30", "source": "Server-1", "message": "CPU usage exceeded 95%"},
    {"timestamp": "2026-04-08 00:35", "source": "Database", "message": "Connection timeout errors"},
    {"timestamp": "2026-04-08 00:40", "source": "API Gateway", "message": "High latency detected"},
]

# --- Streamlit UI ---
st.set_page_config(page_title="Incident Ticketing Dashboard", layout="wide")
st.title("🚨 AI-Powered Incident Ticketing")

# Step 1: Show raw alerts
st.subheader("Raw Alerts from Monitoring Tools")
st.json(raw_alerts)

# Step 2: AI enrichment
tickets = []
for alert in raw_alerts:
    prompt = f"""
    Convert this alert into a detailed incident ticket:
    Alert: {alert}
    Provide:
    - Detailed description
    - Severity (Critical/High/Medium/Low)
    - Suggested resolution steps
    """
    response = llm.invoke(prompt)
    enriched = response.content

    # For demo, store enriched text
    tickets.append({
        "Timestamp": alert["timestamp"],
        "Source": alert["source"],
        "Description": enriched,
    })

# Step 3: Display formatted tickets with severity filter
st.subheader("Incident Tickets")
df = pd.DataFrame(tickets)

# --- Severity filter dropdown ---
severity_options = ["All", "Critical", "High", "Medium", "Low"]
selected_severity = st.selectbox("Filter by Severity", severity_options)

# Apply filter (simple text search in Description for demo)
if selected_severity != "All":
    filtered_df = df[df["Description"].str.contains(selected_severity, case=False)]
else:
    filtered_df = df

st.dataframe(filtered_df, width="stretch")

# Step 4: Dashboard metrics
st.subheader("Dashboard Overview")
col1, col2, col3 = st.columns(3)
col1.metric("Total Incidents", len(tickets))
col2.metric("Critical Alerts", sum("Critical" in t["Description"] for t in tickets))
col3.metric("Resolved Today", 0)  # placeholder

# Step 5: Trend chart (simulated)
trend_data = pd.DataFrame({
    "Hour": ["00:30", "00:35", "00:40"],
    "Incidents": [1, 1, 1]
})
st.line_chart(trend_data.set_index("Hour"))
