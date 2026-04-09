#UI for incident management along with drilldown and colur coding bar chart and pie chart (interactive)
#record count at the bottom

import streamlit as st
import pandas as pd
import plotly.express as px

# --- Sample 20 Incident Data ---
data = {
    "Incident ID": [f"INC-{1001+i}" for i in range(20)],
    "Incident Name": [f"Incident{i+1}" for i in range(20)],
    "Timestamp": [
        "2026-04-08 02:15:00","2026-04-08 02:16:30","2026-04-08 02:18:10","2026-04-08 02:20:45","2026-04-08 02:21:50",
        "2026-04-08 02:25:00","2026-04-08 02:27:15","2026-04-08 02:30:00","2026-04-08 02:32:20","2026-04-08 02:35:00",
        "2026-04-08 02:37:10","2026-04-08 02:40:00","2026-04-08 02:42:30","2026-04-08 02:45:00","2026-04-08 02:47:20",
        "2026-04-08 02:50:00","2026-04-08 02:52:10","2026-04-08 02:55:00","2026-04-08 02:57:30","2026-04-08 03:00:00"
    ],
    "Source": [
        "Server-1","Database","API Gateway","Load Balancer","Web Server",
        "Firewall","Server-2","Database","API Gateway","Server-3",
        "Web Server","Load Balancer","Firewall","Database","API Gateway",
        "Server-4","Web Server","Firewall","Server-5","Database"
    ],
    "Alert Type": [
        "CPU Usage","Connection Timeout","Latency","Health Check Failed","Memory Usage",
        "Unauthorized Access","Disk Space","Query Failure","Rate Limit Exceeded","CPU Usage",
        "SSL Certificate","Node Failure","Port Scan Detected","Deadlock","Timeout",
        "Memory Usage","High Latency","Malware Detected","Disk Failure","Backup Failure"
    ],
    "Severity": [
        "Critical","High","Medium","Critical","Low",
        "Critical","High","Medium","High","Critical",
        "Medium","Critical","High","Medium","High",
        "Low","Medium","Critical","Critical","High"
    ],
    "Message": [
        "CPU usage exceeded 95%","Multiple DB connection failures","Response time > 2s","Node not responding","Memory usage at 70%",
        "Multiple failed login attempts","Disk usage > 90%","Slow queries detected","Too many requests per second","CPU usage exceeded 98%",
        "Certificate expiring soon","Node dropped from cluster","Suspicious traffic detected","Transaction deadlock detected","Requests timing out",
        "Memory usage at 65%","Page load > 3s","Malware signature found","Disk read errors detected","Scheduled backup failed"
    ],
    "Status": [
        "Open","Investigating","Open","Open","Resolved",
        "Open","Open","Investigating","Open","Open",
        "Open","Open","Open","Investigating","Open",
        "Resolved","Open","Open","Open","Open"
    ],
    "Assigned To": [
        "Alice (Ops)","Bob (DBA)","Carol (Backend)","Dave (Infra)","Eve (Support)",
        "Frank (Security)","Grace (Ops)","Bob (DBA)","Carol (Backend)","Alice (Ops)",
        "Eve (Support)","Dave (Infra)","Frank (Security)","Bob (DBA)","Carol (Backend)",
        "Grace (Ops)","Eve (Support)","Frank (Security)","Alice (Ops)","Bob (DBA)"
    ]
}

df = pd.DataFrame(data)

# --- Function to color severity in table ---
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

# --- Dashboard Layout ---
st.set_page_config(page_title="Incident Monitoring Dashboard", layout="wide")
st.title("🚨 Incident Monitoring Dashboard")

# --- Top Section: Expandable Metrics ---
st.subheader("📊 Key Metrics")
col1, col2, col3 = st.columns(3)

with col1.expander(f"Total Incidents: {len(df)}"):
    st.dataframe(df.style.applymap(color_severity, subset=["Severity"]), width="stretch")

with col2.expander(f"Critical Alerts: {(df['Severity'] == 'Critical').sum()}"):
    st.dataframe(df[df["Severity"] == "Critical"].style.applymap(color_severity, subset=["Severity"]), width="stretch")

with col3.expander(f"Resolved: {(df['Status'] == 'Resolved').sum()}"):
    st.dataframe(df[df["Status"] == "Resolved"].style.applymap(color_severity, subset=["Severity"]), width="stretch")

# --- Middle Section: Trend Charts ---
st.subheader("📈 Incident Trend by Severity")
trend_data = df.groupby("Severity").size().reset_index(name="Count")

# Define severity colors
severity_colors = {
    "Critical": "red",
    "High": "orange",
    "Medium": "yellow",
    "Low": "green"
}

colA, colB = st.columns(2)

with colA:
    fig_bar = px.bar(trend_data, x="Severity", y="Count", color="Severity",
                     color_discrete_map=severity_colors,
                     title="Incident Counts by Severity")
    st.plotly_chart(fig_bar, use_container_width=True)

with colB:
    fig_pie = px.pie(trend_data, values="Count", names="Severity",
                     color="Severity", color_discrete_map=severity_colors,
                     title="Incident Distribution")
    st.plotly_chart(fig_pie, use_container_width=True)

# --- Bottom Section: Incident Log with Filters + Search ---
st.subheader("📋 Incident Log")

# Filters
severity_options = ["All"] + sorted(df["Severity"].unique())
selected_severity = st.selectbox("Filter by Severity", severity_options)

status_options = ["All"] + sorted(df["Status"].unique())
selected_status = st.selectbox("Filter by Status", status_options)

search_id = st.text_input("🔎 Search by Incident ID (e.g., INC-1003)")

# Apply filters
filtered_df = df.copy()
if selected_severity != "All":
    filtered_df = filtered_df[filtered_df["Severity"] == selected_severity]
if selected_status != "All":
    filtered_df = filtered_df[filtered_df["Status"] == selected_status]
if search_id:
    filtered_df = filtered_df[filtered_df["Incident ID"].str.contains(search_id, case=False)]

# Display final filtered table
st.dataframe(filtered_df.style.applymap(color_severity, subset=["Severity"]), width="stretch")

# --- Record Count ---
st.write(f"**Total Records Visible:** {len(filtered_df)}")
