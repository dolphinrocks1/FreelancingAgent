import streamlit as st
import pandas as pd
import subprocess
import os
import sys

CSV_FILE = "data/jobs.csv"

def run_scan(niche):
    """Runs searcher.py with site-agnostic progress bar."""
    my_bar = st.progress(0, text=f"Searching for {niche} leads...")
    try:
        my_bar.progress(30, text="📡 Connecting to job feeds...")
        # FIX: Corrected subprocess syntax
        subprocess.run([sys.executable, "searcher.py", niche], check=True)
        my_bar.progress(100, text="✅ Scan complete!")
        st.rerun()
    except Exception as e:
        st.error(f"Searcher failed: {e}")

st.set_page_config(page_title="Scout HQ", layout="wide")
st.title("💼 Freelancing Job Hunter")

# --- Sidebar ---
with st.sidebar:
    st.header("Search Settings")
    target_niche = st.selectbox("Target Niche", 
        ["Cyber Security", "AI Agent Builder", "App Development", "Software Developer"])
    
    if st.button("🚀 Force Manual Scan"):
        run_scan(target_niche)

# --- Data Loading ---
if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
    
    # Map CSV headers to UI labels
    mapping = {'weightage_score': 'score', 'found_at': 'last_scanned', 'is_genuine': 'status'}
    df = df.rename(columns=mapping)

    # Metrics
    col1, col2 = st.columns(2)
    col1.metric("Total Leads", len(df))
    high_match = len(df[df['score'] >= 70]) if 'score' in df.columns else 0
    col2.metric("High Match (70%+)", high_match)

    # --- Tabs Logic ---
    tab1, tab2 = st.tabs(["🆕 New Discovery", "✅ Applied & Archived"])

    with tab1:
        # Filter for 'New' or 'Verified' status
        new_leads = df[df['status'].isin(['New', 'Verified', 'System'])]
        if not new_leads.empty:
            st.dataframe(new_leads[['score', 'title', 'source', 'status', 'last_scanned']], 
                         use_container_width=True, hide_index=True)
        else:
            st.info("No new leads found. Run a scan!")

    with tab2:
        # Filter for 'Applied' status
        archived = df[df['status'] == 'Applied']
        if not archived.empty:
            st.dataframe(archived[['score', 'title', 'source', 'last_scanned']], 
                         use_container_width=True, hide_index=True)
            
            # Restored Purge Button for Archive
            if st.button("🗑️ Purge Archived Leads"):
                df = df[df['status'] != 'Applied']
                df.to_csv(CSV_FILE, index=False)
                st.rerun()
        else:
            st.write("No leads have been marked as 'Applied' yet.")

else:
    st.warning("Database empty. Run a scan to find leads.")
