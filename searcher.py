import os
import sys
import pandas as pd
import feedparser
from datetime import datetime
import pytz

# Configuration
IST = pytz.timezone('Asia/Kolkata')
CSV_FILE = "data/jobs.csv"

def load_and_repair_csv():
    headers = ['id', 'title', 'source', 'weightage_score', 'service', 'is_genuine', 'draft', 'found_at']
    if not os.path.exists(CSV_FILE):
        df = pd.DataFrame(columns=headers)
        os.makedirs("data", exist_ok=True)
        df.to_csv(CSV_FILE, index=False)
        return df
    return pd.read_csv(CSV_FILE)

def main():
    service = sys.argv[1] if len(sys.argv) > 1 else "Cyber Security"
    print(f"🚀 Deep-scanning for: {service}...")
    
    existing_df = load_and_repair_csv()
    
    # Platform Mapping: Use broader tags for Remote OK (no 'remote-' prefix)
    rok_tags = {"Cyber Security": "security", "SOC": "security", "AI Agent Builder": "ai", "Software Developer": "python"}
    
    # Keyword Mapping: Simple '+' only to avoid 'InvalidURL' control character errors
    kw_queries = {
        "Cyber Security": "Cyber+Security+Analyst+Engineer",
        "SOC": "SOC+Analyst+Security+Operations",
        "AI Agent Builder": "Python+Automation+LLM",
        "Software Developer": "Python+Backend"
    }
    
    tag = rok_tags.get(service, "security")
    query = kw_queries.get(service, "security")
    
    # Sources: Simplified to avoid RSS parser blocks
    sources = [
        f"https://remoteok.com/{tag}.rss", 
        f"https://www.upwork.com/ab/feed/jobs/rss?q={query}",
        f"https://www.freelancer.com/rss.xml?keyword={query}"
    ]

    new_found_leads = []
    for rss_url in sources:
        print(f"📡 Checking: {rss_url}")
        feed = feedparser.parse(rss_url)
        
        for entry in feed.entries[:10]:
            clean_link = str(entry.link).split('?')[0].strip()
            
            # Duplicate check
            if not existing_df.empty and clean_link in existing_df['id'].astype(str).values:
                continue

            # We accept all leads for now to verify the feed is working
            new_found_leads.append({
                "id": clean_link, 
                "title": entry.title,
                "source": clean_link,
                "weightage_score": 75, # Static score for testing feed connectivity
                "service": service,
                "is_genuine": "New", 
                "draft": "Interested in this role.",
                "found_at": datetime.now(IST).strftime("%b %d, %I:%M %p")
            })

    if new_found_leads:
        new_df = pd.DataFrame(new_found_leads)
        final_df = pd.concat([existing_df, new_df]).drop_duplicates(subset='id')
        final_df.to_csv(CSV_FILE, index=False)
        print(f"✅ Success: Added {len(new_found_leads)} leads.")
    else:
        print("⚠️ No new leads found. Try a broader search term.")

if __name__ == "__main__":
    main()
