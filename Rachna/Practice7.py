#UI for incident management bar chart

import streamlit as st
import pandas as pd

# Page setup
st.set_page_config(page_title="Incident Monitoring Dashboard", layout="wide")
st.title("🚨 Incident Monitoring Dashboard")

# Sample incident data
data = {
    "Timestamp": [
        "2026-04-08 02:15:00",
        "2026-04-08 02:16:30",
        "2026-04-08 02:18:10",
        "2026-04-08 02:20:45",
        "2026-04-08 02:21:50"
    ],
    "Source": ["Server-1", "Database", "API Gateway", "Load Balancer", "Web Server"],
    "Alert Type": ["CPU Usage", "Connection Timeout", "Latency", "Health Check Failed", "Memory Usage"],
    "Severity": ["Critical", "High", "Medium", "Critical", "Low"],
    "Message": [
        "CPU usage exceeded 95%",
        "Multiple DB connection failures",
        "Response time > 2s",
        "Node not responding",
        "Memory usage at 70%"
    ],
    "Status": ["Open", "Investigating", "Open", "Open", "Resolved"],
    "Assigned To": ["Alice (Ops)", "Bob (DBA)", "Carol (Backend)", "Dave (Infra)", "Eve (Support)"]
}

df = pd.DataFrame(data)

# Add Incident Name and Incident ID columns
df.insert(0, "Incident Name", [f"Incident{i+1}" for i in range(len(df))])
df.insert(0, "Incident ID", [f"INC-{1001+i}" for i in range(len(df))])

# --- Top Section: KPIs ---
st.subheader("📊 Key Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Total Incidents", len(df))
col2.metric("Critical Alerts", (df["Severity"] == "Critical").sum())
col3.metric("Resolved", (df["Status"] == "Resolved").sum())

# --- Middle Section: Trend Chart ---
st.subheader("📈 Incident Trend by Severity")
trend_data = df.groupby("Severity").size().reset_index(name="Count")
st.bar_chart(trend_data.set_index("Severity"))

# --- Bottom Section: Incident Log with Filters + Search ---
st.subheader("📋 Incident Log")

# Severity filter
severity_options = ["All"] + sorted(df["Severity"].unique())
selected_severity = st.selectbox("Filter by Severity", severity_options)

# Status filter
status_options = ["All"] + sorted(df["Status"].unique())
selected_status = st.selectbox("Filter by Status", status_options)

# Incident ID search
search_id = st.text_input("🔎 Search by Incident ID (e.g., INC-1003)")

# Apply filters
filtered_df = df.copy()
if selected_severity != "All":
    filtered_df = filtered_df[filtered_df["Severity"] == selected_severity]
if selected_status != "All":
    filtered_df = filtered_df[filtered_df["Status"] == selected_status]
if search_id:
    filtered_df = filtered_df[filtered_df["Incident ID"].str.contains(search_id, case=False)]

# Display table
st.dataframe(filtered_df, width="stretch")
