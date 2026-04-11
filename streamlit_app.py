import streamlit as st
import pandas as pd
import os
import requests

# Page Config
st.set_page_config(page_title="SIEM/SOAR Scout", layout="wide")
CSV_FILE = "data/jobs.csv"

# --- REFRESH LOGIC ---
def trigger_github_action():
    # Replace with your actual GitHub Details
    OWNER = "dolphinrocks1" 
    REPO = "FreelancingAgent"
    WORKFLOW_ID = "agent_run.yml"
    TOKEN = st.secrets["GH_TOKEN"] # Add this to Streamlit Secrets
    
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/actions/workflows/{WORKFLOW_ID}/dispatches"
    headers = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json"}
    data = {"ref": "main"}
    
    response = requests.post(url, headers=headers, json=data)
    return response.status_code == 204

# --- UI COMPONENTS ---
with st.sidebar:
    st.header("🔄 Manual Sync")
    if st.button("🚀 Trigger New Scan"):
        if trigger_github_action():
            st.success("Action triggered! Check back in 2 minutes.")
        else:
            st.error("Failed to trigger. Check GH_TOKEN in Streamlit secrets.")

st.title("🛡️ SIEM/SOAR Scout")
df = pd.read_csv(CSV_FILE) if os.path.exists(CSV_FILE) else pd.DataFrame()

if not df.empty:
    st.info(f"🕒 Last data update: {df['found_at'].iloc[-1]}")
    # Display logic here...
else:
    st.warning("No leads found yet. Try triggering a manual scan above.")
