import streamlit as st
import pandas as pd
import subprocess
import os
from datetime import datetime

CSV_FILE = "data/jobs.csv"

def run_scan(niche):
    """Runs searcher.py with a progress bar and error handling."""
    progress_bar = st.progress(0, text="Initializing Searcher Agent...")
    try:
        # Use sys.executable to ensure we use the same environment as Streamlit
        import sys
        progress_bar.progress(30, text=f"🔍 Scanning Upwork for {niche}...")
        
        result = subprocess.run(
            [sys.executable, "searcher.py", niche], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        progress_bar.progress(100, text="✅ Scan Complete!")
        st.success(f"Searcher output: {result.stdout.splitlines()[-1]}")
    except subprocess.CalledProcessError as e:
        st.error(f"Searcher crashed: {e.stderr}")
    finally:
        # Give the user a moment to see the 100% before refreshing
        import time
        time.sleep(1)
        st.rerun()

st.title("💼 Freelancing Job Hunter")

# --- Sidebar Settings ---
with st.sidebar:
    st.header("Search Settings")
    current_niche = st.selectbox("Target Niche", ["Cyber Security", "AI Agent Builder", "Software Developer"])
    if st.button("🚀 Force Manual Scan"):
        run_scan(current_niche)
    
    if st.button("🗑️ Clear Database"):
        if os.path.exists(CSV_FILE):
            os.remove(CSV_FILE)
            st.success("Database cleared!")
            st.rerun()

# --- Main Dashboard ---
if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
    
    # Ensure columns match what searcher.py produces
    # We normalize names here to ensure the UI doesn't break
    col_map = {'weightage_score': 'score', 'is_genuine': 'status'}
    df = df.rename(columns=col_map)

    # Metrics
    total_leads = len(df)
    high_match = len(df[df['score'] >= 70]) if 'score' in df.columns else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Leads", total_leads)
    col2.metric("High Match (70%+)", high_match)
    
    if 'last_scanned' in df.columns:
        # Sort by date to keep newest results on top
        df['last_scanned_dt'] = pd.to_datetime(df['last_scanned'], errors='coerce')
        df = df.sort_values(by='last_scanned_dt', ascending=False)
        last_time = df['last_scanned'].iloc[0]
        col3.metric("Last Scan", str(last_time))

    # Display Table
    st.subheader(f"📡 New Leads for {current_niche}")
    # Filter for current niche
    filtered_df = df[df['service'] == current_niche] if 'service' in df.columns else df
    
    if not filtered_df.empty:
        st.dataframe(
            filtered_df[['score', 'title', 'source', 'draft', 'last_scanned']],
            column_config={
                "score": st.column_config.ProgressColumn("Match", format="%d%%", min_value=0, max_value=100),
                "source": st.column_config.LinkColumn("Listing"),
                "draft": "Proposed Pitch"
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No leads found for this niche yet. Click 'Force Manual Scan'.")
else:
    st.warning("No data found. Run your first scan from the sidebar.")
