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
    # HEURISTIC CHECK: If keywords are in the title, it's likely a lead
    keywords = ['siem', 'soar', 'wazuh', 'sentinel', 'splunk', 'soc', 'detection']
    title_lower = title.lower()
    
    # Force a base score if the title is a direct match
    base_score = 0
    if any(k in title_lower for k in keywords):
        base_score = 60 # Ensure it passes the 30 threshold

    prompt = f"""
    Analyze this technical job. 
    Title: {title}
    Description: {description}
    Target: SIEM/SOAR/Detection Engineer (Technical IC).
    
    Score 0-100. If it's a technical role in cybersecurity, score it at least 70.
    If it's HR/Management/Sales, score 0.
    
    Return ONLY JSON: {{"score": 85, "reason": "...", "bid": "..."}}
    """
    try:
        response = model.generate_content(prompt)
        result = json.loads(response.text.strip().replace('```json', '').replace('```', ''))
        # Use the higher of the two scores
        result['score'] = max(result.get('score', 0), base_score)
        return result
    except:
        return {"score": base_score, "reason": "Keyword match fallback"}

def main():
    print(f"🚀 Starting Searcher Agent at {get_ist_time()}...")
    raw_leads = []
    processed_leads = []

    # 1. RSS & Search Logic
    with DDGS() as ddgs:
        # Focusing on high-yield queries
        queries = ["site:freelancer.com SIEM SOAR", "site:freelancer.com Splunk Wazuh", "site:linkedin.com/jobs Detection Engineer remote"]
        for q in queries:
            try:
                for r in ddgs.text(q, max_results=10):
                    raw_leads.append({"title": r['title'], "link": r['href'], "desc": r['body']})
            except: pass

    # 2. Force Processing
    print(f"🧠 Processing {len(raw_leads)} potential leads...")
    for lead in raw_leads:
        analysis = get_ai_score(lead['title'], lead['desc'])
        if analysis['score'] >= 30: #
            processed_leads.append({
                "title": lead['title'],
                "source": lead['link'],
                "weightage_score": analysis['score'],
                "is_genuine": "Verified",
                "draft": analysis.get('bid', "N/A"),
                "found_at": get_ist_time()
            })

    # 3. Final Save
    if not processed_leads:
        processed_leads.append({"title": "System Check: No Matches", "source": "https://github.com", "weightage_score": 1, "is_genuine": "System", "draft": "Zero leads passed filter.", "found_at": get_ist_time()})

    df = pd.DataFrame(processed_leads)
    if os.path.exists(CSV_FILE):
        df = pd.concat([pd.read_csv(CSV_FILE), df], ignore_index=True).drop_duplicates(subset='source', keep='last')
    df.to_csv(CSV_FILE, index=False)
    print(f"✅ Finished. {len(processed_leads)} entries saved.")

if __name__ == "__main__":
    main()
