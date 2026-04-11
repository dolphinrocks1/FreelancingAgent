import streamlit as st
import pandas as pd
import os

# Set Page Config
st.set_page_config(page_title="SIEM/SOAR Scout", layout="wide")

# Constants
CSV_FILE = "data/jobs.csv"

def load_data():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        # Ensure 'found_at' is treated as a string for display
        df['found_at'] = df['found_at'].astype(str)
        return df.sort_values(by="weightage_score", ascending=False)
    return pd.DataFrame()

# UI Header
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
    
    # Show last run time from the most recent entry
    last_run = df['found_at'].iloc[0]
    st.info(f"🕒 Last automated search completed: {last_run}")

    st.divider()

    # Lead Cards
    for _, row in df.iterrows():
        # Visual styling based on lead type
        is_system = row['is_genuine'] == "System"
        icon = "🔴" if is_system else "🟢"
        
        with st.container():
            col_a, col_b = st.columns([3, 1])
            
            with col_a:
                st.subheader(f"{icon} {row['title']}")
                st.write(f"**Relevance Score:** {row['weightage_score']}% | **Source:** {row['source']}")
            
            with col_b:
                # Always provide a clickable link, even for DDG results
                st.link_button("🔗 Open Original Posting", row['source'], use_container_width=True)

            with st.expander("🔍 View AI Analysis & Proposed Pitch"):
                st.markdown("### AI-Generated Pitch Draft")
                st.code(row['draft'], language="text")
            
            st.divider()
else:
    st.warning("No data found. Please run the Searcher Agent to populate the dashboard.")
