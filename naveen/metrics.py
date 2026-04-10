import streamlit as st
import pandas as pd

def render_metrics(m, devices):

    # ---------------- CLEAN COLUMN HANDLING ----------------
    if "Provision_Time(min)" in devices.columns:
        devices["Provision_Time(min)"] = pd.to_numeric(
            devices["Provision_Time(min)"],
            errors="coerce"
        ).fillna(0)

        # SLA rule: provision time > 15 min
        sla_breached = (devices["Provision_Time(min)"] > 15).sum()
    else:
        sla_breached = 0

    # ---------------- METRICS ----------------
    total_devices = m.get("total", len(devices))
    critical_drifts = m.get("critical_drifts", 0)
    compliance_score = m.get("compliance_score", 0)
    compliant = m.get("compliant", 0)

    # ---------------- MODERN CARD DESIGN ----------------
    def card(title, value, subtitle, gradient):

        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {gradient});
            padding: 18px;
            border-radius: 16px;
            color: white;
            box-shadow: 0 6px 18px rgba(0,0,0,0.35);
            min-height: 130px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            transition: 0.3s ease;
        ">
            <div style="font-size:14px; opacity:0.9;">{title}</div>
            <div style="font-size:28px; font-weight:700; margin:6px 0;">{value}</div>
            <div style="font-size:12px; opacity:0.8;">{subtitle}</div>
        </div>
        """, unsafe_allow_html=True)

    # ---------------- 4-COLUMN LAYOUT ----------------
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        card(
            "🖥 Total Devices",
            total_devices,
            "Network inventory",
            "#2563eb, #1e3a8a"   # blue gradient
        )

    with c2:
        card(
            "⚠️ Critical Drifts",
            critical_drifts,
            "High severity issues",
            "#dc2626, #7f1d1d"   # red gradient
        )

    with c3:
        card(
            "🛡 Compliance Score",
            f"{compliance_score}%",
            f"{compliant}/{total_devices} compliant",
            "#16a34a, #065f46"   # green gradient
        )

    with c4:
        card(
            "🚨 SLA Breached",
            sla_breached,
            "Provision time > 15 min",
            "#9333ea, #4c1d95"   # purple gradient
        )