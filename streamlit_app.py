import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Scout HQ", layout="wide", page_icon="🛡️")

# Center alignment for the Score column
st.markdown("""
    <style>
    [data-testid="stHeader"] th:nth-child(1), td:nth-child(1) { text-align: center !important; }
    </style>
""", unsafe_allow_html=True)

CSV_FILE = "data/jobs.csv"

def load_data():
    if not os.path.exists(CSV_FILE):
        return pd.DataFrame()
    
    df = pd.read_csv(CSV_FILE)
    
    # 1. Map actual CSV columns to UI names
    rename_map = {
        'weightage_score': 'score',
        'draft': 'pitch'
    }
    df = df.rename(columns=rename_map)
    
    # 2. Ensure all required columns exist to prevent KeyError
    required_cols = {
        'score': 0,
        'title': 'Unknown Title',
        'source': '#',
        'pitch': 'No pitch generated',
        'last_scanned': 'N/A',
        'status': 'New',
        'service': 'Cyber Security'
    }
    for col, default in required_cols.items():
        if col not in df.columns:
            df[col] = default

    # 3. Clean and Sort
    df['score'] = pd.to_numeric(df['score'], errors='coerce').fillna(0).astype(int)
    
    # Sort latest to oldest if a timestamp is found in the 'last_scanned' or 'found_at'
    if 'last_scanned' in df.columns:
        df = df.sort_index(ascending=False) # Fallback to index sorting for 'latest first'
        
    return df

df = load_data()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Scout HQ")
    service_choice = st.selectbox("Target Niche", 
                                ["Cyber Security", "AI Agent Builder", "App Developer", "Software Developer"])
    st.divider()
    if st.button("🔄 Refresh Data"):
        st.rerun()

# --- MAIN UI ---
st.title("Lead Discovery Dashboard")

if not df.empty:
    tab1, tab2 = st.tabs(["🆕 New Found Details", "✅ Applied Leads"])

    with tab1:
        # Filter for current niche and status
        new_df = df[(df['status'] == 'New') & (df['service'] == service_choice)]
        
        if not new_df.empty:
            st.data_editor(
                new_df[['score', 'title', 'source', 'pitch', 'last_scanned']],
                column_config={
                    "score": st.column_config.NumberColumn("Score", width="small", format="%d%%"),
                    "source": st.column_config.LinkColumn("Listing", display_text="View Job"),
                    "pitch": st.column_config.TextColumn("Proposed Pitch", width="large"),
                    "last_scanned": "Scanned At"
                },
                hide_index=True,
                use_container_width=True,
                disabled=True,
                key="discovery_table"
            )
            
            # Application Action
            st.markdown("---")
            with st.expander("Update Lead Status"):
                job_to_update = st.selectbox("Select job to move to Applied:", new_df['title'].tolist())
                if st.button("Mark as Applied"):
                    df.loc[df['title'] == job_to_update, 'status'] = 'Applied'
                    df.to_csv(CSV_FILE, index=False)
                    st.success(f"Moved '{job_to_update}' to Applied tab.")
                    st.rerun()
        else:
            st.info(f"No new leads for {service_choice}.")

    with tab2:
        applied_df = df[df['status'] == 'Applied']
        if not applied_df.empty:
            st.table(applied_df[['score', 'title', 'source', 'last_scanned']])
        else:
            st.info("No applied leads yet.")
else:
    st.warning("No data found in jobs.csv.")
