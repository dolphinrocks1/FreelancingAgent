import streamlit as st
import pandas as pd
import subprocess
import os

# App Branding
st.set_page_config(page_title="Freelancing Job Hunter", layout="wide", page_icon="💼")

CSV_FILE = "data/jobs.csv"

def run_scan(niche):
    """Executes the searcher agent and captures errors for the UI."""
    with st.spinner(f"Freelancing Job Hunter is scouting {niche}..."):
        try:
            # Capturing output allows us to see the exact crash reason in the UI
            result = subprocess.run(
                ["python", "searcher.py", niche], 
                capture_output=True, 
                text=True, 
                check=True
            )
            st.toast(f"Fresh leads found for {niche}!", icon="🎯")
        except subprocess.CalledProcessError as e:
            st.error("The searcher agent crashed. Check the error details below:")
            # Display the actual traceback to help with debugging
            st.code(e.stderr if e.stderr else e.stdout)

def load_and_repair_data():
    """Loads data and ensures all required columns exist to prevent KeyErrors."""
    if not os.path.exists(CSV_FILE):
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(CSV_FILE)
        
        # Define necessary columns and their default values
        required_schema = {
            'weightage_score': 0, 
            'draft': 'No pitch generated', 
            'status': 'New', 
            'service': 'General',
            'last_scanned': 'N/A',
            'title': 'Unknown Title',
            'source': '#'
        }
        
        # Automatically add missing columns so the UI doesn't crash
        for col, default_val in required_schema.items():
            if col not in df.columns:
                df[col] = default_val
        
        # Map internal CSV names to clean UI names
        df = df.rename(columns={'weightage_score': 'score', 'draft': 'pitch'})
        return df
    except Exception as e:
        st.error(f"Failed to load jobs database: {e}")
        return pd.DataFrame()

# --- UI HEADER ---
st.title("💼 Freelancing Job Hunter")

# --- SIDEBAR & AUTO-SCAN ---
with st.sidebar:
    st.header("Search Settings")
    niche_options = ["Cyber Security", "AI Agent Builder", "App Developer", "Software Developer"]
    
    # Selecting a niche triggers the scan automatically
    current_niche = st.selectbox(
        "Target Niche", 
        niche_options,
        key="niche_selector",
        on_change=lambda: run_scan(st.session_state.niche_selector)
    )
    
    if st.button("Force Manual Scan"):
        run_scan(current_niche)
        st.rerun()

# Load the repaired data
df = load_and_repair_data()

# Summary Metrics
if not df.empty:
    m1, m2 = st.columns(2)
    m1.metric("Total Leads", len(df))
    m2.metric("High Match (70%+)", len(df[df['score'] >= 70]))

# --- DASHBOARD TABS ---
tab1, tab2 = st.tabs(["🆕 New Discovery", "✅ Applied & Archived"])

with tab1:
    if not df.empty and 'service' in df.columns:
        # Show only new leads for the selected niche
        active = df[(df['status'] == 'New') & (df['service'] == current_niche)].copy()
        
        if not active.empty:
            active['Mark Applied'] = False
            # Interactive data editor
            edited = st.data_editor(
                active[['Mark Applied', 'title', 'source', 'score', 'pitch', 'last_scanned']],
                column_config={
                    "Mark Applied": st.column_config.CheckboxColumn("Apply?"),
                    "source": st.column_config.LinkColumn("Listing", display_text="View"),
                    "score": st.column_config.NumberColumn("Match", format="%d%%"),
                    "pitch": st.column_config.TextColumn("Proposed Pitch", width="large"),
                    "last_scanned": "Scanned At"
                },
                hide_index=True, use_container_width=True, key="discovery_table"
            )

            # Save logic for "Mark Applied"
            if edited['Mark Applied'].any():
                applied_titles = edited[edited['Mark Applied'] == True]['title'].tolist()
                df.loc[df['title'].isin(applied_titles), 'status'] = 'Applied'
                # Rename back to original CSV format before saving
                df.rename(columns={'score': 'weightage_score', 'pitch': 'draft'}).to_csv(CSV_FILE, index=False)
                st.rerun()
        else:
            st.info(f"No leads found for {current_niche} in the local database. Select the niche above to scan.")

with tab2:
    applied_leads = df[df['status'] == 'Applied'].copy()
    if not applied_leads.empty:
        applied_leads['Remove'] = False
        cleanup = st.data_editor(
            applied_leads[['Remove', 'title', 'source', 'score', 'last_scanned']],
            column_config={
                "Remove": st.column_config.CheckboxColumn("Delete?"),
                "source": st.column_config.LinkColumn("View")
            },
            hide_index=True, use_container_width=True, key="applied_table"
        )
        
        if cleanup['Remove'].any():
            to_delete = cleanup[cleanup['Remove'] == True]['title'].tolist()
            df = df[~df['title'].isin(to_delete)]
            df.rename(columns={'score': 'weightage_score', 'pitch': 'draft'}).to_csv(CSV_FILE, index=False)
            st.rerun()
    else:
        st.info("Leads you mark as 'Applied' will show up here for archiving.")
