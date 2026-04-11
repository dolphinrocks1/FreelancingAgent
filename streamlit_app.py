import streamlit as st
import pandas as pd
import os

# Renamed for a more professional feel
st.set_page_config(page_title="Freelancing Job Hunter", layout="wide", page_icon="🎯")

CSV_FILE = "data/jobs.csv"

def load_data():
    if not os.path.exists(CSV_FILE): return pd.DataFrame()
    df = pd.read_csv(CSV_FILE)
    # Map CSV names to UI names
    df = df.rename(columns={'weightage_score': 'score', 'draft': 'pitch'})
    # Ensure status column exists
    if 'status' not in df.columns: df['status'] = 'New'
    return df

df = load_data()

st.title("🛰️ Freelancing Job Hunter")

tab1, tab2 = st.tabs(["🆕 New Discovery", "✅ Applied & Archived"])

with tab1:
    niche = st.selectbox("Filter Niche", ["Cyber Security", "AI Agent Builder"])
    # Reordered: Title -> Listing -> Score -> Pitch
    view_df = df[(df['status'] == 'New') & (df['service'] == niche)]
    
    if not view_df.empty:
        # User requested 'Mark Applied' inside table
        view_df['Mark Applied'] = False
        edited = st.data_editor(
            view_df[['Mark Applied', 'title', 'source', 'score', 'pitch', 'last_scanned']],
            column_config={
                "Mark Applied": st.column_config.CheckboxColumn("Apply?"),
                "source": st.column_config.LinkColumn("Listing", display_text="View"),
                "score": st.column_config.NumberColumn("Match", format="%d%%")
            },
            hide_index=True, use_container_width=True
        )
        
        # Logic to move to Applied
        if edited['Mark Applied'].any():
            selected_titles = edited[edited['Mark Applied'] == True]['title'].tolist()
            df.loc[df['title'].isin(selected_titles), 'status'] = 'Applied'
            df.rename(columns={'score': 'weightage_score', 'pitch': 'draft'}).to_csv(CSV_FILE, index=False)
            st.rerun()

with tab2:
    applied_df = df[df['status'] == 'Applied'].copy()
    if not applied_df.empty:
        # Added Remove Option
        applied_df['Delete'] = False
        deleted_df = st.data_editor(
            applied_df[['Delete', 'title', 'source', 'score']],
            column_config={"Delete": st.column_config.CheckboxColumn("Remove?")},
            hide_index=True, use_container_width=True
        )
        
        if deleted_df['Delete'].any():
            to_remove = deleted_df[deleted_df['Delete'] == True]['title'].tolist()
            df = df[~df['title'].isin(to_remove)]
            df.rename(columns={'score': 'weightage_score', 'pitch': 'draft'}).to_csv(CSV_FILE, index=False)
            st.rerun()
