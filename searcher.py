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
    """Hits live RSS feeds and limits results to Top 10 per feed."""
    feeds = [
        "https://www.upwork.com/ab/feed/jobs/rss?q=(SIEM+OR+SOAR+OR+QRadar+OR+Sentinel+OR+Splunk+OR+Wazuh+OR+XSOAR+OR+XSIAM+OR+%22Playbook+Developer%22)&sort=recency",
        "https://weworkremotely.com/categories/remote-security-jobs.rss",
        "https://remoteok.com/remote-security-jobs.rss"
    ]
    
    found_jobs = []
    for url in feeds:
        try:
            print(f"📡 Polling feed: {url[:40]}...")
            feed = feedparser.parse(url)
            # LIMIT: Only take the first 10 entries from each feed
            for entry in feed.entries[:10]:
                found_jobs.append({
                    "title": entry.title,
                    "source": entry.link,
                    "snippet": entry.description[:800] 
                })
        except Exception as e:
            print(f"Feed error: {e}")
            
    return found_jobs

def get_ai_analysis(title, snippet):
    """Refined prompt to filter out Leadership/HR and focus on SIEM/SOAR."""
    prompt = f"""
    Analyze this technical job:
    Title: {title}
    Details: {snippet}
    
    CRITERIA:
    1. Score (0-100): High for technical SIEM/SOAR/Detection Engineering. 
    2. RED FLAG: If title contains 'HR', 'Leadership', 'GTM', 'Sourcing', or 'Compliance', score must be below 50.
    3. Bid Structure: Technical Hook -> Expertise (Wazuh/Sentinel/Splunk) -> Discovery Question.
    
    Output STRICTLY in JSON: {{"score": 75, "bid": "Expert pitch..."}}
    """
    try:
        response = model.generate_content(prompt)
        cleaned = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(cleaned)
    except:
        return {"score": 0, "bid": "N/A"}

def process_and_save(raw_leads):
    os.makedirs('data', exist_ok=True)
    
    # ENSURE FILE EXISTS: Create empty CSV if it doesn't exist to prevent Git errors
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
        
        # INCREASED BAR: Only save if score is 60+ to ensure quality
        if analysis.get('score', 0) >= 60: 
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
        combined.tail(100).to_csv(CSV_FILE, index=False)
        print(f"🚀 Saved {len(final_data)} high-quality leads.")

if __name__ == "__main__":
    try:
        leads = fetch_live_leads()
        process_and_save(leads)
    finally:
        update_timestamp()
