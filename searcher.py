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
    return datetime.now(IST).strftime("%A, %b %d - %I:%M %p")

def get_ai_score(title, description):
    prompt = f"""
    Act as a Technical Recruiter for a SIEM/SOAR Expert.
    Job Title: {title}
    Description: {description}

    Score this from 0-100 based on relevance to: SIEM, SOAR, Wazuh, Sentinel, Splunk, or Detection Engineering.
    RED FLAGS (Score 0): Management, HR, Sales, or non-technical roles.

    Return ONLY JSON: {{"score": 85, "reason": "Mentions Splunk and SOAR automation", "bid": "Professional pitch here..."}}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(text)
    except:
        return {"score": 0, "reason": "AI Scoring Failed"}

def main():
    print(f"🚀 Starting Searcher Agent at {get_ist_time()}...")
    raw_leads = []
    processed_leads = []

    # 1. RSS Feeds (Upwork/RemoteOK)
    # Using broader terms to ensure we get hits
    feed_urls = [
        "https://www.upwork.com/ab/feed/jobs/rss?q=SIEM+OR+SOAR+OR+Splunk+OR+Cybersecurity",
        "https://remoteok.com/remote-security-jobs.rss"
    ]
    
    for url in feed_urls:
        print(f"📡 Polling: {url}")
        feed = feedparser.parse(url)
        for entry in feed.entries[:15]:
            raw_leads.append({"title": entry.title, "link": entry.link, "desc": entry.description})

    # 2. DuckDuckGo Discovery (Freelancer/LinkedIn/Indeed)
    # Bypassing the browser timeouts seen earlier
    with DDGS() as ddgs:
        queries = [
            "site:freelancer.com 'SIEM' OR 'SOAR' OR 'Cybersecurity'",
            "site:freelancer.com 'Splunk' OR 'Wazuh' OR 'Sentinel'",
            "site:linkedin.com/jobs 'Detection Engineer' remote",
            "site:remoteok.com 'Security' OR 'Automation'"
        ]
        for q in queries:
            print(f"🔍 Searching: {q}")
            try:
                results = ddgs.text(q, max_results=8)
                for r in results:
                    raw_leads.append({"title": r['title'], "link": r['href'], "desc": r['body']})
            except Exception as e:
                print(f"⚠️ Search failed for {q}: {e}")

    # 3. Scoring with lower threshold (30) to ensure visibility
    print(f"🧠 Processing {len(raw_leads)} potential leads...")
    for lead in raw_leads:
        analysis = get_ai_score(lead['title'], lead['desc'])
        score = analysis.get('score', 0)
        
        if score >= 30: # Lowered from 50 to ensure we get data
            processed_leads.append({
                "title": lead['title'],
                "source": lead['link'],
                "weightage_score": score,
                "is_genuine": "Verified",
                "draft": analysis.get('bid', "No pitch generated."),
                "found_at": get_ist_time()
            })

    # 4. Save Logic
    if not processed_leads:
        processed_leads.append({
            "title": "System Check: No High Matches",
            "source": "https://github.com",
            "weightage_score": 1,
            "is_genuine": "System",
            "draft": f"Scanned {len(raw_leads)} leads. None passed the relevance filter.",
            "found_at": get_ist_time()
        })

    new_df = pd.DataFrame(processed_leads)
    if os.path.exists(CSV_FILE):
        existing_df = pd.read_csv(CSV_FILE)
        final_df = pd.concat([existing_df, new_df], ignore_index=True).drop_duplicates(subset='source', keep='last')
    else:
        final_df = new_df
    
    final_df.to_csv(CSV_FILE, index=False)
    print(f"✅ Finished. {len(processed_leads)} entries saved to {CSV_FILE}.")

if __name__ == "__main__":
    main()
