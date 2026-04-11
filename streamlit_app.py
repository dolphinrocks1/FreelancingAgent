import streamlit as st
import pandas as pd
import os

# Page Config
st.set_page_config(page_title="SIEM/SOAR Scout", page_icon="🛡️", layout="wide")

CSV_FILE = "data/jobs.csv"

# Sidebar for Manual Sync
with st.sidebar:
    st.title("🔄 Manual Sync")
    st.info("The agent runs automatically every 3 hours.")
    if st.button("🚀 Trigger New Scan"):
        st.warning("Ensure GH_TOKEN is set in Streamlit Secrets to use this.")

st.title("🛡️ SIEM/SOAR Scout")
st.markdown("---")

# Data Loading with Error Handling
if os.path.exists(CSV_FILE):
    try:
        df = pd.read_csv(CSV_FILE)
        
        # Clean up data: ensure weightage is numeric and drop empty rows
        df['weightage_score'] = pd.to_numeric(df['weightage_score'], errors='coerce').fillna(0)
        df = df.sort_values(by='weightage_score', ascending=False)

        # Dashboard Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Leads", len(df))
        col2.metric("High Match (60+)", len(df[df['weightage_score'] >= 60]))
        col3.write(f"🕒 **Last Update:** {df['found_at'].iloc[-1] if 'found_at' in df.columns else 'Unknown'}")

        # Display Loop
        for index, row in df.iterrows():
            # Skip the system heartbeat entries from the main view
            if row['is_genuine'] == "System":
                continue
                
            with st.container():
                st.subheader(f"📍 {row['title']}")
                c1, c2 = st.columns([1, 4])
                c1.progress(int(row['weightage_score']) / 100)
                c2.write(f"**Score:** {row['weightage_score']}% | **Source:** [View Posting]({row['source']})")
                
                with st.expander("🔍 View AI Analysis & Proposed Pitch"):
                    st.info(row['draft'])
                    st.button("📋 Copy Bid to Clipboard", key=f"btn_{index}")
                st.markdown("---")

    except Exception as e:
        st.error(f"Error loading UI: {e}")
        st.write("Raw Data Preview:", df if 'df' in locals() else "CSV could not be read.")
else:
    st.warning("Waiting for the first scan to complete. Check GitHub Actions for status.")
