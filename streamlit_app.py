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

niche = st.sidebar.selectbox("Service Type", ["Cyber Security", "AI in Cyber Security", "AI Agent Development", "Web Development", "Software Development"])
if st.sidebar.button("🚀 Sync Fresh Leads"):
    subprocess.run([sys.executable, "searcher.py", niche])
    st.rerun()

tab1, tab2 = st.tabs(["🆕 New Found Jobs", "✅ Applied Jobs"])

with tab1:
    df = pd.read_sql(f"SELECT * FROM jobs WHERE niche = '{niche}' AND status = 'New' ORDER BY score DESC", engine)
    if not df.empty:
        for idx, row in df.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.subheader(row['title'])
                c2.metric("AI Match", f"{row['score']}%")
                c3.write(f"**Found:** \n {row['found_at']}")
                
                with st.expander("🔍 View Requirements, Source, and Professional Pitch"):
                    st.write("**Details (Company/Budget/Req):**")
                    st.info(row['details'])
                    st.write("**Professional AI Pitch:**")
                    st.success(row['pitch'])
                    st.caption(f"Source: {row['url']}")

                b1, b2, b3 = st.columns([1, 1, 1])
                b1.link_button("🔗 Open Job Posting", row['url'])
                if b2.button("✅ Mark as Applied", key=f"a_{row['id']}"):
                    update_status(row['id'], "Applied"); st.rerun()
                if b3.button("🗑️ Purge (Remove)", key=f"p_{row['id']}"):
                    update_status(row['id'], "Purged"); st.rerun()
    else:
        st.info("No new leads found.")

with tab2:
    # Requirement #3: Table format with Purge option
    df_app = pd.read_sql(f"SELECT title, score, found_at, url, id FROM jobs WHERE niche='{niche}' AND status='Applied'", engine)
    if not df_app.empty:
        st.dataframe(df_app[['title', 'score', 'found_at', 'url']], use_container_width=True)
        
        col_del, _ = st.columns([1, 3])
        job_to_del = col_del.selectbox("Select job to remove from history:", df_app['title'])
        if col_del.button("🔥 Purge from Applied"):
            target_id = df_app[df_app['title'] == job_to_del]['id'].values[0]
            update_status(target_id, "Purged")
            st.rerun()
