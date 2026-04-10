import streamlit as st
from datetime import datetime

from api.client import fetch_devices
from utils.helpers import compute_metrics

from components.metrics import render_metrics
#from components.compliance_overview import render_compliance_overview
from components.device_inventory import render_device_inventory
from components.config_drift import render_drift_analysis

st.set_page_config(page_title="Network Compliance Dashboard", layout="wide")

# HEADER
st.title("🛡 Network Compliance Dashboard")
st.caption("Real-time device + configuration drift monitoring")

if st.button("🔄 Refresh"):
    st.rerun()

# DATA
devices = fetch_devices()

# METRICS
metrics = compute_metrics(devices)
render_metrics(metrics, devices)

st.markdown("## ")

# CHARTS

# CONFIG DRIFT MODULE (NEW SYSTEM)
render_drift_analysis()

# DEVICE INVENTORY
render_device_inventory(devices)

# FOOTER
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

st.markdown("""
<style>

/* Background */
body {
    background-color: #0b1220;
}

/* Metric Cards */
.card {
    padding: 18px;
    border-radius: 14px;
    color: white;
    background: linear-gradient(135deg, #1f2937, #111827);
    box-shadow: 0 4px 14px rgba(0,0,0,0.4);
    transition: 0.3s ease;
}

.card:hover {
    transform: translateY(-3px);
}

.card.red {
    background: linear-gradient(135deg, #7f1d1d, #991b1b);
}

.card.green {
    background: linear-gradient(135deg, #065f46, #047857);
}

.card.blue {
    background: linear-gradient(135deg, #1e3a8a, #2563eb);
}

.card.purple {
    background: linear-gradient(135deg, #4c1d95, #6d28d9);
}

/* Table styling */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
}

/* Section spacing */
section {
    padding-top: 10px;
}

/* Titles */
h1, h2, h3 {
    color: #e5e7eb;
}

</style>
""", unsafe_allow_html=True)