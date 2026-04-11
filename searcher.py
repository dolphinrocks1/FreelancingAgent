import os
import sys
import pandas as pd
import feedparser
import json
import google.generativeai as genai
from datetime import datetime
import pytz

# Configuration
IST = pytz.timezone('Asia/Kolkata')
CSV_FILE = "data/jobs.csv"

def load_and_repair_csv():
    # Use 'status' to match your Streamlit UI's expectation (Image 12)
    headers = ['id', 'title', 'source', 'weightage_score', 'service', 'status', 'draft', 'found_at']
    if not os.path.exists(CSV_FILE):
        df = pd.DataFrame(columns=headers)
        df.to_csv(CSV_FILE, index=False)
        return df
    try:
        df = pd.read_csv(CSV_FILE)
        # Repair missing columns to prevent Streamlit KeyErrors
        for col in headers:
            if col not in df.columns:
                df[col] = "New" if col == 'status' else ""
        return df
    except:
        return pd.DataFrame(columns=headers)

def main():
    service = sys.argv[1] if len(sys.argv) > 1 else "Cyber Security"
    print(f"🚀 Scanning across platforms for: {service}...")
    
    existing_df = load_and_repair_csv()
    
    # Platform-specific tags (Removed 'remote' from slugs)
    rok_tags = {
        "Cyber Security": "security",
        "SOC": "security",
        "AI Agent Builder": "ai",
        "Software Developer": "python"
    }
    
    kw_queries = {
        "Cyber Security": "SIEM+SOAR+Wazuh+Sentinel+Splunk+SOC+Cyber",
        "SOC": "SOC+Analyst+Engineer+Architect",
        "AI Agent Builder": "LLM+LangChain+Python+Automation",
        "Software Developer": "Python+Backend+FastAPI"
    }
    
    tag = rok_tags.get(service, "security")
    query = kw_queries.get(service, "python")
    
    # Updated Sources: Removed 'remote-' prefix from RemoteOK
    sources = [
        f"https://remoteok.com/{tag}.rss", 
        f"https://www.upwork.com/ab/feed/jobs/rss?q={query}",
        f"https://www.freelancer.com/rss.xml?keyword={query}"
    ]

    new_found_leads = []
    
    for rss_url in sources:
        print(f"📡 Requesting: {rss_url}")
        feed = feedparser.parse(rss_url)
        
        if not feed.entries:
            continue

        for entry in feed.entries[:15]:
            # Link cleaning to avoid duplicates with trackers
            clean_link = str(entry.link).split('?')[0].strip()
            
            if not existing_df.empty and clean_link in existing_df['id'].astype(str).values:
                continue

            # Fallback for description as seen in RemoteOK XML (Image 14)
            desc = entry.get('description', entry.get('summary', ''))
            analysis = get_ai_analysis(entry.title, desc, service)
            
            if analysis['score'] >= 35:
                new_found_leads.append({
                    "id": clean_link, 
                    "title": entry.title,
                    "source": clean_link,
                    "weightage_score": analysis['score'],
                    "service": service,
                    "status": "New", # Matches Streamlit 'status' column
                    "draft": analysis['pitch'],
                    "found_at": datetime.now(IST).strftime("%a, %b %d - %I:%M %p")
                })

    if new_found_leads:
        new_df = pd.DataFrame(new_found_leads)
        final_df = pd.concat([existing_df, new_df]).drop_duplicates(subset='id', keep='last')
        final_df.to_csv(CSV_FILE, index=False)
        print(f"✅ Added {len(new_found_leads)} new leads.")
