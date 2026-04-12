import streamlit as st
import pandas as pd
import os
import subprocess
import sys
from sqlalchemy import create_engine

# Database Connection
engine = create_engine(os.getenv("DATABASE_URL"))

st.set_page_config(page_title="Scout HQ Pro", page_icon="💼", layout="wide")

st.sidebar.header("Agent Controls")
niche = st.sidebar.selectbox("Target Niche", ["Cyber Security", "SOC", "AI Agent Builder", "Software Developer"])

if st.sidebar.button("🔍 Run Deep Scan"):
    with st.sidebar.status("Agent is searching the web..."):
        # Run our new searcher
        subprocess.run([sys.executable, "searcher.py", niche])
        st.rerun()

st.title("💼 Scout HQ: Lead Dashboard")

# Load data from Postgres into Pandas
query = f"SELECT * FROM jobs WHERE niche = '{niche}' AND status != 'Archived' ORDER BY score DESC"
df = pd.read_sql(query, engine)

if not df.empty:
    col1, col2 = st.columns(2)
    col1.metric("Leads Available", len(df))
    col2.metric("Top Matches", len(df[df['score'] >= 80]))

    # Display Leads
    for idx, row in df.iterrows():
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            c1.subheader(row['title'])
            c2.button(f"Apply ↗️", key=f"btn_{idx}", on_click=lambda u=row['url']: st.write(f"Opening {u}..."))
            
            st.write(f"**AI Pitch:** {row['pitch']}")
            st.caption(f"Score: {row['score']} | Found: {row['found_at']}")
            st.write(f"[View Job Posting]({row['url']})")
else:
    st.info(f"No leads found for {niche} yet. Click 'Run Deep Scan' to start.")
