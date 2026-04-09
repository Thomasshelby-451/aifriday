#Incident Monitoring basic Dashboard and add the severity filter dropdown

import streamlit as st
import pandas as pd

# Page setup
st.set_page_config(page_title="Incident Monitoring Dashboard", layout="wide")
st.title("🚨 Incident Monitoring Dashboard")

# Example metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total Incidents", 128, 12)
col2.metric("Critical Alerts", 15, 3)
col3.metric("Resolved Today", 42, -5)

# Example trend chart
st.subheader("Incident Trend (Last 7 Days)")
incident_trend = pd.DataFrame({
    "Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    "Incidents": [20, 25, 18, 30, 22, 15, 28]
})
st.line_chart(incident_trend.set_index("Day"))

# Incident log data
data = {
    "Timestamp": ["2026-04-07 10:15", "2026-04-07 11:05", "2026-04-07 12:30", "2026-04-07 13:45"],
    "Severity": ["Critical", "High", "Medium", "Low"],
    "Source": ["Server-1", "Database", "API Gateway", "Load Balancer"],
    "Status": ["Open", "Investigating", "Resolved", "Open"]
}
df = pd.DataFrame(data)

# Severity filter dropdown
st.subheader("Incident Log")
severity_options = ["All"] + sorted(df["Severity"].unique())
selected_severity = st.selectbox("Filter by Severity", severity_options)

# Apply filter
if selected_severity != "All":
    filtered_df = df[df["Severity"] == selected_severity]
else:
    filtered_df = df

# Display filtered table
#st.dataframe(filtered_df, use_container_width=True)
st.dataframe(filtered_df, width="stretch")

