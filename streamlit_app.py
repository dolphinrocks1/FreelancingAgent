import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Scout HQ", layout="wide", page_icon="🛡️")

# CSS to ensure the UI feels tight and professional
st.markdown("""
    <style>
    div[data-testid="stExpander"] { border: 1px solid #30363d; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

CSV_FILE = "data/jobs.csv"

def load_and_fix_data():
    if not os.path.exists(CSV_FILE): return pd.DataFrame()
    df = pd.read_csv(CSV_FILE)
    
    # 1. Column Mapping & Normalization
    if 'weightage_score' in df.columns:
        df = df.rename(columns={'weightage_score': 'score'})
    if 'draft' in df.columns:
        df = df.rename(columns={'draft': 'pitch'})
    
    # 2. Score Formatting (Integer for centering)
    if 'score' in df.columns:
        df['score'] = pd.to_numeric(df['score'], errors='coerce').fillna(0).astype(int)
    
    # 3. Timestamp & Sorting Logic
    # Convert found_at or last_scanned to datetime for proper sorting
    time_col = 'found_at' if 'found_at' in df.columns else 'last_scanned'
    if time_col in df.columns:
        df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
        # Sort Latest to Oldest
        df = df.sort_values(by=time_col, ascending=False)
    
    # 4. Fill missing metadata
    for col in ['status', 'service']:
        if col not in df.columns:
            df[col] = "New" if col == 'status' else "Cyber Security"
            
    return df

df = load_and_fix_data()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Scout HQ")
    service_choice = st.selectbox("Target Niche", 
                                ["Cyber Security", "AI Agent Builder", "App Developer", "Software Developer"])
    st.divider()
    if st.button("🔄 Refresh Data"):
        st.rerun()

# --- MAIN DASHBOARD ---
st.title("Lead Discovery Dashboard")

if not df.empty:
    # Tab Definition
    tab1, tab2 = st.tabs(["🆕 New Found Details", "✅ Applied Leads"])

    with tab1:
        new_df = df[(df['status'] == 'New') & (df['service'] == service_choice)].copy()
        
        if not new_df.empty:
            # Single Clean Table with "Mark Applied" as a checkbox column
            # We use data_editor to allow one-click status changes
            edited_df = st.data_editor(
                new_df[['score', 'title', 'source', 'pitch', 'last_scanned']],
                column_config={
                    "score": st.column_config.NumberColumn("Score", width="small", format="%d%%", help="AI Match Confidence"),
                    "title": st.column_config.TextColumn("Job Title", width="medium"),
                    "source": st.column_config.LinkColumn("Listing", display_text="View Job"),
                    "pitch": st.column_config.TextColumn("Proposed Pitch", width="large"),
                    "last_scanned": st.column_config.DatetimeColumn("Scanned At", format="D MMM, h:mm a")
                },
                hide_index=True,
                use_container_width=True,
                key="new_leads_table"
            )
            
            # Action logic for marking as applied below the table
            st.markdown("### Update Status")
            selected_job = st.selectbox("Select a job to mark as applied:", new_df['title'].tolist())
            if st.button("Move to Applied Tab"):
                idx = df[df['title'] == selected_job].index
                df.at[idx[0], 'status'] = 'Applied'
                df.to_csv(CSV_FILE, index=False)
                st.success(f"Updated {selected_job}")
                st.rerun()
        else:
            st.info(f"No new leads found for {service_choice}.")

    with tab2:
        applied_df = df[df['status'] == 'Applied'].copy()
        if not applied_df.empty:
            st.dataframe(
                applied_df[['score', 'title', 'source', 'last_scanned']],
                column_config={
                    "score": st.column_config.NumberColumn("Score", width="small", format="%d%%"),
                    "source": st.column_config.LinkColumn("Listing", display_text="View Job"),
                    "last_scanned": st.column_config.DatetimeColumn("Scanned At", format="D MMM, h:mm a")
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("You haven't marked any leads as applied yet.")
else:
    st.warning("No data found. Check your searcher.py execution logs.")
