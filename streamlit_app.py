import streamlit as st
import pandas as pd
import os
import subprocess
import sys

# --- Configuration ---
CSV_FILE = "data/jobs.csv"
REQUIRED_COLS = ['id', 'title', 'source', 'weightage_score', 'service', 'is_genuine', 'draft', 'found_at']

st.set_page_config(page_title="Scout HQ", page_icon="💼", layout="wide")

def load_data():
    if not os.path.exists(CSV_FILE):
        return pd.DataFrame(columns=REQUIRED_COLS)
    
    df = pd.read_csv(CSV_FILE)
    
    # REPAIR ENGINE: If a column is missing, add it with default values to prevent KeyError
    for col in REQUIRED_COLS:
        if col not in df.columns:
            if col == 'is_genuine':
                df[col] = 'New'
            elif col == 'id':
                df[col] = range(len(df)) # Fallback IDs
            else:
                df[col] = ""
    
    df['id'] = df['id'].astype(str)
    return df

# --- Sidebar ---
st.sidebar.header("Search Settings")
target_niche = st.sidebar.selectbox(
    "Target Niche",
    ["Cyber Security", "SOC", "AI Agent Builder", "Software Developer"]
)

if st.sidebar.button("🚀 Force Manual Scan"):
    with st.sidebar.status(f"Scanning for {target_niche}..."):
        # Use sys.executable to ensure we use the same environment as Streamlit
        result = subprocess.run([sys.executable, "searcher.py", target_niche], capture_output=True, text=True)
        if result.returncode == 0:
            st.rerun()
        else:
            st.error("Searcher Agent Crashed")
            st.code(result.stderr)

if st.sidebar.button("🗑️ Clear Database"):
    if os.path.exists(CSV_FILE):
        os.remove(CSV_FILE)
        st.rerun()

# --- Main Dashboard ---
st.title("💼 Freelancing Job Hunter")
df = load_data()

if not df.empty:
    # Use 'is_genuine' instead of 'status' to match searcher.py
    mask = (df['is_genuine'] != 'Applied') & (df['service'] == target_niche)
    display_df = df[mask].copy()
    
    col1, col2 = st.columns(2)
    col1.metric("Total Leads", len(display_df))
    col2.metric("High Match (70%+)", len(display_df[display_df['weightage_score'] >= 70]))

    tab1, tab2 = st.tabs(["🆕 New Discovery", "✅ Applied & Archived"])

    with tab1:
        if not display_df.empty:
            # Note: Changed 'last_scanned' to 'found_at' to match your CSV
            st.table(display_df[['weightage_score', 'title', 'source', 'draft', 'found_at']].sort_values(by='weightage_score', ascending=False))
        else:
            st.info(f"No leads in database for {target_niche}. Run a scan!")

    with tab2:
        archived = df[df['is_genuine'] == 'Applied']
        if not archived.empty:
            st.table(archived[['title', 'service', 'found_at']])
else:
    st.warning("Database is empty. Run a scan to fetch jobs.")
