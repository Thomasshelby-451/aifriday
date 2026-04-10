"""import streamlit as st
import plotly.express as px

def render_compliance_overview(devices):

    st.subheader("📊 Compliance Overview")

    fig = px.pie(
        devices,
        names="Compliance",
        color="Compliance",
        color_discrete_map={
            "Compliant": "#10b981",
            "Non-Compliant": "#ef4444"
        },
        hole=0.6
    )

    st.plotly_chart(fig, use_container_width=True)"""