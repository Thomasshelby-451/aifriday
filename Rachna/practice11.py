#travel expense AI agent basic code

import streamlit as st
import pandas as pd

# --- Sample travel expenses ---
expenses = [
    {"Date": "2026-04-01", "Category": "Flight", "Description": "Kolkata to Delhi", "Amount": 12000},
    {"Date": "2026-04-02", "Category": "Hotel", "Description": "Delhi Marriott", "Amount": 8000},
    {"Date": "2026-04-02", "Category": "Meals", "Description": "Dinner with client", "Amount": 1500},
    {"Date": "2026-04-03", "Category": "Taxi", "Description": "Airport transfer", "Amount": 600},
    {"Date": "2026-04-03", "Category": "Misc", "Description": "Conference fee", "Amount": 5000},
]

# Convert to DataFrame
df = pd.DataFrame(expenses)

# Summarize by category
summary = df.groupby("Category")["Amount"].sum().reset_index()

# --- Streamlit UI ---
st.title("🧾 Travel Expense Report")

st.subheader("Detailed Expenses")
st.table(df)

st.subheader("Summary by Category")
st.table(summary)

st.subheader("Total Expenses")
st.write(f"**₹{df['Amount'].sum()}**")
