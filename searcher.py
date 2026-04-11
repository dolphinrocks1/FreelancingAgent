import os
import time
import json
import pandas as pd
import google.generativeai as genai
from datetime import datetime
from duckduckgo_search import DDGS

# 1. Configuration & API Setup
CSV_FILE = 'data/jobs.csv'
LAST_RUN_FILE = 'data/last_run.txt'
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def update_timestamp():
    """Requirement: Ensures the UI shows the last time the agent was active."""
    os.makedirs('data', exist_ok=True)
    with open(LAST_RUN_FILE, 'w') as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print(f"🕒 Timestamp updated: {datetime.now().strftime('%H:%M:%S')}")

def get_ai_analysis(title, snippet):
    """Uses Gemini to score the job and draft a professional bid."""
    prompt = f"""
    Analyze this job for a Senior SIEM/SOAR Engineer:
    Title: {title}
    Description: {snippet}
    
    1. Score (0-100): How relevant is this to SIEM/SOAR/SOC specifically?
    2. Genuine: Is this a clear project (true) or just a company profile/spam (false)?
    3. Bid: Write a concise 3-sentence expert pitch focusing on 'Detection Engineering' and 'Automation'.
    
    Return ONLY JSON: {{"score": 85, "is_genuine": true, "bid": "..."}}
    """
    try:
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(cleaned_response)
    except Exception as e:
        print(f"AI Error: {e}")
        return {"score": 50, "is_genuine": True, "bid": "I am interested in this SIEM/SOAR role."}

def fetch_cyber_leads():
    """Finds a wider range of SOC/SIEM jobs across multiple platforms."""
    queries = [
        'site:upwork.com ("SIEM" OR "SOAR" OR "SOC" OR "Log Management") "Remote"',
        'site:upwork.com ("Splunk" OR "Sentinel" OR "Wazuh" OR "ELK") "Freelance"',
        'site:freelancer.com ("Cybersecurity" OR "Information Security") "Remote"',
        'site:guru.com ("Security Analyst" OR "Firewall" OR "Compliance")',
        'site:linkedin.com/jobs "SIEM" "Contract"',
        'site:simplyhired.com "Security Operations Center" "Remote"'
    ]
    
    found_jobs = []
    MAX_TOTAL_RESULTS = 15 # Requirement: Keep list populated
    
    with DDGS() as ddgs:
        for query in queries:
            if len(found_jobs) >= MAX_TOTAL_RESULTS:
                break
            try:
                # timelimit='w' (week) ensures results even on quiet days
                results = ddgs.text(query, timelimit='w', max_results=10)
                for r in results:
                    if any(x in r['href'].lower() for x in ["/jobs/", "/projects/", "/view/"]):
                        found_jobs.append({
                            "title": r['title'].split(" - ")[0],
                            "source": r['href'],
                            "snippet": r['body']
                        })
                time.sleep(5) 
            except Exception as e:
                print(f"Search Error on {query}: {e}")
                time.sleep(10) 
                
    return found_jobs[:MAX_TOTAL_RESULTS]

def process_and_save(raw_leads):
    os.makedirs('data', exist_ok=True)
    
    # 1. Handle "No Leads" scenario immediately so UI gets updated
    if not raw_leads:
        if not os.path.exists(CSV_FILE):
            pd.DataFrame(columns=["title", "source", "weightage_score", "is_genuine", "draft", "found_at"]).to_csv(CSV_FILE, index=False)
        print("No jobs found in this crawl.")
        return

    # 2. Duplicate Filtering
    if os.path.exists(CSV_FILE):
        existing_df = pd.read_csv(CSV_FILE)
        raw_leads = [l for l in raw_leads if l['source'] not in existing_df['source'].values]

    if not raw_leads:
        print("No new unique leads since last run.")
        return

    # 3. AI Scoring & Pitching
    final_data = []
    for lead in raw_leads:
        print(f"Analyzing: {lead['title']}")
        analysis = get_ai_analysis(lead['title'], lead['snippet'])
        
        final_data.append({
            "title": lead['title'],
            "source": lead['source'],
            "weightage_score": analysis.get('score', 50),
            "is_genuine": analysis.get('is_genuine', True),
            "draft": analysis.get('bid', ""),
            "found_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        time.sleep(1) # AI rate limiting

    # 4. Save to Disk
    new_df = pd.DataFrame(final_data)
    if os.path.exists(CSV_FILE):
        updated_df = pd.concat([pd.read_csv(CSV_FILE), new_df], ignore_index=True)
        # Optional: Keep only the most recent 50 leads to prevent file bloat
        updated_df.tail(50).to_csv(CSV_FILE, index=False)
    else:
        new_df.to_csv(CSV_FILE, index=False)
    
    print(f"✅ Successfully added {len(final_data)} new leads.")

if __name__ == "__main__":
    try:
        leads = fetch_cyber_leads()
        process_and_save(leads)
    finally:
        # This runs NO MATTER WHAT (success or crash)
        update_timestamp()
