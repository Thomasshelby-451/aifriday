import streamlit as st
import pandas as pd
from ai_engine import run_ai_analysis

def render_drift_analysis():

    st.subheader("⚙️ Configuration Drift Analysis")

    # ================= GLOBAL TABLE STYLE =================
    st.markdown("""
    <style>
    div[data-testid="column"] {
        border-right: 1px solid rgba(255,255,255,0.10);
        padding-right: 6px;
    }

    div[data-testid="column"]:last-child {
        border-right: none;
    }

    .row-container {
        border-bottom: 1px solid rgba(255,255,255,0.08);
        padding-bottom: 6px;
        margin-bottom: 6px;
    }
    </style>
    """, unsafe_allow_html=True)

    # ---------------- LOAD DATA ----------------
    df = pd.read_csv("data/config_drift.csv")
    df.columns = df.columns.str.strip()
    df["DriftEvents"] = pd.to_numeric(df["DriftEvents"], errors="coerce").fillna(0)

    # ---------------- KPIs ----------------
    total = len(df)
    compliant = df[df["ComplianceStatus"] == "Compliant"].shape[0]
    non_compliant = df[df["ComplianceStatus"] != "Compliant"].shape[0]
    avg_drift = df["DriftEvents"].mean()

    # ---------------- CARD FUNCTION ----------------
    def safe_card(col, title, value, subtitle, color):

        color_map = {
            "blue": ("#1e3a8a", "#2563eb"),
            "green": ("#065f46", "#047857"),
            "red": ("#7f1d1d", "#991b1b"),
            "purple": ("#4c1d95", "#6d28d9")
        }

        c1, c2 = color_map.get(color, ("#1f2937", "#111827"))

        with col:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {c1}, {c2});
                padding: 18px;
                border-radius: 14px;
                color: white;
                min-height: 120px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                box-shadow: 0 4px 14px rgba(0,0,0,0.4);
            ">
                <h4 style="margin:0; font-size:14px;">{title}</h4>
                <h2 style="margin:5px 0;">{value}</h2>
                <p style="margin:0; opacity:0.85;">{subtitle}</p>
            </div>
            """, unsafe_allow_html=True)

    # ---------------- KPI CARDS ----------------
    c1, c2, c3, c4 = st.columns(4)

    safe_card(c1, "🖥 Total Devices", total, "In scope", "blue")
    safe_card(c2, "🟢 Compliant", compliant, f"{round((compliant/total)*100,1)}%", "green")
    safe_card(c3, "🔴 Non-Compliant", non_compliant, f"{round((non_compliant/total)*100,1)}%", "red")

    drift_color = "red" if avg_drift > 1 else "blue"
    safe_card(c4, "📉 Avg Drift", round(avg_drift, 2), "Deviation score", drift_color)

    st.markdown("---")

    # ---------------- TABLE HEADER ----------------
    st.markdown("### 📋 Drift Analysis")

    h1, h2, h3, h4, h5, h6 = st.columns([1.6, 1.2, 1.2, 1, 1.3, 1])

    h1.markdown("**Device ID**")
    h2.markdown("**Type**")
    h3.markdown("**Model**")
    h4.markdown("**Drift**")
    h5.markdown("**Compliance**")
    h6.markdown("**Action**")

    st.markdown("---")

    # ---------------- COLOR FUNCTION ----------------
    def get_bg(status, drift):
        if status == "Compliant":
            return "rgba(16,185,129,0.12)"
        elif drift >= 2:
            return "rgba(239,68,68,0.12)"
        elif drift == 1:
            return "rgba(245,158,11,0.12)"
        else:
            return "rgba(59,130,246,0.08)"

    # ---------------- TABLE ROWS ----------------
    for i, row in df.iterrows():

        bg = get_bg(row["ComplianceStatus"], row["DriftEvents"])

        style = f"""
            background-color: {bg};
            padding: 10px;
            border-radius: 6px;
            border: 1px solid rgba(255,255,255,0.08);
        """

        c1, c2, c3, c4, c5, c6 = st.columns([1.6, 1.2, 1.2, 1, 1.3, 1])

        c1.markdown(f"<div style='{style}'>{row['DeviceID']}</div>", unsafe_allow_html=True)
        c2.markdown(f"<div style='{style}'>{row['Type']}</div>", unsafe_allow_html=True)
        c3.markdown(f"<div style='{style}'>{row['Model']}</div>", unsafe_allow_html=True)
        c4.markdown(f"<div style='{style}'>{row['DriftEvents']}</div>", unsafe_allow_html=True)
        c5.markdown(f"<div style='{style}'>{row['ComplianceStatus']}</div>", unsafe_allow_html=True)

        # ✅ ACTION BUTTON (FIXED INDENTATION)
        if row["ComplianceStatus"] == "Non-Compliant":

            if c6.button("🚀 Analyze", key=f"ai_{i}"):

                with st.spinner("Running AI analysis..."):

                    result = run_ai_analysis([{
                        "DeviceID": row["DeviceID"],
                        "Type": row["Type"],
                        "Model": row["Model"],
                        "OSVersion": row.get("OSVersion", ""),
                        "ProvisioningStatus": row.get("ProvisioningStatus", ""),
                        "VLANConfig": row.get("VLANConfig", ""),
                        "PortSecurity": row.get("PortSecurity", ""),
                        "STPEnabled": row.get("STPEnabled", ""),
                        "ACLsApplied": row.get("ACLsApplied", ""),
                        "Logging": row.get("Logging", ""),
                        "RoutingProtocols": row.get("RoutingProtocols", ""),
                        "ProtocolAuthEnabled": row.get("ProtocolAuthEnabled", ""),
                        "EncryptionEnabled": row.get("EncryptionEnabled", ""),
                        "DriftEvents": row.get("DriftEvents", 0)
                    }])

                st.success(f"AI Analysis Complete for {row['DeviceID']}")
                st.json(result)

        else:
            c6.markdown("—")