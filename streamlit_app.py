import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="SIEM/SOAR Scout", layout="wide")

# Center-align the 'Score' column via CSS
st.markdown("""
    <style>
    [data-testid="stTable"] td:nth-child(1), [data-testid="stMetricValue"] { text-align: center; }
    .stDataFrame td:nth-child(1) { display: flex; justify-content: center; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

CSV_FILE = "data/jobs.csv"

def load_data():
    if not os.path.exists(CSV_FILE): return pd.DataFrame()
    df = pd.read_csv(CSV_FILE)
    # Ensure Score is numeric to prevent '0' default display
    if 'score' in df.columns:
        df['score'] = pd.to_numeric(df['score'], errors='coerce').fillna(0).astype(int)
    return df

df = load_data()

# --- HEADER & NICHE SELECTION ---
col_head, col_sync = st.columns([4, 1])
with col_head:
    st.title("🛡️ Scout HQ")
    service_choice = st.selectbox("Target Niche", ["Cyber Security", "AI Agent Builder", "App Developer", "Software Developer"])

# --- TABULAR INTERFACE ---
if not df.empty:
    new_df = df[(df['status'] == 'New') & (df['service'] == service_choice)].copy()
    
    st.subheader(f"📊 Fresh Leads: {service_choice}")
    
    # The interactive table
    st.data_editor(
        new_df[['score', 'title', 'source', 'pitch', 'last_scanned']],
        column_config={
            "score": st.column_config.NumberColumn("Score", format="%d", width="small"),
            "title": st.column_config.TextColumn("Job Title", width="medium"),
            "source": st.column_config.LinkColumn("Open Job Link", display_text="View Posting"),
            "pitch": st.column_config.TextColumn("Proposed Pitch", width="large"),
            "last_scanned": st.column_config.TextColumn("Last Scanned", width="medium")
        },
        hide_index=True,
        use_container_width=True,
        disabled=True # Keeps it as a clean view-only table with clickable links
    )

    # --- ACTION BUTTONS ---
    st.markdown("### ⚡ Quick Apply")
    for i, row in new_df.iterrows():
        with st.expander(f"Apply to: {row['title']} (Score: {row['score']})"):
            st.info(f"**AI Pitch:** {row['pitch']}")
            if st.button("✅ Mark as Applied", key=f"btn_{i}"):
                df.at[i, 'status'] = 'Applied'
                df.to_csv(CSV_FILE, index=False)
                st.rerun()
else:
    st.warning("No data found. Please trigger a scan.")
