import streamlit as st
import json
import httpx
import pandas as pd
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI


def run_ai_analysis(devices):
    result = graph.invoke({"devices": devices})
    return result

# -------------------------------
# ✅ UI CONFIG
# -------------------------------
st.set_page_config(page_title="AI Network Compliance", layout="wide")
st.title("🤖 AI Network Compliance Dashboard")

# -------------------------------
# ✅ LLM SETUP
# -------------------------------
llm = ChatOpenAI(
    base_url="https://genailab.tcs.in",
    model="azure_ai/genailab-maas-DeepSeek-V3-0324",
    api_key="sk-7mnBOjys5IsMNfvbA2FVwg",  # 🔥 replace
    temperature=0,
    http_client=httpx.Client(verify=False)
)

# -------------------------------
# ✅ POLICY
# -------------------------------
policy = {
  "PolicyName": "Default Network Compliance Policy",
  "Version": "1.0",
  "AppliesTo": ["Switch", "Router", "Firewall"],
  "Parameters": {
    "OSVersion": {
      "MinimumSwitchOS": "v10.0",
      "MinimumRouterOS": "v12.0",
      "MinimumFirewallOS": "v6.0",
      "RiskWeight": 0.3,
      "Recommendation": "Upgrade firmware/OS to baseline version"
    },
    "Provisioning": {
      "SuccessRateThreshold": 0.95,
      "MaxProvisioningTimeMinutes": 20,
      "RiskWeight": 0.2,
      "Recommendation": "Investigate failed provisioning logs and optimize automation"
    },
    "Configuration": {
      "VLANConfigRequired": True,
      "ACLsRequired": True,
      "STPRequired": True,
      "EncryptionRequired": True,
      "RiskWeight": 0.25,
      "Recommendation": "Apply baseline configuration templates and enforce ACLs"
    },
    "SecurityControls": {
      "PortSecurityRequired": True,
      "MFAForAdminAccess": True,
      "LoggingToSIEM": True,
      "RiskWeight": 0.15,
      "Recommendation": "Enable port security, enforce MFA, forward logs to SIEM"
    },
    "DriftEvents": {
      "MaxAllowedDriftEvents": 0,
      "RiskWeight": 0.1,
      "Recommendation": "Remediate drift immediately and reapply baseline configs"
    }
  },
  "SeverityLevels": {
    "Compliant": "Meets all baseline requirements",
    "Non-Compliant": "Fails one or more parameters",
    "Critical": "Unauthorized device or multiple high-risk violations"
  }
}
 # keep your same policy

# -------------------------------
# ✅ DEVICES
# -------------------------------
devices = [
    {
        "DeviceID": "D2",
        "Type": "Switch",
        "Model": "SX200",
        "OSVersion": "v9.5",
        "ProvisioningStatus": "Failure",
        "VLANConfig": False,
        "PortSecurity": True,
        "STPEnabled": True,
        "ACLsApplied": False,
        "Logging": True,
        "RoutingProtocols": None,
        "ProtocolAuthEnabled": None,
        "EncryptionEnabled": None,
        "DriftEvents": 3
    },
    {
        "DeviceID": "D6",
        "Type": "Switch",
        "Model": "SX300",
        "OSVersion": "v10.2",
        "ProvisioningStatus": "Success",
        "VLANConfig": True,
        "PortSecurity": True,
        "STPEnabled": True,
        "ACLsApplied": True,
        "Logging": True,
        "RoutingProtocols": None,
        "ProtocolAuthEnabled": None,
        "EncryptionEnabled": None,
        "DriftEvents": 0
    },
    {
        "DeviceID": "D9",
        "Type": "Router",
        "Model": "RX200",
        "OSVersion": "v11.5",
        "ProvisioningStatus": "Failure",
        "VLANConfig": None,
        "PortSecurity": None,
        "STPEnabled": False,
        "ACLsApplied": False,
        "Logging": False,
        "RoutingProtocols": "BGP",
        "ProtocolAuthEnabled": False,
        "EncryptionEnabled": False,
        "DriftEvents": 2
    }
] # keep your same devices

# -------------------------------
# ✅ STATE
# -------------------------------
class GraphState(TypedDict):
    devices: List[Dict[str, Any]]
    results: List[Dict[str, Any]]

# -------------------------------
# ✅ CLEAN JSON
# -------------------------------
def clean_llm_output(content: str):
    content = content.strip()

    if content.startswith("```"):
        content = content.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(content)
    except:
        return {"error": content}

# -------------------------------
# ✅ AI NODE
# -------------------------------
def ai_node(state: GraphState) -> GraphState:
    results = []

    for device in state["devices"]:
        prompt = f"""
You are a Network Compliance AI.

Policy:
{json.dumps(policy)}

Device:
{json.dumps(device)}

Return ONLY JSON:
{{
  "issues": [],
  "risk": 0.0,
  "severity": "Low",
  "troubleshooting": "",
  "commands": ""
}}
"""

        response = llm.invoke(prompt)
        output = clean_llm_output(response.content)

        results.append({
            "DeviceID": device["DeviceID"],
            "analysis": output
        })

    return {"devices": state["devices"], "results": results}

# -------------------------------
# ✅ GRAPH
# -------------------------------
builder = StateGraph(GraphState)
builder.add_node("ai_node", ai_node)
builder.set_entry_point("ai_node")
builder.set_finish_point("ai_node")
graph = builder.compile()

# -------------------------------
# 🚀 UI BUTTON
# -------------------------------
if st.button("Run AI Analysis"):

    with st.spinner("Running AI analysis..."):
        result = graph.invoke({"devices": devices})
        results = result["results"]

    st.success("Analysis Complete ✅")

    # -------------------------------
    # 📊 SUMMARY CARDS
    # -------------------------------
    total = len(results)
    high = sum(1 for r in results if r["analysis"].get("severity") == "High")
    medium = sum(1 for r in results if r["analysis"].get("severity") == "Medium")
    low = sum(1 for r in results if r["analysis"].get("severity") == "Low")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Devices", total)
    col2.metric("High Risk", high)
    col3.metric("Medium Risk", medium)
    col4.metric("Low Risk", low)

    # -------------------------------
    # 📋 TABLE VIEW
    # -------------------------------
    table_data = []

    for r in results:
        analysis = r["analysis"]
        table_data.append({
            "DeviceID": r["DeviceID"],
            "Risk": analysis.get("risk"),
            "Severity": analysis.get("severity"),
            "Issues": len(analysis.get("issues", []))
        })

    df = pd.DataFrame(table_data)

    st.subheader("📊 Device Summary")
    st.dataframe(df)

    # -------------------------------
    # 🔍 DETAILS VIEW
    # -------------------------------
    st.subheader("🔍 Detailed Analysis")

    for r in results:
        with st.expander(f"Device {r['DeviceID']}"):
            st.json(r["analysis"])