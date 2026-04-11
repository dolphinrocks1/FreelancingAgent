import streamlit as st
import pandas as pd
import os
import streamlit.components.v1 as components

# --- PAGE CONFIG ---
st.set_page_config(page_title="SIEM/SOAR Scout", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM FUNCTIONS ---
def copy_button(text, index):
    """Creates a custom button that copies text to the clipboard using JS."""
    html_code = f"""
        <button onclick="navigator.clipboard.writeText(`{text}`)" 
                style="padding: 8px; border-radius: 5px; background-color: #007bff; color: white; border: none; cursor: pointer; width: 100%; font-weight: bold;">
            📋 Copy Bid to Clipboard
        </button>
    """
    components.html(html_code, height=45)

def get_metadata():
    """Reads the timestamp from the last_run.txt file."""
    file_path = 'data/last_run.txt'
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                return f.read().strip()
        except:
            return "Error reading timestamp"
    return "No record found"

@st.cache_data(ttl=600)
def load_data():
    """Loads the job data from CSV."""
    file_path = 'data/jobs.csv'
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            # Ensure required columns exist
            required_cols = ["title", "source", "weightage_score", "is_genuine", "draft"]
            for col in required_cols:
                if col not in df.columns:
                    df[col] = "N/A"
            return df.sort_values(by="weightage_score", ascending=False)
        except Exception as e:
            return pd.DataFrame()
    return pd.DataFrame()

# --- UI HEADER ---
st.title("🛡️ SIEM/SOAR Scout")
st.caption("Automated Freelance Lead Generation | Run Schedule: Every 3 Hours")

# --- 1. STATUS BAR (Always Visible) ---
last_run = get_metadata()
st.info(f"🕒 **Last automated search completed:** {last_run}")

# --- 2. DATA LOADING & STATS ---
df = load_data()

# Statistics Row (only show if data exists)
if not df.empty:
    col_a, col_b = st.columns(2)
    col_a.metric("Total Leads", len(df))
    col_b.metric("High Match (>80)", len(df[df['weightage_score'] >= 80] if 'weightage_score' in df.columns else []))
    st.divider()

# --- 3. MAIN FEED ---
if df.empty:
    st.warning("📡 No active leads found in the most recent crawl. The agent is currently scouting.")
    # Show an empty template so the UI structure remains consistent
    st.table(pd.DataFrame(columns=["Title", "Relevance Score", "Source"]))
    if st.button("Force Refresh Data"):
        st.cache_data.clear()
        st.rerun()
else:
    # JOB FEED
    for index, row in df.iterrows():
        score = row.get('weightage_score', 0)
        status_color = "🟢" if score >= 80 else "🟡" if score >= 50 else "🔴"
        
        with st.container():
            c1, c2 = st.columns([4, 1])
            with c1:
                st.subheader(f"{status_color} {row['title']}")
                st.write(f"**Relevance Score:** {score}%")
            with c2:
                if str(row['is_genuine']).lower() == 'true' or row['is_genuine'] == True:
                    st.success("Genuine")
                else:
                    st.warning("Review")

            with st.expander("View AI Analysis & Bid Draft"):
                st.write("**AI-Generated Bid:**")
                st.info(row['draft'])
                copy_button(row['draft'], index)
                st.link_button("🌐 Open Job Posting", row['source'])
            
            st.divider()

# --- SIDEBAR & SETTINGS ---
with st.sidebar:
    st.header("Settings")
    if st.button("Clear App Cache"):
        st.cache_data.clear()
        st.rerun()
    st.write("---")
    st.write(f"Agent Status: **Online**")
    st.caption(f"Last Scout: {last_run}")
