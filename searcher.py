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
    """Broadened search to ensure we don't return an empty crawl."""
    feeds = [
        # 1. Targeted SIEM/SOAR
        "https://www.upwork.com/ab/feed/jobs/rss?q=(SIEM+OR+SOAR+OR+Wazuh+OR+Sentinel+OR+Splunk+OR+QRadar)&sort=recency",
        # 2. Broad Technical Security (The 'Safety Net')
        "https://www.upwork.com/ab/feed/jobs/rss?q=(%22Cybersecurity+Engineer%22+OR+%22Detection+Engineer%22+OR+%22SOC+Automation%22)&sort=recency",
        "https://weworkremotely.com/categories/remote-security-jobs.rss",
        "https://remoteok.com/remote-security-jobs.rss"
    ]
    
    found_jobs = []
    for url in feeds:
        try:
            print(f"📡 Polling: {url[:50]}...")
            feed = feedparser.parse(url)
            for entry in feed.entries[:15]: # Increased to top 15
                found_jobs.append({
                    "title": entry.title,
                    "source": entry.link,
                    "snippet": entry.description[:1200] 
                })
        except Exception as e:
            print(f"Feed error: {e}")
            
    return found_jobs

def get_ai_analysis(title, snippet):
    """Balanced prompt: Rewards technical depth, punishes HR/Sales."""
    prompt = f"""
    Analyze this job:
    Title: {title}
    Details: {snippet}
    
    SCORING RULES:
    1. Base Score: 50.
    2. Bonus (+30): Specifically mentions Splunk, Wazuh, Sentinel, SOAR, or Playbooks.
    3. Penalty (-60): Title contains 'Recruiter', 'HR', 'Sourcing', 'Sales', or 'Manager'.
    
    Goal: Identify technical roles that involve security automation or monitoring.
    Output JSON only: {{"score": 75, "bid": "Expert pitch..."}}
    """
    try:
        response = model.generate_content(prompt)
        cleaned = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(cleaned)
    except:
        return {"score": 0, "bid": "N/A"}

def process_and_save(raw_leads):
    os.makedirs('data', exist_ok=True)
    if not os.path.exists(CSV_FILE):
        pd.DataFrame(columns=["title", "source", "weightage_score", "is_genuine", "draft", "found_at"]).to_csv(CSV_FILE, index=False)

    if not raw_leads:
        print("⚠️ No leads found in RSS. Check connection/URL.")
        return

    existing_df = pd.read_csv(CSV_FILE)
    existing_sources = existing_df['source'].tolist()

    final_data = []
    for lead in raw_leads:
        if lead['source'] in existing_sources:
            continue
            
        analysis = get_ai_analysis(lead['title'], lead['snippet'])
        
        # LOWER BAR: 50 is the new minimum to ensure the app isn't empty
        if analysis.get('score', 0) >= 50: 
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
        # Keep top 100, newest first
        combined.sort_values(by="found_at", ascending=False).head(100).to_csv(CSV_FILE, index=False)
        print(f"🚀 Success! Found {len(final_data)} leads.")
    else:
        print("Done. All found leads were below quality threshold.")

if __name__ == "__main__":
    try:
        leads = fetch_live_leads()
        process_and_save(leads)
    finally:
        update_timestamp()
