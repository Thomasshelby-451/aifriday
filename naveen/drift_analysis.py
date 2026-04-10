import streamlit as st
import pandas as pd

def render_drift_analysis():

    st.subheader("⚙️ Configuration Drift Analysis")

    df = pd.read_csv("data/config_drift.csv")

    # Safe numeric conversion
    df["DriftEvents"] = pd.to_numeric(df["DriftEvents"], errors="coerce").fillna(0)

    # ---------------- KPIs ----------------
    total = len(df)
    compliant = df[df["ComplianceStatus"] == "Compliant"].shape[0]
    non_compliant = df[df["ComplianceStatus"] != "Compliant"].shape[0]
    avg_drift = df["DriftEvents"].mean()

    def card(title, value, subtitle, color):
        st.markdown(f"""
        <div class="card {color}">
            <h4>{title}</h4>
            <h2>{value}</h2>
            <p>{subtitle}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### 📊 Drift KPIs")

    # ✅ FIX: force equal column widths (prevents 4th card drop)
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])

    with c1:
        card("🖥 Total Devices", total, "In scope", "blue")

    with c2:
        card(
            "🟢 Compliant",
            compliant,
            f"{round((compliant/total)*100,1)}%",
            "green"
        )

    with c3:
        card(
            "🔴 Non-Compliant",
            non_compliant,
            f"{round((non_compliant/total)*100,1)}%",
            "red"
        )

    with c4:
        drift_color = "red" if avg_drift > 1 else "blue"
        card(
            "📉 Avg Drift",
            round(avg_drift, 2),
            "Deviation score",
            drift_color
        )

    st.markdown("---")

    # ---------------- TABLE ----------------
    st.markdown("### 📋 Drift Analysis")

    def highlight(row):
        if row["ComplianceStatus"] == "Compliant":
            return ["background-color: rgba(16,185,129,0.12)"] * len(row)

        elif row["DriftEvents"] >= 2:
            return ["background-color: rgba(239,68,68,0.12)"] * len(row)

        elif row["DriftEvents"] == 1:
            return ["background-color: rgba(245,158,11,0.12)"] * len(row)

        else:
            return ["background-color: rgba(59,130,246,0.08)"] * len(row)

    styled_df = df.style.apply(highlight, axis=1)

    st.dataframe(styled_df, use_container_width=True)