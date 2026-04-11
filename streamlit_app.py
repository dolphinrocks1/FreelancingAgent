import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Scout HQ", layout="wide", page_icon="🛡️")

# CSS to ensure scannability and professional feel
st.markdown("""
    <style>
    [data-testid="stHeader"] th { text-align: left !important; }
    .stDataFrame td { vertical-align: middle !important; }
    </style>
""", unsafe_allow_html=True)

CSV_FILE = "data/jobs.csv"

def load_data():
    if not os.path.exists(CSV_FILE):
        return pd.DataFrame()
    
    df = pd.read_csv(CSV_FILE)
    
    # 1. Column Mapping
    rename_map = {'weightage_score': 'score', 'draft': 'pitch'}
    df = df.rename(columns=rename_map)
    
    # 2. Fix 'Scanned At' data
    # If the CSV column is empty or missing, we use the file's last modified time as a proxy
    file_mod_time = datetime.fromtimestamp(os.path.getmtime(CSV_FILE)).strftime('%Y-%m-%d %H:%M')
    if 'last_scanned' not in df.columns:
        df['last_scanned'] = file_mod_time
    df['last_scanned'] = df['last_scanned'].fillna(file_mod_time)

    # 3. Ensure essential columns exist
    defaults = {'status': 'New', 'service': 'Cyber Security', 'pitch': 'AI analysis pending...'}
    for col, val in defaults.items():
        if col not in df.columns:
            df[col] = val

    # 4. Interactive 'Applied' column for the table
    df['Mark Applied'] = df['status'] == 'Applied'
    
    # 5. Type Casting & Latest First
    df['score'] = pd.to_numeric(df['score'], errors='coerce').fillna(0).astype(int)
    return df.sort_index(ascending=False)

df = load_data()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Scout HQ")
    service_choice = st.selectbox("Target Niche", 
                                ["Cyber Security", "AI Agent Builder", "App Developer", "Software Developer"])
    st.divider()
    if st.button("🔄 Sync & Refresh"):
        st.rerun()

# --- MAIN UI ---
st.title("Lead Discovery Dashboard")

if not df.empty:
    tab1, tab2 = st.tabs(["🆕 New Found Details", "✅ Applied Leads"])

    with tab1:
        # Filter for the view
        active_mask = (df['status'] == 'New') & (df['service'] == service_choice)
        active_df = df[active_mask].copy()
        
        if not active_df.empty:
            # Table logic with "Mark Applied" as an interactive column
            # Note the column order: title -> Listing -> score -> pitch -> last_scanned
            edited_df = st.data_editor(
                active_df[['Mark Applied', 'title', 'source', 'score', 'pitch', 'last_scanned']],
                column_config={
                    "Mark Applied": st.column_config.CheckboxColumn("Applied?", help="Check to move to Applied tab"),
                    "title": st.column_config.TextColumn("Job Title", width="medium"),
                    "source": st.column_config.LinkColumn("Listing", display_text="View Job"),
                    "score": st.column_config.NumberColumn("Score", format="%d%%", width="small"),
                    "pitch": st.column_config.TextColumn("Proposed Pitch", width="large"),
                    "last_scanned": st.column_config.TextColumn("Scanned At", width="small")
                },
                hide_index=True,
                use_container_width=True,
                key="editor_table"
            )

            # 6. Save changes if a checkbox is clicked
            # Detect which rows were changed to True
            if not edited_df.equals(active_df[['Mark Applied', 'title', 'source', 'score', 'pitch', 'last_scanned']]):
                for i, row in edited_df.iterrows():
                    if row['Mark Applied']:
                        # Match by title to update original master dataframe
                        df.loc[df['title'] == row['title'], 'status'] = 'Applied'
                
                # Cleanup temporary column before saving to CSV
                save_df = df.drop(columns=['Mark Applied'])
                # Re-map back to original CSV names
                save_df = save_df.rename(columns={'score': 'weightage_score', 'pitch': 'draft'})
                save_df.to_csv(CSV_FILE, index=False)
                st.toast("Updated lead status!", icon="✅")
                st.rerun()
        else:
            st.info(f"No new leads found for {service_choice}.")

    with tab2:
        applied_df = df[df['status'] == 'Applied']
        if not applied_df.empty:
            st.dataframe(
                applied_df[['title', 'source', 'score', 'last_scanned']],
                column_config={
                    "source": st.column_config.LinkColumn("Listing", display_text="View Job"),
                    "score": st.column_config.NumberColumn("Score", format="%d%%")
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No applied leads recorded yet.")
else:
    st.warning("No data found in data/jobs.csv. Run a scan first.")
