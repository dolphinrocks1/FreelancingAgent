import streamlit as st
import pandas as pd
import os
import streamlit.components.v1 as components

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="SIEM/SOAR Scout", 
    layout="wide", 
    initial_sidebar_state="collapsed",
    page_icon="🛡️"
)

# --- CUSTOM FUNCTIONS ---
def copy_button(text, index):
    """Creates a custom button that copies text to the clipboard using JS."""
    # Using a unique ID per button to prevent conflicts
    html_code = f"""
        <button id="btn-{index}" onclick="navigator.clipboard.writeText(`{text}`)" 
                style="padding: 8px; border-radius: 5px; background-color: #007bff; color: white; border: none; cursor: pointer; width: 100%; font-weight: bold;">
            📋 Copy Bid to Clipboard
        </button>
    """
    components.html(html_code, height=45)

def get_metadata():
    """Reads the timestamp from the last_run.txt file for reliable status reporting."""
    file_path = 'data/last_run.txt'
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                content = f.read().strip()
                return content if content else "Timestamp file empty"
        except Exception:
            return "Error reading timestamp"
    return "Agent is warming up... first run pending."

@st.cache_data(ttl=600)
def load_data():
    """Loads the job data from CSV with fallback for missing columns."""
    file_path = 'data/jobs.csv'
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            if df.empty:
                return pd.DataFrame()
            
            # Ensure required columns exist to prevent UI crashes
            required_cols = ["title", "source", "weightage_score", "is_genuine", "draft"]
            for col in required_cols:
                if col not in df.columns:
                    df[col] = "N/A"
            
            # Numeric conversion for sorting
            df['weightage_score'] = pd.to_numeric(df['weightage_score'], errors='coerce').fillna(0)
            return df.sort_values(by="weightage_score", ascending=False)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

# --- UI HEADER ---
st.title("🛡️ SIEM/SOAR Scout")
st.caption("Automated Freelance Lead Generation | Run Schedule: Every 3 Hours")

# --- 1. STATUS BAR (The "last_run.txt" integration) ---
# This ensures users see the search status even if the CSV is empty
last_run = get_metadata()
if "warming up" in last_run.lower():
    st.warning(f"🕒 **Status:** {last_run}")
else:
    st.info(f"🕒 **Last automated search completed:** {last_run}")

# --- 2. DATA LOADING ---
df = load_data()

# Statistics Row (only show if data exists)
if not df.empty:
    col_a, col_b, col_c = st.columns([1, 1, 2])
    col_a.metric("Total Leads", len(df))
    # Count leads with score >= 80 safely
    high_match_count = len(df[df['weightage_score'] >= 80])
    col_b.metric("High Match", high_match_count)
    
    with col_c:
        if st.button("🔄 Force Refresh Data"):
            st.cache_data.clear()
            st.rerun()
    st.divider()

# --- 3. MAIN FEED ---
if df.empty:
    st.warning("📡 No active leads found in the most recent crawl. The agent is currently scouting.")
    
    # Visual placeholder for the table
    st.table(pd.DataFrame(columns=["Title", "Relevance Score", "Source"]))
    
    # Backup refresh button if metric row is hidden
    if st.button("Manual Cache Clear"):
        st.cache_data.clear()
        st.rerun()
else:
    # Render Job Cards
    for index, row in df.iterrows():
        score = int(row['weightage_score'])
        status_color = "🟢" if score >= 80 else "🟡" if score >= 50 else "🔴"
        
        with st.container():
            c1, c2 = st.columns([4, 1])
            with c1:
                st.subheader(f"{status_color} {row['title']}")
                st.write(f"**Relevance Score:** `{score}%` | **Source:** {row['source'].split('/')[2] if 'http' in str(row['source']) else 'Unknown'}")
            with c2:
                # Type-safe check for boolean column
                is_genuine = str(row['is_genuine']).lower() == 'true'
                if is_genuine:
                    st.success("Verified Lead")
                else:
                    st.warning("Needs Review")

            with st.expander("🔍 View AI Analysis & Proposed Pitch"):
                st.markdown("### AI-Generated Pitch Draft")
                st.info(row['draft'])
                
                # Action Buttons
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    copy_button(row['draft'], index)
                with btn_col2:
                    st.link_button("🌐 Open Original Posting", row['source'], use_container_width=True)
            
            st.divider()

# --- SIDEBAR ---
with st.sidebar:
    st.header("Agent Control")
    st.write(f"**Status:** Online ✅")
    st.write(f"**Last Sync:** {last_run}")
    
    if st.button("Clear App Cache"):
        st.cache_data.clear()
        st.rerun()
    
    st.divider()
    st.caption("v2.1.0 | SIEM/SOAR Scout Agent")
