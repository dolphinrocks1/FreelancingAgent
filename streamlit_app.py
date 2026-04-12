import streamlit as st
import pandas as pd
import os, subprocess, sys
from sqlalchemy import create_engine, text

engine = create_engine(os.getenv("DATABASE_URL"))

def update_status(job_id, status):
    with engine.connect() as conn:
        conn.execute(text("UPDATE jobs SET status = :s WHERE id = :id"), {"s": status, "id": job_id})
        conn.commit()

st.set_page_config(page_title="Freelancing Job Hunter", layout="wide")
st.title("🎯 Freelancing Job Hunter")

# Sidebar
niche = st.sidebar.selectbox("Service Type", ["Cyber Security", "AI in Cyber Security", "AI Agent Development", "Web Development", "Software Development"])
if st.sidebar.button("🚀 Sync Fresh Leads"):
    subprocess.run([sys.executable, "searcher.py", niche])
    st.rerun()

tab1, tab2 = st.tabs(["🆕 New Found Jobs", "✅ Applied Jobs"])

with tab1:
    query = f"SELECT * FROM jobs WHERE niche = '{niche}' AND status = 'New' ORDER BY score DESC"
    df = pd.read_sql(query, engine)
    
    if not df.empty:
        # We display as a clean table-like structure with specific columns
        for idx, row in df.iterrows():
            with st.container(border=True):
                # Layout for the "Table" Row
                col_title, col_score, col_found = st.columns([3, 1, 1])
                col_title.subheader(row['title'])
                col_score.metric("AI Match", f"{row['score']}%")
                col_found.write(f"**Found:** \n {row['found_at']}")
                
                # Expandable Deep Info
                with st.expander("📄 View Requirements, Source, and Professional Pitch"):
                    st.write("**Details (Company/Budget/Req):**")
                    st.info(row['details'])
                    st.write("**Professional AI Pitch:**")
                    st.success(row['pitch'])
                    st.write(f"**Source:** {row['url']}")
                
                # Requirement: Purge and Apply options
                btn_apply, btn_purge, btn_link = st.columns([1, 1, 1])
                btn_link.link_button("🔗 Open Job Posting", row['url'])
                if btn_apply.button("✅ Mark as Applied", key=f"a_{row['id']}"):
                    update_status(row['id'], "Applied")
                    st.rerun()
                if btn_purge.button("🗑️ Purge (Remove)", key=f"p_{row['id']}"):
                    update_status(row['id'], "Purged")
                    st.rerun()
    else:
        st.info("No new leads found.")

with tab2:
    # Tabular data for applied history
    df_app = pd.read_sql(f"SELECT title, score, found_at, url FROM jobs WHERE status='Applied' AND niche='{niche}'", engine)
    if not df_app.empty:
        st.dataframe(df_app, use_container_width=True)
    else:
        st.info("No applied history yet.")
