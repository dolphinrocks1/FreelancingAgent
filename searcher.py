import os
import json
import pandas as pd
import google.generativeai as genai
import feedparser 
from datetime import datetime, timedelta

# --- CONFIGURATION ---
CSV_FILE = 'data/jobs.csv'
LAST_RUN_FILE = 'data/last_run.txt'
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def update_timestamp():
    os.makedirs('data', exist_ok=True)
    ist_time = datetime.now() + timedelta(hours=5, minutes=30)
    now_str = ist_time.strftime("%A, %b %d - %I:%M %p")
    with open(LAST_RUN_FILE, 'w') as f:
        f.write(now_str)

def fetch_live_leads():
    """Broader search queries to capture more technical SIEM/SOAR leads."""
    feeds = [
        # Expanded Upwork query to include SOC and Detection Engineering
        "https://www.upwork.com/ab/feed/jobs/rss?q=(SIEM+OR+SOAR+OR+QRadar+OR+Sentinel+OR+Splunk+OR+Wazuh+OR+XSOAR+OR+XSIAM+OR+%22Detection+Engineer%22+OR+%22SOC+Automation%22)&sort=recency",
        "https://weworkremotely.com/categories/remote-security-jobs.rss",
        "https://remoteok.com/remote-security-jobs.rss"
    ]
    
    found_jobs = []
    for url in feeds:
        try:
            print(f"📡 Polling feed: {url[:40]}...")
            feed = feedparser.parse(url)
            # LIMIT: Top 10 per feed for freshness
            for entry in feed.entries[:10]:
                found_jobs.append({
                    "title": entry.title,
                    "source": entry.link,
                    "snippet": entry.description[:1000] # Increased context for AI
                })
        except Exception as e:
            print(f"Feed error: {e}")
            
    return found_jobs

def get_ai_analysis(title, snippet):
    """Aggressive filtering for Technical SIEM/SOAR roles only."""
    prompt = f"""
    Analyze this job posting for a SIEM/SOAR Specialist:
    Title: {title}
    Details: {snippet}
    
    CRITERIA:
    1. Score (0-100): High ONLY for hands-on technical roles (Engineers, Developers, Architects).
    2. IMMEDIATE FAIL (Score < 20): If the job is for 'Recruiter', 'Sourcer', 'HR', 'GTM', 'Sales', or 'Compliance'.
    3. TARGET SKILLS: QRadar, Sentinel, Splunk, Wazuh, Playbook development, API integration.
    
    Output STRICTLY in JSON: {{"score": 85, "bid": "Technical pitch..."}}
    """
    try:
        response = model.generate_content(prompt)
        cleaned = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(cleaned)
    except:
        return {"score": 0, "bid": "N/A"}

def process_and_save(raw_leads):
    os.makedirs('data', exist_ok=True)
    
    # Self-healing file check
    if not os.path.exists(CSV_FILE):
        pd.DataFrame(columns=["title", "source", "weightage_score", "is_genuine", "draft", "found_at"]).to_csv(CSV_FILE, index=False)

    if not raw_leads:
        return

    existing_df = pd.read_csv(CSV_FILE)
    existing_sources = existing_df['source'].tolist()

    final_data = []
    for lead in raw_leads:
        if lead['source'] in existing_sources:
            continue
            
        analysis = get_ai_analysis(lead['title'], lead['snippet'])
        
        # QUALITY BAR: Back to 75 to eliminate "Sr Sourcer" and "HR" noise
        if analysis.get('score', 0) >= 75: 
            final_data.append({
                "title": lead['title'],
                "source": lead['source'],
                "weightage_score": analysis.get('score', 0),
                "is_genuine": True,
                "draft": analysis.get('bid', "Drafting..."),
                "found_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            })

    if final_data:
        new_df = pd.DataFrame(final_data)
        combined = pd.concat([existing_df, new_df], ignore_index=True)
        # Keep the best 100 historical leads
        combined.sort_values(by="weightage_score", ascending=False).head(100).to_csv(CSV_FILE, index=False)
        print(f"🚀 Success: {len(final_data)} technical leads found.")
    else:
        print("Done. No new high-quality technical leads found in this crawl.")

if __name__ == "__main__":
    try:
        leads = fetch_live_leads()
        process_and_save(leads)
    finally:
        update_timestamp()
