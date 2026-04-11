import streamlit as st
import pandas as pd
import os
import streamlit.components.v1 as components

# --- PAGE CONFIG ---
st.set_page_config(page_title="SIEM/SOAR Scout", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM FUNCTIONS ---
def copy_button(text, index):
    """Creates a custom button that copies text to the clipboard using JS."""
    # We use the index to ensure each button on the page has a unique ID
    html_code = f"""
        <button onclick="navigator.clipboard.writeText(`{text}`)" 
                style="padding: 8px; border-radius: 5px; background-color: #007bff; color: white; border: none; cursor: pointer; width: 100%; font-weight: bold;">
            📋 Copy Bid to Clipboard
        </button>
    """
    components.html(html_code, height=45)

# 1. Force a fresh read of the CSV (Disabling long-term cache)
@st.cache_data(ttl=600)  # Re-checks the file every 10 minutes maximum
def load_data():
    file_path = 'data/jobs.csv'
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            # Ensure columns exist even if file is new
            required_cols = ["title", "source", "weightage_score", "is_genuine", "draft"]
            for col in required_cols:
                if col not in df.columns:
                    df[col] = "N/A"
            return df.sort_values(by="weightage_score", ascending=False)
        except Exception as e:
            st.error(f"Error reading data: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

# --- UI HEADER ---
st.title("🛡️ SIEM/SOAR Scout")
st.caption("Automated Freelance Lead Generation | Updated Hourly")

# --- DATA LOADING ---
df = load_data()

if df.empty:
    st.info("📡 The agent is currently scouting for new leads. Check back in a bit!")
    if st.button("Force Refresh"):
        st.cache_data.clear()
        st.rerun()
else:
    # Statistics Row
    col_a, col_b = st.columns(2)
    col_a.metric("Total Leads", len(df))
    col_b.metric("High Match (>80)", len(df[df['weightage_score'] >= 80]))

    st.divider()

    # --- JOB FEED ---
    for index, row in df.iterrows():
        # Color coding the score for visual priority
        score = row['weightage_score']
        status_color = "🟢" if score >= 80 else "🟡" if score >= 50 else "🔴"
        
        with st.container():
            c1, c2 = st.columns([4, 1])
            
            with c1:
                st.subheader(f"{status_color} {row['title']}")
                st.write(f"**Relevance Score:** {score}%")
            
            with c2:
                if row['is_genuine']:
                    st.success("Genuine")
                else:
                    st.warning("Review")

            # Expandable Details & Bid
            with st.expander("View AI Analysis & Bid Draft"):
                st.write("**AI-Generated Bid:**")
                st.info(row['draft'])
                
                # Copy Button logic
                copy_button(row['draft'], index)
                
                st.link_button("🌐 Open Job Posting", row['source'])
            
            st.divider()

# --- SIDEBAR & FOOTER ---
with st.sidebar:
    st.header("Settings")
    if st.button("Clear App Cache"):
        st.cache_data.clear()
        st.rerun()
    st.write("---")
    st.write("Agent Status: **Online**")

with st.sidebar:
    if os.path.exists('data/last_run.txt'):
        with open('data/last_run.txt', 'r') as f:
            last_run = f.read()
        st.caption(f"🕒 Last Scout: {last_run}")
    else:
        st.caption("🕒 Last Scout: Never")
