import streamlit as st
import pandas as pd

def render_device_inventory(devices):

    st.subheader("🖥 Device Inventory")

    def highlight(row):
        if row["Compliance"] == "Compliant":
            return ['background-color: rgba(16,185,129,0.12)'] * len(row)
        return ['background-color: rgba(239,68,68,0.12)'] * len(row)

    styled = devices.style.apply(highlight, axis=1)

    # IMPORTANT FIX 👇
    st.markdown(styled.to_html(), unsafe_allow_html=True)