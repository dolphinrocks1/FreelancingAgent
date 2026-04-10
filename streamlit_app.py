import streamlit as st
import pandas as pd

# Page Config for Mobile Responsiveness
st.set_page_config(page_title="SIEM/SOAR Scout", layout="wide")

st.title("🛡️ Cyber Security Freelance Scout")
st.subheader("Real-time SIEM & SOAR Opportunities")

# --- MOCK DATA (This is where your Agent's JSON output will go) ---
data = [
    {
        "title": "Microsoft Sentinel Rule Logic Optimization",
        "tech": "Sentinel",
        "score": 92,
        "is_genuine": True,
        "location": "Remote",
        "source": "https://upwork.com/sample1",
        "draft": "I saw your request for Sentinel optimization. I specialize in KQL and reducing false positives..."
    },
    {
        "title": "Splunk Enterprise Security Deployment",
        "tech": "Splunk",
        "score": 78,
        "is_genuine": True,
        "location": "Remote (US Only)",
        "source": "https://linkedin.com/sample2",
        "draft": "With 5 years of Splunk ES experience, I can handle your deployment from indexing to dashboards."
    }
]

# --- SIDEBAR FILTERS ---
st.sidebar.header("Filters")
selected_tech = st.sidebar.multiselect("Security Stack", ["Splunk", "Sentinel", "QRadar", "XSOAR", "XSIAM"], default=["Splunk", "Sentinel"])

# --- MAIN DASHBOARD ---
for job in data:
    if job["tech"] in selected_tech:
        with st.container():
            # Header with Score Metric
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"### {job['title']}")
                st.caption(f"📍 {job['location']} | 🛠️ {job['tech']}")
            
            with col2:
                # Color coding the score
                color = "normal" if job["score"] > 80 else "off"
                st.metric("Weightage", f"{job['score']}%", delta_color=color)
            
            with col3:
                status = "✅ Genuine" if job["is_genuine"] else "⚠️ Review"
                st.write(f"**Status:** \n\n {status}")

            # Expandable Details
            with st.expander("View Details & AI Draft"):
                st.write("**Recommended Bid:**")
                st.info(job["draft"])
                st.link_button("View Original Post", job["source"])
            
            st.divider()
