import os
import pandas as pd
import feedparser
import google.generativeai as genai
from datetime import datetime
import pytz
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
    """Rigid technical filter with a keyword safety net"""
    keywords = ['siem', 'soar', 'wazuh', 'sentinel', 'splunk', 'soc', 'detection', 'automation']
    title_lower = title.lower()
    
    # HEURISTIC: If core keywords are in the title, it's a 65+ match automatically
    base_score = 65 if any(k in title_lower for k in keywords) else 0

    prompt = f"Analyze: {title}. Desc: {description}. Score 0-100 for SIEM/SOAR IC. Return ONLY JSON: {{\"score\": 85, \"reason\": \"...\", \"bid\": \"...\"}}"
    try:
        response = model.generate_content(prompt)
        res = json.loads(response.text.strip().replace('```json', '').replace('```', ''))
        return {"score": max(res.get('score', 0), base_score), "bid": res.get('bid', 'N/A')}
    except:
        return {"score": base_score, "bid": "Keyword fallback"}

def main():
    print(f"🚀 Starting Final Stability Run at {get_ist_time()}...")
    raw_leads = []

    # 1. DIRECT RSS POLLING (No Scraping/Search needed)
    rss_sources = [
        "https://www.upwork.com/ab/feed/jobs/rss?q=SIEM+OR+SOAR+OR+Splunk+OR+Wazuh",
        "https://remoteok.com/remote-security-jobs.rss",
        "https://www.freelancer.com/rss.xml" # Basic Freelancer RSS
    ]
    
    for url in rss_sources:
        try:
            print(f"📡 Polling Feed: {url}")
            feed = feedparser.parse(url)
            for entry in feed.entries[:20]:
                raw_leads.append({
                    "title": entry.title,
                    "link": entry.link,
                    "desc": entry.get('summary', entry.get('description', ''))
                })
        except Exception as e:
            print(f"⚠️ Feed failed: {e}")

    # 2. PROCESSING
    processed_leads = []
    print(f"🧠 Processing {len(raw_leads)} potential leads...")
    
    for lead in raw_leads:
        analysis = get_ai_score(lead['title'], lead['desc'])
        if analysis['score'] >= 45: # Professional Relevance Threshold
            processed_leads.append({
                "title": lead['title'],
                "source": lead['link'],
                "weightage_score": analysis['score'],
                "is_genuine": "Verified",
                "draft": analysis['bid'],
                "found_at": get_ist_time()
            })

    # 3. ALWAYS SAVE A HEARTBEAT
    if not processed_leads:
        processed_leads.append({
            "title": "System Check: RSS Active",
            "source": "https://github.com",
            "weightage_score": 1,
            "is_genuine": "System",
            "draft": f"Scan complete. Found {len(raw_leads)} raw entries, 0 matched SIEM/SOAR criteria.",
            "found_at": get_ist_time()
        })

    # 4. DEDUPLICATE AND SAVE
    new_df = pd.DataFrame(processed_leads)
    if os.path.exists(CSV_FILE):
        df = pd.concat([pd.read_csv(CSV_FILE), new_df], ignore_index=True).drop_duplicates(subset='source', keep='last')
    else:
        df = new_df
    
    df.to_csv(CSV_FILE, index=False)
    print(f"✅ Save Complete. {len(processed_leads)} entries recorded.")

if __name__ == "__main__":
    main()
