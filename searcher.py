import os
import time
import json
import pandas as pd
import google.generativeai as genai
from datetime import datetime, timedelta
from duckduckgo_search import DDGS

# --- CONFIGURATION ---
CSV_FILE = 'data/jobs.csv'
LAST_RUN_FILE = 'data/last_run.txt'
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def update_timestamp():
    """Adjusts UTC time to IST (UTC+5:30)."""
    os.makedirs('data', exist_ok=True)
    ist_time = datetime.now() + timedelta(hours=5, minutes=30)
    now_str = ist_time.strftime("%A, %b %d - %I:%M %p")
    with open(LAST_RUN_FILE, 'w') as f:
        f.write(now_str)
    print(f"🕒 Timestamp updated (IST): {now_str}")

def fetch_cyber_leads():
    """
    STRATEGY CHANGE: Search for the JOB TITLE directly. 
    Using 'site:' on freelance boards is often blocked by their robots.txt.
    """
    queries = [
        # Broad Cybersecurity & SIEM
        'remote "Cyber Security" freelance jobs 2026',
        'remote "SIEM" "SOAR" engineer contract jobs',
        'remote "Splunk" or "Sentinel" OR "Qradar" OR "XSOAR" OR "Automation" project',
        # Web & Software Development (High volume - guaranteed hits)
        'remote "React" "Node" developer freelance projects',
        'remote "Python" developer contract jobs'
    ]
    
    found_jobs = []
    MAX_RESULTS = 15
    
    with DDGS() as ddgs:
        for query in queries:
            try:
                # We search the whole web for these keywords + 'jobs' or 'projects'
                results = ddgs.text(query, max_results=15)
                for r in results:
                    # Look for links that look like job postings
                    link = r['href'].lower()
                    if any(x in link for x in ["job", "project", "view", "career", "work"]):
                        found_jobs.append({
                            "title": r['title'],
                            "source": r['href'],
                            "snippet": r['body']
                        })
                time.sleep(2) 
            except Exception as e:
                print(f"Search error: {e}")
                
    return found_jobs[:MAX_RESULTS]

def get_ai_analysis(title, snippet):
    """Refined prompt to handle both Cyber and Dev roles."""
    prompt = f"""
    Analyze this freelance job:
    Title: {title}
    Snippet: {snippet}

    1. Score (0-100): How relevant is this to a Senior SIEM/SOAR Engineer OR a Senior Fullstack Dev?
    2. Genuine: Is it a real project/role?
    3. Bid: Write a 3-sentence expert pitch.

    Return ONLY JSON: {{"score": 90, "is_genuine": true, "bid": "..."}}
    """
    try:
        response = model.generate_content(prompt)
        cleaned = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(cleaned)
    except:
        return {"score": 40, "is_genuine": True, "bid": "I am an expert in this field and ready to help."}

def process_and_save(raw_leads):
    os.makedirs('data', exist_ok=True)
    if not raw_leads:
        print("Empty crawl. Check search queries.")
        return

    # Load existing to avoid dupes
    existing_sources = []
    if os.path.exists(CSV_FILE):
        existing_sources = pd.read_csv(CSV_FILE)['source'].tolist()

    final_data = []
    for lead in raw_leads:
        if lead['source'] in existing_sources:
            continue
            
        print(f"Scoring: {lead['title'][:50]}...")
        analysis = get_ai_analysis(lead['title'], lead['snippet'])
        
        final_data.append({
            "title": lead['title'],
            "source": lead['source'],
            "weightage_score": analysis.get('score', 50),
            "is_genuine": analysis.get('is_genuine', True),
            "draft": analysis.get('bid', ""),
            "found_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        time.sleep(1)

    if final_data:
        new_df = pd.DataFrame(final_data)
        if os.path.exists(CSV_FILE):
            combined = pd.concat([pd.read_csv(CSV_FILE), new_df], ignore_index=True)
            combined.tail(50).to_csv(CSV_FILE, index=False)
        else:
            new_df.to_csv(CSV_FILE, index=False)
        print(f"✅ Saved {len(final_data)} leads.")

if __name__ == "__main__":
    try:
        leads = fetch_cyber_leads()
        process_and_save(leads)
    finally:
        update_timestamp()
