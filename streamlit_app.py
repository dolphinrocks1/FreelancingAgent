import streamlit as st
import pandas as pd
import os, subprocess, sys
from sqlalchemy import create_engine, text

# --- Database Connection ---
engine = create_engine(os.getenv("DATABASE_URL"))

def update_status(job_id, status):
    """Updates job status to 'Applied' or 'Purged'."""
    with engine.connect() as conn:
        conn.execute(
            text("UPDATE jobs SET status = :s WHERE id = :id"), 
            {"s": status, "id": job_id}
        )
        conn.commit()

# --- Page Config ---
st.set_page_config(page_title="Scout HQ | Job Hunter", layout="wide")
st.title("🎯 Scout HQ: Freelance Job Hunter")

# --- Sidebar Controls ---
st.sidebar.header("Agent Control")
niche = st.sidebar.selectbox(
    "Service Type", 
    ["Cyber Security", "AI in Cyber Security", "AI Agent Development", "Web Development", "Software Development"]
)

if st.sidebar.button("🚀 Sync Fresh Leads"):
    with st.sidebar.status("Hunting for leads..."):
        subprocess.run([sys.executable, "searcher.py", niche])
        st.rerun()

# --- Main Interface ---
tab1, tab2 = st.tabs(["🆕 New Found Jobs", "✅ Applied Jobs"])

with tab1:
    # Fetching enriched data (details, score, pitch)
    query = f"SELECT * FROM jobs WHERE niche = '{niche}' AND status = 'New' ORDER BY score DESC"
    df = pd.read_sql(query, engine)
    
    if not df.empty:
        for idx, row in df.iterrows():
            with st.container(border=True):
                # Header Row
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.subheader(row['title'])
                c2.metric("AI Match", f"{row['score']}%")
                c3.write(f"**Found (UTC):**\n{row['found_at'].strftime('%Y-%m-%d %H:%M')}")
                
                # Expandable Details & Multi-Paragraph Pitch
                with st.expander("🔍 View Requirements & Professional Winning Pitch"):
                    st.markdown("### 📋 Job Details")
                    st.info(row['details'])
                    
                    st.markdown("### ✍️ Winning AI Pitch")
                    # Rendering the pitch with success styling for visibility
                    st.success(row['pitch'])
                    
                    st.caption(f"**Source URL:** {row['url']}")

                # Action Buttons
                b1, b2, b3 = st.columns([1, 1, 1])
                b1.link_button("🔗 Open Job Posting", row['url'], use_container_width=True)
                
                if b2.button("✅ Mark as Applied", key=f"a_{row['id']}", use_container_width=True):
                    update_status(row['id'], "Applied")
                    st.rerun()
                    
                if b3.button("🗑️ Purge (Remove)", key=f"p_{row['id']}", use_container_width=True):
                    update_status(row['id'], "Purged")
                    st.rerun()
    else:
        st.info(f"No new leads found for {niche}. Click 'Sync Fresh Leads' to start.")

with tab2:
    # Requirement: Table format for Applied History
    df_app = pd.read_sql(
        f"SELECT title, score, found_at, url, id FROM jobs WHERE niche='{niche}' AND status='Applied' ORDER BY found_at DESC", 
        engine
    )
    
    if not df_app.empty:
        # Displaying history in a clean dataframe
        st.dataframe(
            df_app[['title', 'score', 'found_at', 'url']], 
            use_container_width=True,
            column_config={
                "url": st.column_config.LinkColumn("Job Posting"),
                "found_at": st.column_config.DatetimeColumn("Date Found")
            }
        )
        
        # Requirement: Purge option for Applied History
        st.markdown("---")
        col_del, _ = st.columns([1, 2])
        job_to_del = col_del.selectbox("Select job to remove from history:", df_app['title'])
        if col_del.button("🔥 Purge from Applied History", type="secondary"):
            target_id = df_app[df_app['title'] == job_to_del]['id'].values[0]
            update_status(target_id, "Purged")
            st.rerun()
    else:
        st.info("Your applied jobs list is currently empty.")
