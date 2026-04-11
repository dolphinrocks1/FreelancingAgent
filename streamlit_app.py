import streamlit as st
import pandas as pd
import os

# Set Page Config
st.set_page_config(page_title="SIEM/SOAR Scout", layout="wide")

CSV_FILE = "data/jobs.csv"

def load_data():
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            if not df.empty:
                df['found_at'] = df['found_at'].astype(str)
                return df.sort_values(by="weightage_score", ascending=False)
        except Exception as e:
            st.error(f"Error reading CSV: {e}")
    return pd.DataFrame()

# --- ADMIN SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Admin Controls")
    st.info("Use these tools to manage the underlying data store.")
    
    if st.checkbox("Unlock Data Management"):
        st.warning("Action: Permanent Deletion")
        if st.button("🗑️ Clear All Jobs"):
            if os.path.exists(CSV_FILE):
                # Create an empty dataframe with the required columns
                empty_df = pd.DataFrame(columns=["title", "source", "weightage_score", "is_genuine", "draft", "found_at"])
                empty_df.to_csv(CSV_FILE, index=False)
                st.success("Database cleared! Refreshing...")
                st.rerun()
            else:
                st.error("No CSV file found to delete.")

# --- MAIN UI ---
st.title("🛡️ SIEM/SOAR Scout")
st.caption("Automated Freelance Lead Generation | Run Schedule: Every 3 Hours")

df = load_data()

if not df.empty:
    # Top Metrics
    total_leads = len(df[df['is_genuine'] != "System"])
    high_matches = len(df[df['weightage_score'] >= 80])
    
    col1, col2, col3 = st.columns([1, 1, 2])
    col1.metric("Total Leads", total_leads)
    col2.metric("High Match", high_matches)
    
    # Last run from the most recent entry
    last_run = df['found_at'].iloc[0]
    st.info(f"🕒 Last automated search completed: {last_run}")

    st.divider()

    # Lead Cards
    for _, row in df.iterrows():
        is_system = row['is_genuine'] == "System"
        icon = "⚪" if is_system else "🟢"
        
        with st.container():
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.subheader(f"{icon} {row['title']}")
                st.write(f"**Score:** {row['weightage_score']}% | **Source:** {row['source']}")
            with col_b:
                st.link_button("🔗 Open Posting", row['source'], use_container_width=True)

            with st.expander("🔍 View AI Analysis & Pitch"):
                st.code(row['draft'], language="text")
            st.divider()
else:
    st.info("📭 The dashboard is currently empty. The next automated run will populate it.")
