import streamlit as st
import pandas as pd
import os
import subprocess
import sys
from sqlalchemy import create_engine

# --- Database Config ---
engine = create_engine(os.getenv("DATABASE_URL"))

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
        # Pass the selection to the searcher
        result = subprocess.run([sys.executable, "searcher.py", target_niche], capture_output=True, text=True)
        if result.returncode == 0:
            st.rerun()
        else:
            st.error("Scan Failed")
            st.code(result.stderr)

# Main Dashboard
st.title(f"💼 {target_niche} Opportunities")

try:
    # Filter strictly by the selected niche
    query = f"SELECT * FROM jobs WHERE niche = '{target_niche}' AND status = 'New' ORDER BY score DESC"
    df = pd.read_sql(query, engine)
except:
    df = pd.DataFrame()

if not df.empty:
    for idx, row in df.iterrows():
        with st.container(border=True):
            st.subheader(row['title'])
            st.write(f"**Found at:** {row['found_at']}")
            st.write(f"**Pitch:** {row['pitch']}")
            st.write(f"[Open Job Link]({row['url']})")
else:
    st.info(f"No active leads for {target_niche}. Initiate a scan to populate.")
