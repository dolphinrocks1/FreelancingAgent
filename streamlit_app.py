import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Agency Lead Manager", layout="wide")
CSV_FILE = "data/jobs.csv"

# --- SIDEBAR & ANALYTICS ---
with st.sidebar:
    st.title("🛡️ Scout HQ")
    service = st.selectbox("Target Niche", ["Cyber Security", "AI Agent Builder", "App Developer", "Software Developer"])
    
    if st.button("🔎 Scan for New Leads"):
        st.info(f"Triggering GitHub Action for {service}...")
        # Note: You need to pass the 'service' variable to your GH Action trigger

    st.markdown("---")
    st.subheader("📊 Performance")
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        st.metric("Total in Database", len(df))
        st.metric("Applied Leads", len(df[df['status'] == 'Applied']))

# --- MAIN DASHBOARD ---
st.title("Lead Management Dashboard")

if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
    tab1, tab2 = st.tabs(["🆕 New Found Details", "✅ Applied Leads"])

    with tab1:
        # Filter for the selected service and 'New' status
        new_df = df[(df['status'] == 'New') & (df['service'] == service)]
        
        if not new_df.empty:
            # Tabular Display
            st.dataframe(new_df[['title', 'score', 'found_at']], use_container_width=True)
            
            for i, row in new_df.iterrows():
                with st.expander(f"Action: {row['title']} (Score: {row['score']})"):
                    st.write(f"**AI Analysis:** {row['analysis']}")
                    st.text_area("Customized Pitch", row['pitch'], height=100, key=f"p_{i}")
                    
                    c1, c2 = st.columns(2)
                    if c1.button("Mark as Applied", key=f"app_{i}"):
                        df.at[i, 'status'] = 'Applied'
                        df.to_csv(CSV_FILE, index=False)
                        st.rerun()
                    c2.link_button("Open Job Link", row['source'])
        else:
            st.write("No new leads found for this niche yet.")

    with tab2:
        applied_df = df[df['status'] == 'Applied']
        if not applied_df.empty:
            for i, row in applied_df.iterrows():
                col_t, col_b = st.columns([4, 1])
                col_t.write(f"**{row['title']}** ({row['service']})")
                if col_b.button("🗑️ Remove", key=f"del_{i}"):
                    df = df.drop(i)
                    df.to_csv(CSV_FILE, index=False)
                    st.rerun()
            st.table(applied_df[['title', 'service', 'found_at']])
        else:
            st.info("No leads moved to 'Applied' status yet.")
else:
    st.warning("No data found. Please run a scan.")
