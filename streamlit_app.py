import streamlit as st
import pandas as pd
import os
import subprocess
import sys
from sqlalchemy import create_engine

# --- Database Config ---
# Ensure DATABASE_URL is set in your Streamlit Secrets
engine = create_engine(os.getenv("DATABASE_URL"))

st.set_page_config(page_title="Scout HQ Pro", page_icon="💼", layout="wide")

# --- Sidebar: Niche Selection ---
st.sidebar.header("Agent Controls")
# This dropdown drives the entire logic
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

if st.sidebar.button("🔍 Run Deep Scan"):
    with st.sidebar.status(f"Agent searching for {target_niche}..."):
        # CRITICAL: We pass target_niche as an argument to searcher.py
        result = subprocess.run(
            [sys.executable, "searcher.py", target_niche], 
            capture_output=True, 
            text=True
        )
        if result.returncode == 0:
            st.sidebar.success(f"Scan for {target_niche} complete!")
            st.rerun()
        else:
            st.sidebar.error("Searcher Failed")
            st.code(result.stderr)

# --- Main Dashboard ---
st.title(f"💼 Leads: {target_niche}")

# Load only the jobs matching the current selection
try:
    query = f"SELECT * FROM jobs WHERE niche = '{target_niche}' AND status != 'Applied' ORDER BY score DESC"
    df = pd.read_sql(query, engine)
except Exception:
    df = pd.DataFrame() # Handle case where table doesn't exist yet

if not df.empty:
    for idx, row in df.iterrows():
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            c1.subheader(row['title'])
            st.write(f"**Source:** {row['url']}")
            st.write(f"**AI Match Score:** {row['score']}%")
            st.write(f"**AI Pitch:** {row['pitch']}")
            
            if c2.button("Mark Applied", key=f"app_{idx}"):
                # Add your database update logic here (as discussed in previous step)
                pass
else:
    st.info(f"No leads found in the database for {target_niche}. Use the sidebar to scan.")
