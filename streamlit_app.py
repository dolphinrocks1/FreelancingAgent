import streamlit as st
import pandas as pd
import os
import subprocess
from datetime import datetime

# --- Configuration ---
CSV_FILE = "data/jobs.csv"

st.set_page_config(page_title="Scout HQ", page_icon="💼", layout="wide")

def load_data():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        # Ensure 'id' is string to prevent scientific notation in tables
        df['id'] = df['id'].astype(str)
        return df
    return pd.DataFrame()

# --- Sidebar ---
st.sidebar.header("Search Settings")

# UPDATED: Added 'SOC' to the niche selection
target_niche = st.sidebar.selectbox(
    "Target Niche",
    ["Cyber Security", "SOC", "AI Agent Builder", "Software Developer"]
)

if st.sidebar.button("🚀 Force Manual Scan"):
    with st.sidebar.status("Connecting to job feeds..."):
        # Pass the niche to the searcher script
        result = subprocess.run(["python", "searcher.py", target_niche], capture_output=True, text=True)
        if result.returncode == 0:
            st.sidebar.success("Scan Complete!")
            st.rerun()
        else:
            st.sidebar.error("The searcher agent crashed.")
            st.code(result.stderr)

if st.sidebar.button("🗑️ Clear Database"):
    if os.path.exists(CSV_FILE):
        os.remove(CSV_FILE)
        st.rerun()

# --- Main Dashboard ---
st.title("💼 Freelancing Job Hunter")

df = load_data()

# Logic check for empty dataframe to prevent IndexErrors
if not df.empty:
    # Filter by selected niche and status
    mask = (df['is_genuine'] != 'Applied') & (df['service'] == target_niche)
    display_df = df[mask].copy()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Leads", len(display_df))
    with col2:
        high_match = len(display_df[display_df['weightage_score'] >= 70])
        st.metric("High Match (70%+)", high_match)

    # UI Tabs
    tab1, tab2 = st.tabs(["🆕 New Discovery", "✅ Applied & Archived"])

    with tab1:
        if not display_df.empty:
            # Sort by highest score first
            st.table(display_df[['weightage_score', 'title', 'source', 'draft', 'found_at']].sort_values(by='weightage_score', ascending=False))
        else:
            st.info(f"No leads found for {target_niche} in the local database. Try a manual scan.")

    with tab2:
        archived = df[df['is_genuine'] == 'Applied']
        if not archived.empty:
            st.table(archived[['title', 'service', 'found_at']])
        else:
            st.write("No archived jobs yet.")

else:
    st.warning("Database is empty. Select a niche and run a manual scan to begin.")
