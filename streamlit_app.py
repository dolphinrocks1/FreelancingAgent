import streamlit as st
import pandas as pd
import subprocess
import os
import sys
from datetime import datetime

CSV_FILE = "data/jobs.csv"

def run_scan(niche):
    """Generic progress tracker for any job source."""
    progress_bar = st.progress(0, text="Initializing Searcher Agent...")
    try:
        progress_bar.progress(25, text=f"📡 Connecting to data feeds for {niche}...")
        # Ensuring we use the Streamlit python environment to avoid ModuleNotFound
        result = subprocess.run(
            [sys.executable, "searcher.py", niche], 
            capture_output=True, text=True, check=True
        )
        progress_bar.progress(75, text="🧠 AI is scoring and drafting pitches...")
        progress_bar.progress(100, text="✅ Scan Complete!")
        st.success("New leads aggregated successfully.")
    except subprocess.CalledProcessError as e:
        st.error(f"Searcher failed: {e.stderr}")
    finally:
        import time
        time.sleep(1)
        st.rerun()

st.set_page_config(page_title="Scout HQ", layout="wide")
st.title("💼 Lead Discovery Dashboard")

# --- Sidebar ---
with st.sidebar:
    st.header("Search Settings")
    # Restored all niches including App Development
    current_niche = st.selectbox("Target Niche", 
        ["Cyber Security", "AI Agent Builder", "App Development", "Software Developer"])
    
    if st.button("🚀 Force Manual Scan"):
        run_scan(current_niche)
    
    if st.button("🗑️ Clear Database"):
        if os.path.exists(CSV_FILE):
            os.remove(CSV_FILE)
            st.rerun()

# --- Main Logic ---
if os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 60: # 60 bytes handles empty header-only files
    df = pd.read_csv(CSV_FILE)
    
    # Map headers to UI names
    col_map = {'weightage_score': 'score', 'is_genuine': 'status'}
    df = df.rename(columns=col_map)

    # Metrics with empty-check safeguard
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Leads", len(df))
    
    high_match = len(df[df['score'] >= 70]) if 'score' in df.columns else 0
    col2.metric("High Match", high_match)
    
    # FIX for IndexError: Only check iloc if df is NOT empty
    if not df.empty and 'last_scanned' in df.columns:
        df = df.sort_values(by='last_scanned', ascending=False)
        last_time = df['last_scanned'].iloc[0]
        col3.metric("Last Scan", str(last_time))

    # Table View - Filter by Niche
    st.subheader(f"📡 New Leads: {current_niche}")
    display_df = df[df['service'] == current_niche] if 'service' in df.columns else df
    
    if not display_df.empty:
        st.dataframe(
            display_df[['score', 'title', 'source', 'draft', 'last_scanned']],
            column_config={"source": st.column_config.LinkColumn("Listing")},
            hide_index=True, use_container_width=True
        )
    else:
        st.info(f"No results found for {current_niche} in the local database.")
else:
    st.warning("Database is empty. Please run a scan to find new leads.")
