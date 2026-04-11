import streamlit as st
import pandas as pd
import os

# Page Config
st.set_page_config(page_title="Agency Lead Manager", layout="wide", page_icon="🛡️")

CSV_FILE = "data/jobs.csv"

# 1. Helper to ensure data schema is correct (Fixes the KeyError)
def load_and_repair_data():
    if not os.path.exists(CSV_FILE):
        return pd.DataFrame()
    
    df = pd.read_csv(CSV_FILE)
    
    # Required columns for the new professional UI
    required_columns = {
        'status': 'New',
        'service': 'Cyber Security',
        'score': 0,
        'pitch': 'No pitch generated.',
        'analysis': 'No analysis available.',
        'id': 'N/A'
    }
    
    # Silently add missing columns to prevent UI crashes
    for col, default_val in required_columns.items():
        if col not in df.columns:
            df[col] = default_val
            
    return df

# --- SIDEBAR & ANALYTICS ---
with st.sidebar:
    st.title("🛡️ Scout HQ")
    service_choice = st.selectbox("Target Niche", 
                                ["Cyber Security", "AI Agent Builder", "App Developer", "Software Developer"])
    
    st.markdown("---")
    st.subheader("📊 Performance")
    
    df = load_and_repair_data()
    
    if not df.empty:
        st.metric("Total in Database", len(df))
        # This line no longer crashes because status is guaranteed to exist
        applied_count = len(df[df['status'] == 'Applied'])
        st.metric("Applied Leads", applied_count)
    else:
        st.write("Database is empty.")

# --- MAIN DASHBOARD ---
st.title("Lead Management Dashboard")

if not df.empty:
    tab1, tab2 = st.tabs(["🆕 New Found Details", "✅ Applied Leads"])

    with tab1:
        # Filter for the selected service and 'New' status
        new_df = df[(df['status'] == 'New') & (df['service'] == service_choice)]
        
        if not new_df.empty:
            # Tabular Summary for quick scanning
            st.dataframe(new_df[['title', 'score', 'found_at']].sort_values('score', ascending=False), 
                         use_container_width=True)
            
            st.markdown("### Action Center")
            for i, row in new_df.iterrows():
                with st.expander(f"📝 {row['title']} (Score: {row['score']})"):
                    st.write(f"**AI Analysis:** {row['analysis']}")
                    st.text_area("Proposed Pitch", row['pitch'], height=120, key=f"pitch_{i}")
                    
                    c1, c2 = st.columns(2)
                    if c1.button("✅ Mark as Applied", key=f"btn_app_{i}"):
                        df.at[i, 'status'] = 'Applied'
                        df.to_csv(CSV_FILE, index=False)
                        st.success("Moved to Applied Tab!")
                        st.rerun()
                    c2.link_button("🌐 Open Job Link", row['source'])
        else:
            st.info(f"No new leads found for {service_choice}. Run a scan to fetch fresh data.")

    with tab2:
        applied_df = df[df['status'] == 'Applied']
        if not applied_df.empty:
            st.dataframe(applied_df[['title', 'service', 'found_at']], use_container_width=True)
            
            for i, row in applied_df.iterrows():
                with st.container():
                    col_text, col_btn = st.columns([5, 1])
                    col_text.write(f"**{row['title']}**")
                    if col_btn.button("🗑️ Remove", key=f"del_{i}"):
                        df = df.drop(i)
                        df.to_csv(CSV_FILE, index=False)
                        st.rerun()
        else:
            st.info("Your applied list is currently empty.")
else:
    st.warning("No data found in data/jobs.csv. Run your searcher.py script first.")
