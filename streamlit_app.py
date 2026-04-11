import streamlit as st
import pandas as pd
import subprocess
import os
import sys

# Constants
CSV_FILE = "data/jobs.csv"

def run_scan(niche):
    """Runs searcher.py and shows a generic progress bar."""
    progress_text = f"Searching for {niche} leads..."
    my_bar = st.progress(0, text=progress_text)
    
    try:
        # Step 1: Initialization
        my_bar.progress(30, text="📡 Connecting to job feeds...")
        
        # We use sys.executable to ensure we use the Streamlit environment's pandas
        result = subprocess.run(
            [sys.executable, "searcher.py", niche],
            capture_output=True, text=True, check=True
        )
        
        # Step 2: Processing
        my_bar.progress(70, text="🧠 AI is scoring and drafting pitches...")
        
        # Step 3: Completion
        my_bar.progress(100, text="✅ Scan complete!")
        st.success(f"Successfully updated leads for {niche}")
        st.rerun()
        
    except subprocess.CalledProcessError as e:
        st.error(f"The searcher agent crashed. Check the error details below:")
        st.code(e.stderr)

# --- UI Layout ---
st.set_page_config(page_title="Scout HQ", layout="wide")
st.title("💼 Freelancing Job Hunter")

# Sidebar Configuration
with st.sidebar:
    st.header("Search Settings")
    # Restored all niches
    target_niche = st.selectbox("Target Niche", 
        ["Cyber Security", "AI Agent Builder", "App Development", "Software Developer"])
    
    if st.button("🚀 Force Manual Scan"):
        run_scan(target_niche)
        
    if st.button("🗑️ Clear All Old Leads"):
        if os.path.exists(CSV_FILE):
            # Write a fresh header to avoid IndexError on next load
            pd.DataFrame(columns=['title','source','weightage_score','is_genuine','draft','found_at','service']).to_csv(CSV_FILE, index=False)
            st.rerun()

# --- Data Display Logic ---
if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
    
    # FIX: Map CSV headers to UI labels
    mapping = {
        'weightage_score': 'score',
        'found_at': 'last_scanned',
        'is_genuine': 'status'
    }
    df = df.rename(columns=mapping)

    # Metrics with empty-check safeguard
    col1, col2 = st.columns(2)
    col1.metric("Total Leads", len(df))
    
    high_match = len(df[df['score'] >= 70]) if 'score' in df.columns else 0
    col2.metric("High Match (70%+)", high_match)

    # Filtered Table View
    st.tabs(["New Discovery", "Applied & Archived"])
    
    # Only show leads for the selected niche
    display_df = df[df['service'] == target_niche] if 'service' in df.columns else df
    
    if not display_df.empty:
        # Sort by latest found
        if 'last_scanned' in display_df.columns:
            display_df = display_df.sort_values(by='last_scanned', ascending=False)
            
        st.dataframe(
            display_df[['score', 'title', 'source', 'draft', 'last_scanned']],
            column_config={"source": st.column_config.LinkColumn("Listing")},
            hide_index=True, 
            use_container_width=True
        )
    else:
        st.info(f"No 'New' leads found for {target_niche}. Try 'Force Manual Scan' or change the niche.")
else:
    st.warning("Database not found. Please run your first scan.")
