import streamlit as st
import pandas as pd
import os
import sys
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- Database Config ---
engine = create_engine(os.getenv("DATABASE_URL"))
Base = declarative_base()

class Job(Base):
    __tablename__ = 'jobs'
    id = Column(String, primary_key=True)
    title = Column(String)
    url = Column(String)
    score = Column(Integer)
    niche = Column(String)
    pitch = Column(Text)
    status = Column(String)
    found_at = Column(DateTime)

# --- Logic ---
def mark_as_applied(job_id):
    Session = sessionmaker(bind=engine)
    session = Session()
    session.query(Job).filter(Job.id == job_id).update({"status": "Applied"})
    session.commit()
    session.close()

# --- UI ---
st.set_page_config(page_title="Scout HQ Pro", layout="wide")
st.title("💼 Scout HQ: Lead Dashboard")

niche = st.sidebar.selectbox("Target Niche", ["Cyber Security", "SOC", "AI Agent Builder"])

# Tabs for organization
tab_new, tab_applied = st.tabs(["🆕 New Leads", "✅ Applied"])

with tab_new:
    query = f"SELECT * FROM jobs WHERE niche = '{niche}' AND status = 'New' ORDER BY score DESC"
    df_new = pd.read_sql(query, engine)
    
    if not df_new.empty:
        for _, row in df_new.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([5, 1])
                c1.subheader(row['title'])
                st.write(f"**AI Pitch:** {row['pitch']}")
                
                # Button triggers the callback and a rerun
                if c2.button("Apply", key=f"btn_{row['id']}"):
                    mark_as_applied(row['id'])
                    st.rerun()
    else:
        st.info("No new leads.")

with tab_applied:
    query_applied = f"SELECT * FROM jobs WHERE niche = '{niche}' AND status = 'Applied'"
    df_app = pd.read_sql(query_applied, engine)
    st.table(df_app[['title', 'found_at']])
