import streamlit as st
import pandas as pd
import os
import subprocess
import sys
from sqlalchemy import create_engine, text

# --- Database Setup ---
# Using os.getenv ensures your secrets from GitHub/Streamlit Cloud are loaded
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    st.error("DATABASE_URL not found. Please check your Secrets configuration.")
    st.stop()

engine = create_engine(DATABASE_URL)

# --- Functions ---
def update_job_status(job_id, new_status):
    """Directly updates the status in Postgres to avoid CSV corruption issues."""
    with engine.connect() as conn:
        query = text("UPDATE jobs SET status = :status WHERE id = :id")
        conn.execute(query, {"status": new_status, "id": job_id})
        conn.commit()

# --- Page Config ---
st.set_page_config(page_title="Scout HQ Pro", page_icon="💼", layout="wide")

# Sidebar: Service Type Selection
st.sidebar.header("Service Configuration")
target_niche = st.sidebar.selectbox(
    "Select Service Type", 
    [
        "Cyber Security", 
        "AI in Cyber Security", 
        "AI Agent Development", 
        "Web Development", 
        "Software Development"
    ]
)

if st.sidebar.button("🚀 Force Deep Scan"):
    with st.sidebar.status(f"Hunting for {target_niche} roles..."):
        # This passes your dropdown choice to the searcher script's NICHE_MAP
        result = subprocess.run([sys.executable, "searcher.py", target_niche], capture_output=True, text=True)
        if result.returncode == 0:
            st.rerun()
        else:
            st.error("Scan Failed")
            st.code(result.stderr)

# --- Main Dashboard ---
st.title(f"💼 {target_niche} Opportunities")

try:
    # Filter strictly by the selected niche and 'New' status
    query = f"SELECT * FROM jobs WHERE niche = '{target_niche}' AND status = 'New' ORDER BY score DESC"
    df = pd.read_sql(query, engine)
except Exception as e:
    st.error(f"Database connection error: {e}")
    df = pd.DataFrame()

# Layout metrics
if not df.empty:
    st.metric("New Leads Found", len(df))
    
    for idx, row in df.iterrows():
        with st.container(border=True):
            col_main, col_btn = st.columns([5, 1])
            
            with col_main:
                st.subheader(row['title'])
                st.write(f"**AI Match Score:** {row['score']}%")
                st.write(f"**AI Pitch:** {row['pitch']}")
                st.caption(f"Found on: {row['found_at']} | URL: {row['url']}")
                st.write(f"[Open Job Posting]({row['url']})")
            
            with col_btn:
                # Unique key prevents Streamlit button conflicts
                if st.button("Mark Applied", key=f"btn_{row['id']}"):
                    update_job_status(row['id'], "Applied")
                    st.toast(f"Updated: {row['title']}")
                    st.rerun()
else:
    st.info(f"No active leads for {target_niche}. Initiate a scan to populate the database.")
