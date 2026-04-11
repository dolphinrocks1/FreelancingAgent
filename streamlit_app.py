import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="SIEM/SOAR Scout", layout="wide", page_icon="🛡️")

# CSS for Table Centering and custom Button styling
st.markdown("""
    <style>
    [data-testid="stTable"] td:nth-child(1), .stDataFrame td:nth-child(1) { 
        text-align: center !important; 
        font-weight: bold;
    }
    .stButton>button { width: 100%; }
    </style>
""", unsafe_allow_html=True)

CSV_FILE = "data/jobs.csv"

def load_and_fix_data():
    if not os.path.exists(CSV_FILE): return pd.DataFrame()
    df = pd.read_csv(CSV_FILE)
    # Map old columns to new UI logic
    if 'weightage_score' in df.columns:
        df = df.rename(columns={'weightage_score': 'score'})
    if 'draft' in df.columns:
        df = df.rename(columns={'draft': 'pitch'})
    
    # Ensure Score is an integer
    if 'score' in df.columns:
        df['score'] = pd.to_numeric(df['score'], errors='coerce').fillna(0).astype(int)
    
    # Default columns for consistency
    for col in ['status', 'service', 'last_scanned']:
        if col not in df.columns:
            df[col] = "New" if col == 'status' else ("Cyber Security" if col == 'service' else "N/A")
    return df

df = load_and_fix_data()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Scout HQ")
    service_choice = st.selectbox("Target Niche", 
                                ["Cyber Security", "AI Agent Builder", "App Developer", "Software Developer"])
    st.divider()
    st.metric("Total Leads", len(df))

# --- MAIN UI ---
st.title("Lead Discovery Dashboard")

if not df.empty:
    # Filter for active niche
    active_df = df[(df['status'] == 'New') & (df['service'] == service_choice)].copy()
    
    if not active_df.empty:
        st.subheader(f"🆕 New Leads for {service_choice}")
        
        # Interactive Table
        st.data_editor(
            active_df[['score', 'title', 'source', 'last_scanned']],
            column_config={
                "score": st.column_config.NumberColumn("Score", width="small", format="%d%%"),
                "source": st.column_config.LinkColumn("Listing", display_text="View Job"),
                "last_scanned": "Scanned At"
            },
            hide_index=True,
            use_container_width=True,
            disabled=True
        )

        st.divider()
        st.subheader("📝 Action Center")

        for i, row in active_df.iterrows():
            with st.expander(f"{row['score']}% - {row['title']}"):
                col_pitch, col_actions = st.columns([4, 1])
                
                with col_pitch:
                    # Native code block is safer than JS for some browsers
                    st.text_area("Proposed Pitch", row['pitch'], height=150, key=f"pitch_val_{i}")
                    st.info("💡 Copy the text above for your application.")

                with col_actions:
                    if st.button("✅ Applied", key=f"applied_{i}"):
                        df.at[i, 'status'] = 'Applied'
                        df.to_csv(CSV_FILE, index=False)
                        st.success("Updated!")
                        st.rerun()
                    st.link_button("🌐 Open Post", row['source'])
    else:
        st.info(f"No new leads found for {service_choice}.")
else:
    st.warning("No data found in data/jobs.csv.")
