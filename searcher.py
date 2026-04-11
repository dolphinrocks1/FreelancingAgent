import os
import time
import pandas as pd
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
    """Heuristic + AI Scoring to ensure technical IC roles pass"""
    keywords = ['siem', 'soar', 'wazuh', 'sentinel', 'splunk', 'soc', 'detection', 'automation']
    title_lower = title.lower()
    base_score = 60 if any(k in title_lower for k in keywords) else 0

    prompt = f"Analyze: {title}. Desc: {description}. Score 0-100 for SIEM/SOAR/SOC technical role. Return ONLY JSON: {{\"score\": 85, \"reason\": \"...\", \"bid\": \"...\"}}"
    try:
        response = model.generate_content(prompt)
        result = json.loads(response.text.strip().replace('```json', '').replace('```', ''))
        result['score'] = max(result.get('score', 0), base_score)
        return result
    except:
        return {"score": base_score, "reason": "Keyword fallback"}

def fetch_results(queries, region="wt-wt"):
    """Performs the actual DDG search with rate-limit handling"""
    results_list = []
    with DDGS() as ddgs:
        for q in queries:
            try:
                print(f"🔍 Searching ({region}): {q}")
                for r in ddgs.text(q, max_results=10, region=region):
                    results_list.append({"title": r['title'], "link": r['href'], "desc": r['body']})
                time.sleep(1) # Polite delay
            except Exception as e:
                print(f"⚠️ Query failed: {e}")
    return results_list

def main():
    print(f"🚀 Starting Searcher Agent at {get_ist_time()}...")
    
    # 1. Primary Targeted Search
    primary_queries = [
        "site:freelancer.com SIEM SOAR", 
        "site:freelancer.com Splunk Wazuh",
        "site:linkedin.com/jobs 'Detection Engineer' remote"
    ]
    raw_leads = fetch_results(primary_queries)

    # 2. Safety Net: Broaden and Retry if 0 results
    if not raw_leads:
        print("Empty results. Activating Safety Net & Regional Retry...")
        time.sleep(5) # Wait 5s to bypass transient blocks
        safety_queries = [
            "site:freelancer.com 'SOC Analyst'",
            "site:freelancer.com 'Cybersecurity Automation'",
            "site:upwork.com 'SIEM' OR 'SOAR'"
        ]
        # Retry with US region to bypass local blocks
        raw_leads = fetch_results(safety_queries, region="us-en")

    # 3. Processing
    processed_leads = []
    print(f"🧠 Processing {len(raw_leads)} potential leads...")
    for lead in raw_leads:
        analysis = get_ai_score(lead['title'], lead['desc'])
        if analysis['score'] >= 30:
            processed_leads.append({
                "title": lead['title'],
                "source": lead['link'],
                "weightage_score": analysis['score'],
                "is_genuine": "Verified",
                "draft": analysis.get('bid', "N/A"),
                "found_at": get_ist_time()
            })

    # 4. Force Heartbeat (Visual Confirmation)
    if not processed_leads:
        processed_leads.append({
            "title": "System Check: Agent Active",
            "source": "https://github.com/dolphinrocks1",
            "weightage_score": 1,
            "is_genuine": "System",
            "draft": f"Scan completed at {get_ist_time()}. Scanned {len(raw_leads)} raw leads, 0 passed relevance.",
            "found_at": get_ist_time()
        })

    # 5. Save and Deduplicate
    new_df = pd.DataFrame(processed_leads)
    if os.path.exists(CSV_FILE):
        combined_df = pd.concat([pd.read_csv(CSV_FILE), new_df], ignore_index=True)
        final_df = combined_df.drop_duplicates(subset='source', keep='last')
    else:
        final_df = new_df
    
    final_df.to_csv(CSV_FILE, index=False)
    print(f"✅ Finished. {len(processed_leads)} entries saved.")

if __name__ == "__main__":
    main()
