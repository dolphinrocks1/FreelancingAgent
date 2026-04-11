import streamlit as st
import pandas as pd
import subprocess
import os

st.set_page_config(page_title="Freelancing Job Hunter", layout="wide", page_icon="💼")

CSV_FILE = "data/jobs.csv"

def run_scan(niche):
    with st.spinner(f"Freelancing Job Hunter is scouting {niche}..."):
        try:
            # Capture output so we can see the actual error in the UI
            result = subprocess.run(
                ["python", "searcher.py", niche], 
                capture_output=True, 
                text=True, 
                check=True
            )
            st.toast(f"Fresh leads found for {niche}!", icon="🎯")
        except subprocess.CalledProcessError as e:
            st.error(f"Scan Failed! Error details:")
            st.code(e.stderr) # This will show the actual Python traceback from searcher.py

def load_data():
    if not os.path.exists(CSV_FILE): return pd.DataFrame()
    df = pd.read_csv(CSV_FILE)
    df = df.rename(columns={'weightage_score': 'score', 'draft': 'pitch'})
    if 'status' not in df.columns: df['status'] = 'New'
    return df

st.title("💼 Freelancing Job Hunter")

# Sidebar with Automatic Trigger
with st.sidebar:
    st.header("Search Settings")
    current_niche = st.selectbox(
        "Target Niche", 
        ["Cyber Security", "AI Agent Builder", "App Developer", "Software Developer"],
        key="niche_selector",
        on_change=lambda: run_scan(st.session_state.niche_selector)
    )
    if st.button("Force Manual Scan"):
        run_scan(current_niche)
        st.rerun()

df = load_data()

tab1, tab2 = st.tabs(["🆕 New Discovery", "✅ Applied & Archived"])

with tab1:
    if not df.empty:
        active_leads = df[(df['status'] == 'New') & (df['service'] == current_niche)].copy()
        if not active_leads.empty:
            active_leads['Mark Applied'] = False
            # Title -> Listing -> Score -> Pitch -> Scanned At
            edited = st.data_editor(
                active_leads[['Mark Applied', 'title', 'source', 'score', 'pitch', 'last_scanned']],
                column_config={
                    "Mark Applied": st.column_config.CheckboxColumn("Apply?"),
                    "source": st.column_config.LinkColumn("Listing", display_text="View"),
                    "score": st.column_config.NumberColumn("Match", format="%d%%"),
                    "pitch": st.column_config.TextColumn("Pitch", width="large")
                },
                hide_index=True, use_container_width=True, key="disc_table"
            )

            if edited['Mark Applied'].any():
                selected = edited[edited['Mark Applied'] == True]['title'].tolist()
                df.loc[df['title'].isin(selected), 'status'] = 'Applied'
                df.rename(columns={'score': 'weightage_score', 'pitch': 'draft'}).to_csv(CSV_FILE, index=False)
                st.rerun()
        else:
            st.info(f"No local leads for {current_niche}. Select it above to trigger a scan.")

with tab2:
    applied_df = df[df['status'] == 'Applied'].copy()
    if not applied_df.empty:
        applied_df['Remove'] = False
        cleanup = st.data_editor(
            applied_df[['Remove', 'title', 'source', 'score', 'last_scanned']],
            column_config={"Remove": st.column_config.CheckboxColumn("Delete?"), "source": st.column_config.LinkColumn("View")},
            hide_index=True, use_container_width=True, key="app_table"
        )
        if cleanup['Remove'].any():
            to_del = cleanup[cleanup['Remove'] == True]['title'].tolist()
            df = df[~df['title'].isin(to_del)]
            df.rename(columns={'score': 'weightage_score', 'pitch': 'draft'}).to_csv(CSV_FILE, index=False)
            st.rerun()
    else:
        st.info("No applied leads yet.")
