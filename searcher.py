import os
import pandas as pd
import feedparser
import google.generativeai as genai
from datetime import datetime
import pytz
from duckduckgo_search import DDGS
import json

# --- CONFIGURATION ---
IST = pytz.timezone('Asia/Kolkata')
CSV_FILE = "data/jobs.csv"
os.makedirs("data", exist_ok=True)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def get_ist_time():
    return datetime.now(IST).strftime("%Y-%m-%d %I:%M %p")

def get_ai_score(title, description):
    """Refined technical scoring for SIEM/SOAR roles."""
    prompt = f"""
    Analyze this job for a Senior SIEM/SOAR/Detection Engineer.
    Title: {title}
    Details: {description}

    RULES:
    - 90-100: IC roles using Splunk, Sentinel, Wazuh, or SOAR automation.
    - 0: HR, Leadership, Management, or GTM roles.
    
    Return ONLY JSON: {{"score": 85, "reason": "...", "bid": "..."}}
    """
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text.strip().replace('```json', '').replace('```', ''))
    except:
        return {"score": 0}

def main():
    print(f"🚀 Starting Searcher Agent at {get_ist_time()}...")
    raw_leads = []
    processed_leads = []

    # 1. RSS Feeds (Upwork/RemoteOK) - 100% Reliable
    for url in ["https://www.upwork.com/ab/feed/jobs/rss?q=SIEM+OR+SOAR", "https://remoteok.com/remote-security-jobs.rss"]:
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]:
            raw_leads.append({"title": entry.title, "link": entry.link, "desc": entry.description})

    # 2. Search Discovery (LinkedIn/Freelancer/General) - Bypasses timeouts
    with DDGS() as ddgs:
        queries = [
            "site:freelancer.com 'SIEM' OR 'SOAR' OR 'Wazuh'",
            "site:linkedin.com/jobs 'Detection Engineer' OR 'Sentinel' remote"
        ]
        for q in queries:
            results = ddgs.text(q, max_results=5)
            for r in results:
                raw_leads.append({"title": r['title'], "link": r['href'], "desc": r['body']})

    # 3. Scoring
    for lead in raw_leads:
        analysis = get_ai_score(lead['title'], lead['desc'])
        if analysis.get('score', 0) >= 50:
            processed_leads.append({
                "title": lead['title'],
                "source": lead['link'],
                "weightage_score": analysis['score'],
                "is_genuine": "Verified",
                "draft": analysis.get('bid', "N/A"),
                "found_at": get_ist_time()
            })

    # 4. Save and Safety Valve
    if not processed_leads:
        processed_leads.append({
            "title": "System Check: Active",
            "source": "https://github.com",
            "weightage_score": 1,
            "is_genuine": "System",
            "draft": f"Scanned {len(raw_leads)} potential leads; none met threshold.",
            "found_at": get_ist_time()
        })

    df = pd.DataFrame(processed_leads)
    if os.path.exists(CSV_FILE):
        df = pd.concat([pd.read_csv(CSV_FILE), df], ignore_index=True).drop_duplicates(subset='source')
    df.to_csv(CSV_FILE, index=False)
    print(f"✅ Finished. {len(processed_leads)} entries saved.")

if __name__ == "__main__":
    main()
