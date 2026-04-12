import streamlit as st
import pandas as pd
import os, subprocess, sys
from sqlalchemy import create_engine, text

# --- Database Setup ---
engine = create_engine(os.getenv("DATABASE_URL"))

def update_status(job_id, status):
    with engine.connect() as conn:
        conn.execute(text("UPDATE jobs SET status = :s WHERE id = :id"), {"s": status, "id": job_id})
        conn.commit()

# --- Page UI ---
st.set_page_config(page_title="Freelancing Job Hunter", page_icon="🎯", layout="wide")
st.title("🎯 Freelancing Job Hunter")

# Sidebar
st.sidebar.header("Agent Controls")
niche_options = [
    "Cyber Security", "AI in Cyber Security", 
    "AI Agent Development", "Web Development", "Software Development"
]
selected_niche = st.sidebar.selectbox("Select Service Type", niche_options)

if st.sidebar.button("🚀 Run Searcher Agent"):
    with st.sidebar.status("Hunting for jobs..."):
        subprocess.run([sys.executable, "searcher.py", selected_niche])
        st.rerun()

# Requirement #2: Two-tab system
tab_new, tab_applied = st.tabs(["🆕 New Found Jobs", "✅ Applied Jobs"])

with tab_new:
    query = f"SELECT * FROM jobs WHERE niche = '{selected_niche}' AND status = 'New' ORDER BY score DESC"
    df = pd.read_sql(query, engine)
    
    if not df.empty:
        for idx, row in df.iterrows():
            with st.container(border=True):
                col_info, col_score = st.columns([5, 1])
                with col_info:
                    st.subheader(row['title'])
                    st.write(f"**Found:** {row['found_at']}")
                with col_score:
                    st.metric("Match Score", f"{row['score']}%")
                
                # Detailed View
                with st.expander("🔍 View Details & Professional Pitch"):
                    st.write("**Details:**", row['details'])
                    st.divider()
                    st.write("**Professional AI Pitch:**")
                    st.info(row['pitch'])
                
                # Action Buttons
                b1, b2, b3 = st.columns([1, 1, 1])
                b1.link_button("🔗 Open Job Posting", row['url'])
                if b2.button("✅ Mark as Applied", key=f"app_{row['id']}"):
                    update_status(row['id'], "Applied")
                    st.rerun()
                if b3.button("🗑️ Purge (Never show again)", key=f"purg_{row['id']}"):
                    update_status(row['id'], "Purged")
                    st.rerun()
    else:
        st.info(f"No new {selected_niche} leads. Use the sidebar to scan.")

with tab_applied:
    # Requirement #1: Tabular format for applied jobs
    query_app = f"SELECT title, score, pitch, url, found_at, id FROM jobs WHERE status = 'Applied' AND niche = '{selected_niche}'"
    df_app = pd.read_sql(query_app, engine)
    
    if not df_app.empty:
        # Custom display for Applied jobs
        st.dataframe(
            df_app[['title', 'score', 'found_at', 'url']], 
            use_container_width=True,
            column_config={"url": st.column_config.LinkColumn("Job Link")}
        )
        
        # Requirement #3: Manual Purge Option
        if st.button("🔥 Clear All Applied History", type="primary"):
            with engine.connect() as conn:
                conn.execute(text(f"UPDATE jobs SET status = 'Purged' WHERE status = 'Applied' AND niche = '{selected_niche}'"))
                conn.commit()
            st.rerun()
    else:
        st.info("You haven't applied to any jobs in this niche yet.")
