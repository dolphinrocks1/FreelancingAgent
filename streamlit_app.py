import streamlit as st
import pandas as pd
import os
import subprocess
import sys

# --- Configuration ---
# Aligned with searcher.py schema to prevent KeyErrors
CSV_FILE = "data/jobs.csv"
REQUIRED_COLS = ['id', 'title', 'source', 'weightage_score', 'service', 'is_genuine', 'draft', 'found_at']

st.set_page_config(page_title="Scout HQ", page_icon="💼", layout="wide")

def load_data():
    """Loads CSV and repairs missing columns or files on the fly."""
    if not os.path.exists(CSV_FILE):
        return pd.DataFrame(columns=REQUIRED_COLS)
    
    try:
        df = pd.read_csv(CSV_FILE)
        
        # REPAIR ENGINE: Ensures all UI-required columns exist
        for col in REQUIRED_COLS:
            if col not in df.columns:
                if col == 'is_genuine':
                    df[col] = 'New'
                elif col == 'weightage_score':
                    df[col] = 0
                else:
                    df[col] = ""
        
        # Ensure ID is a string for stable filtering
        df['id'] = df['id'].astype(str)
        return df
    except Exception as e:
        st.error(f"Error loading database: {e}")
        return pd.DataFrame(columns=REQUIRED_COLS)

# --- Sidebar ---
st.sidebar.header("Search Settings")
target_niche = st.sidebar.selectbox(
    "Target Niche",
    ["Cyber Security", "SOC", "AI Agent Builder", "Software Developer"]
)

if st.sidebar.button("🚀 Force Manual Scan"):
    with st.sidebar.status(f"Scanning for {target_niche}..."):
        # sys.executable ensures we use the Streamlit environment's packages
        result = subprocess.run(
            [sys.executable, "searcher.py", target_niche], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            st.sidebar.success("Scan Complete!")
            st.rerun()
        else:
            st.sidebar.error("Searcher Agent Crashed")
            with st.sidebar.expander("View Error Traceback"):
                st.code(result.stderr)

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Clear Database", help="This will delete all saved leads"):
    if os.path.exists(CSV_FILE):
        os.remove(CSV_FILE)
        st.rerun()

# --- Main Dashboard ---
st.title("💼 Freelancing Job Hunter")
df = load_data()

if not df.empty:
    # Filter based on the selected niche and status
    mask = (df['is_genuine'] != 'Applied') & (df['service'] == target_niche)
    display_df = df[mask].copy()
    
    # Dashboard Metrics
    m1, m2 = st.columns(2)
    m1.metric("Total Leads Found", len(display_df))
    # Filter for high matches (70+)
    high_match_count = len(display_df[display_df['weightage_score'].astype(float) >= 70])
    m2.metric("High Match (70%+)", high_match_count)

    tab1, tab2 = st.tabs(["🆕 New Discovery", "✅ Applied & Archived"])

    with tab1:
        if not display_df.empty:
            # Sort by weightage score descending to show best leads first
            sorted_df = display_df[['weightage_score', 'title', 'source', 'draft', 'found_at']].sort_values(
                by='weightage_score', 
                ascending=False
            )
            st.table(sorted_df)
        else:
            st.info(f"No active leads for '{target_niche}'. Try running a manual scan.")

    with tab2:
        archived = df[df['is_genuine'] == 'Applied']
        if not archived.empty:
            st.table(archived[['title', 'service', 'found_at']])
        else:
            st.info("No archived applications yet.")
else:
    st.warning("Database is currently empty. Use the sidebar to start a manual scan.")
