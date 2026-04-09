#UI for incident management along with drilldown and colur coding bar chart
import streamlit as st
import pandas as pd
# Page setup
st.set_page_config(page_title="Incident Monitoring Dashboard", layout="wide")
st.title("🚨 Incident Monitoring Dashboard")
# Sample incident data
data = {
    "Incident ID": [f"INC-{1001+i}" for i in range(5)],
    "Incident Name": [f"Incident{i+1}" for i in range(5)],
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

# --- Function to color severity ---
def color_severity(val):
    if val == "Critical":
        return "background-color: red; color: white"
    elif val == "High":
        return "background-color: orange; color: black"
    elif val == "Medium":
        return "background-color: yellow; color: black"
    elif val == "Low":
        return "background-color: lightgreen; color: black"
    return ""

# --- Top Section: Expandable Metrics ---
st.subheader("📊 Key Metrics")

col1, col2, col3 = st.columns(3)

with col1.expander(f"Total Incidents: {len(df)}"):
    st.dataframe(df.style.applymap(color_severity, subset=["Severity"]), width="stretch")

with col2.expander(f"Critical Alerts: {(df['Severity'] == 'Critical').sum()}"):
    st.dataframe(df[df["Severity"] == "Critical"].style.applymap(color_severity, subset=["Severity"]), width="stretch")

with col3.expander(f"Resolved: {(df['Status'] == 'Resolved').sum()}"):
    st.dataframe(df[df["Status"] == "Resolved"].style.applymap(color_severity, subset=["Severity"]), width="stretch")

# --- Middle Section: Trend Chart ---
st.subheader("📈 Incident Trend by Severity")
trend_data = df.groupby("Severity").size().reset_index(name="Count")
st.bar_chart(trend_data.set_index("Severity"))

# --- Bottom Section: Incident Log ---
st.subheader("📋 Incident Log")
st.dataframe(df.style.applymap(color_severity, subset=["Severity"]), width="stretch")
