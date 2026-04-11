import os
import time
import json
import pandas as pd
import google.generativeai as genai
import feedparser # NEW: For live feed processing
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
    """Directly hits live RSS feeds for instant updates."""
    # FEEDS: You can add more RSS URLs here as you find them
    feeds = [
        # Upwork: "Cyber Security" & "SIEM" feed (Example URL - see note below)
        "https://www.upwork.com/ab/feed/jobs/rss?q=cyber%20security,%20siem,%20qradar,%20splunk,%20soar",
        # We Work Remotely: Dev & Security roles
        "https://weworkremotely.com/categories/remote-dev-jobs.rss",
        # Remote OK: Security roles
        "https://remoteok.com/remote-security-jobs.rss"
    ]
    
    found_jobs = []
    for url in feeds:
        try:
            print(f"📡 Polling live feed: {url[:50]}...")
            feed = feedparser.parse(url)
            for entry in feed.entries:
                found_jobs.append({
                    "title": entry.title,
                    "source": entry.link,
                    "snippet": entry.description[:500] # Keep AI prompt manageable
                })
        except Exception as e:
            print(f"Feed error: {e}")
            
    return found_jobs

def get_ai_analysis(title, snippet):
    prompt = f"""
    Analyze this NEW job posting:
    Title: {title}
    Details: {snippet}
    
    Role: SIEM/SOAR/Detection Engineer or Senior Software Developer.
    Return ONLY JSON: {{"score": 95, "is_genuine": true, "bid": "Expert pitch..."}}
    """
    try:
        response = model.generate_content(prompt)
        cleaned = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(cleaned)
    except:
        return {"score": 60, "is_genuine": True, "bid": "I am an expert in this field."}

def process_and_save(raw_leads):
    os.makedirs('data', exist_ok=True)
    if not raw_leads:
        print("No live listings found in this cycle.")
        return

    existing_sources = []
    if os.path.exists(CSV_FILE):
        existing_sources = pd.read_csv(CSV_FILE)['source'].tolist()

    final_data = []
    for lead in raw_leads:
        if lead['source'] in existing_sources:
            continue
            
        analysis = get_ai_analysis(lead['title'], lead['snippet'])
        if analysis.get('score', 0) > 70: # Only keep high-quality leads
            final_data.append({
                "title": lead['title'],
                "source": lead['source'],
                "weightage_score": analysis['score'],
                "is_genuine": analysis['is_genuine'],
                "draft": analysis['bid'],
                "found_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            })

    if final_data:
        new_df = pd.DataFrame(final_data)
        if os.path.exists(CSV_FILE):
            combined = pd.concat([pd.read_csv(CSV_FILE), new_df], ignore_index=True)
            combined.tail(100).to_csv(CSV_FILE, index=False)
        else:
            new_df.to_csv(CSV_FILE, index=False)
        print(f"🚀 Found and saved {len(final_data)} high-quality live leads!")

if __name__ == "__main__":
    try:
        leads = fetch_live_leads()
        process_and_save(leads)
    finally:
        update_timestamp()
