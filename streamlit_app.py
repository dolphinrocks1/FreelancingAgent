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
        subprocess.run([sys.executable, "searcher.py", niche], check=True)
        my_bar.progress(100, text="✅ Scan complete!")
        st.rerun()
    except Exception as e:
        st.error(f"Searcher failed: {e}")

def save_changes(df):
    """Helper to save UI changes back to the original CSV headers."""
    # Reverse the mapping back to CSV headers before saving
    reverse_mapping = {'score': 'weightage_score', 'last_scanned': 'found_at', 'status': 'is_genuine'}
    to_save = df.rename(columns=reverse_mapping)
    to_save.to_csv(CSV_FILE, index=False)

st.set_page_config(page_title="Scout HQ", layout="wide")
st.title("💼 Freelancing Job Hunter")

# --- Sidebar ---
with st.sidebar:
    st.header("Search Settings")
    target_niche = st.selectbox("Target Niche", 
        ["Cyber Security", "AI Agent Builder", "App Development", "Software Developer"])
    
    if st.button("🚀 Force Manual Scan"):
        run_scan(target_niche)
    
    st.divider()
    if st.button("🗑️ Clear Database"):
        if os.path.exists(CSV_FILE):
            os.remove(CSV_FILE)
            st.rerun()

# --- Data Loading & Transformation ---
if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
    
    # SAFETY: Ensure critical columns exist before UI processing to avoid KeyErrors
    if 'is_genuine' not in df.columns:
        df['is_genuine'] = 'New'
    if 'service' not in df.columns:
        df['service'] = target_niche
    
    if df.empty:
        st.info("The local database is currently empty. Run a manual scan to populate it.")
    else:
        # Map CSV headers to UI labels
        mapping = {'weightage_score': 'score', 'found_at': 'last_scanned', 'is_genuine': 'status'}
        df = df.rename(columns=mapping)

        # Tabs
        tab1, tab2 = st.tabs(["🆕 New Discovery", "✅ Applied & Archived"])

        with tab1:
            # Filter for non-applied leads for this niche
            mask = (df['status'] != 'Applied') & (df['service'] == target_niche)
            new_leads = df[mask].copy()

            if not new_leads.empty:
                st.info("💡 Check the box in the 'Apply' column to move a lead to the Archive.")
                
                # Add a temporary boolean column for the editor
                new_leads['Apply'] = False
                
                # Use data_editor for interactivity
                edited_df = st.data_editor(
                    new_leads[['Apply', 'score', 'title', 'source', 'status', 'last_scanned']],
                    column_config={
                        "Apply": st.column_config.CheckboxColumn("Apply?", default=False),
                        "source": st.column_config.LinkColumn("Listing"),
                        "score": st.column_config.NumberColumn(format="%d%%")
                    },
                    disabled=["score", "title", "source", "status", "last_scanned"],
                    hide_index=True,
                    use_container_width=True,
                    key="new_leads_editor"
                )

                # Check if any checkboxes were ticked
                if edited_df['Apply'].any():
                    applied_ids = edited_df[edited_df['Apply'] == True]['source'].tolist()
                    # Update main dataframe status
                    df.loc[df['source'].isin(applied_ids), 'status'] = 'Applied'
                    save_changes(df)
                    st.success(f"Moved {len(applied_ids)} leads to Applied & Archived!")
                    st.rerun()
            else:
                st.write(f"No new leads found for {target_niche}.")

        with tab2:
            archived = df[df['status'] == 'Applied']
            if not archived.empty:
                st.dataframe(
                    archived[['score', 'title', 'source', 'last_scanned']], 
                    column_config={"source": st.column_config.LinkColumn("Listing")},
                    use_container_width=True, 
                    hide_index=True
                )
                
                if st.button("🗑️ Purge Archived Leads"):
                    df = df[df['status'] != 'Applied']
                    save_changes(df)
                    st.rerun()
            else:
                st.write("No leads have been marked as 'Applied' yet.")
else:
    st.warning("No database found. Please run a manual scan to initialize jobs.csv.")
