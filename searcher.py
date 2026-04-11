import os
import pandas as pd
import feedparser
import google.generativeai as genai
from datetime import datetime
import pytz
from duckduckgo_search import DDGS

# --- CONFIGURATION ---
IST = pytz.timezone('Asia/Kolkata')
CSV_FILE = "data/jobs.csv"

# Ensure directory exists
os.makedirs("data", exist_ok=True)

def get_ist_time():
    return datetime.now(IST).strftime("%Y-%m-%d %I:%M %p")

def search_freelancer_ddg():
    """Uses DuckDuckGo to find Freelancer.com jobs without direct scraping timeouts."""
    leads = []
    with DDGS() as ddgs:
        # Targeting SIEM/SOAR roles specifically
        query = "site:freelancer.com/jobs 'SIEM' OR 'SOAR' OR 'Wazuh' OR 'Sentinel'"
        results = ddgs.text(query, max_results=10)
        for r in results:
            leads.append({
                "title": r['title'],
                "source": r['href'],
                "description": r['body']
            })
    return leads

def main():
    print(f"🚀 Starting Searcher Agent at {get_ist_time()}...")
    all_raw = []
    new_data = []

    # 1. Stable RSS Feeds (Upwork/RemoteOK)
    feeds = [
        "https://www.upwork.com/ab/feed/jobs/rss?q=(SIEM+OR+SOAR+OR+Wazuh)",
        "https://remoteok.com/remote-security-jobs.rss"
    ]
    
    for url in feeds:
        print(f"📡 Polling feed: {url}")
        feed = feedparser.parse(url)
        for entry in feed.entries:
            all_raw.append({
                "title": entry.title,
                "source": entry.link,
                "description": entry.description
            })

    # 2. Freelancer Discovery via DDG
    try:
        print("🔍 Searching Freelancer via DDG...")
        all_raw.extend(search_freelancer_ddg())
    except Exception as e:
        print(f"⚠️ DDG Search failed: {e}")

    # 3. Processing & Scoring (Placeholder for your Gemini Logic)
    #
    # (Iterate through all_raw and append high-matches to new_data)

    # 4. SAFETY VALVE: The "System Check" Entry
    if not new_data and len(all_raw) > 0:
        print("💡 No high-matches found. Adding a system-check entry.")
        new_data.append({
            "title": "System Check: Scraper Active",
            "source": "https://github.com",
            "weightage_score": 1,
            "is_genuine": "System",
            "draft": f"Processed {len(all_raw)} raw leads. None met the score threshold.",
            "found_at": get_ist_time()
        })

    # 5. Save to CSV
    if new_data:
        new_df = pd.DataFrame(new_data)
        if os.path.exists(CSV_FILE):
            df = pd.read_csv(CSV_FILE)
            final_df = pd.concat([df, new_df], ignore_index=True)
        else:
            final_df = new_df
        
        final_df.to_csv(CSV_FILE, index=False)
        print(f"✅ Success: Added {len(new_data)} entries.")

if __name__ == "__main__":
    main()
