import streamlit as st
import pandas as pd
import os
from streamlit_extras.stylable_container import stylable_container 

st.set_page_config(page_title="SIEM/SOAR Scout", layout="wide", page_icon="🛡️")

# 1. CSS for Table Centering & Clipboard UI
st.markdown("""
    <style>
    /* Center the Score Column */
    [data-testid="stTable"] td:nth-child(1), .stDataFrame td:nth-child(1) { 
        text-align: center !important; 
        font-weight: bold;
    }
    /* Style the Copy Button */
    .copy-btn {
        background-color: #2e7d32;
        color: white;
        border: none;
        padding: 4px 8px;
        border-radius: 4px;
        cursor: pointer;
    }
    </style>
""", unsafe_allow_html=True)

CSV_FILE = "data/jobs.csv"

def load_and_fix_data():
    if not os.path.exists(CSV_FILE): return pd.DataFrame()
    df = pd.read_csv(CSV_FILE)
    # Ensure Score is an integer to prevent the '0' bug
    if 'score' in df.columns:
        df['score'] = pd.to_numeric(df['score'], errors='coerce').fillna(0).astype(int)
    # Ensure Last Scanned exists
    if 'last_scanned' not in df.columns:
        df['last_scanned'] = "Not tracked"
    return df

df = load_and_fix_data()

# --- SIDEBAR & FILTERING ---
with st.sidebar:
    st.title("🛡️ Scout HQ")
    service_choice = st.selectbox("Target Niche", 
                                ["Cyber Security", "AI Agent Builder", "App Developer", "Software Developer"])
    st.divider()
    if st.button("🔄 Refresh Dashboard"):
        st.rerun()

# --- MAIN UI ---
st.title("Lead Discovery Dashboard")

if not df.empty:
    # Filter for active niche
    active_df = df[(df['status'] == 'New') & (df['service'] == service_choice)].copy()
    
    if not active_df.empty:
        # High-Level Table (Non-interactive for centering)
        st.subheader(f"🆕 New Leads for {service_choice}")
        
        # Display table with "Open Link" as a clickable column
        st.dataframe(
            active_df[['score', 'title', 'source', 'last_scanned']],
            column_config={
                "score": st.column_config.NumberColumn("Score", width="small", format="%d%%"),
                "source": st.column_config.LinkColumn("Listing", display_text="View Job"),
                "last_scanned": "Scanned At"
            },
            hide_index=True,
            use_container_width=True
        )

        st.divider()
        st.subheader("📝 Action Center (Copy Pitch & Apply)")

        # 2. The Interactive Action Cards
        for i, row in active_df.iterrows():
            with st.expander(f"{row['score']}% - {row['title']}"):
                col_pitch, col_actions = st.columns([4, 1])
                
                with col_pitch:
                    # The "Copy to Clipboard" Logic
                    pitch_text = row['pitch'].replace('"', '\\"') # Escape quotes for JS
                    st.code(row['pitch'], language=None)
                    
                    # Custom HTML Button for Clipboard
                    st.components.v1.html(f"""
                        <button class="copy-btn" onclick="navigator.clipboard.writeText('{pitch_text}')">
                            📋 Copy Pitch to Clipboard
                        </button>
                        <script>
                        // Visual feedback when clicked
                        document.querySelector('.copy-btn').onclick = function() {{
                            navigator.clipboard.writeText('{pitch_text}');
                            this.innerText = '✅ Copied!';
                            setTimeout(() => {{ this.innerText = '📋 Copy Pitch to Clipboard'; }}, 2000);
                        }};
                        </script>
                        <style>
                        .copy-btn {{
                            background-color: #0e1117; color: white; border: 1px solid #30363d;
                            padding: 8px 16px; border-radius: 8px; cursor: pointer; font-family: sans-serif;
                        }}
                        .copy-btn:hover {{ background-color: #161b22; border-color: #8b949e; }}
                        </style>
                    """, height=50)

                with col_actions:
                    if st.button("✅ Applied", key=f"applied_{i}", use_container_width=True):
                        df.at[i, 'status'] = 'Applied'
                        df.to_csv(CSV_FILE, index=False)
                        st.success("Moved to Applied!")
                        st.rerun()
                    st.link_button("🌐 View Post", row['source'], use_container_width=True)
    else:
        st.info(f"No new leads for {service_choice}. Try triggering a new scan.")
else:
    st.warning("No data found. Check your GitHub Action logs.")
