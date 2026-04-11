import os
import sys
import pandas as pd
import feedparser
import json
import google.generativeai as genai
from datetime import datetime
import pytz
from urllib.parse import quote

# Configuration
IST = pytz.timezone('Asia/Kolkata')
CSV_FILE = "data/jobs.csv"
os.makedirs("data", exist_ok=True)

# API Setup
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def load_and_repair_csv():
    headers = ['id', 'title', 'source', 'weightage_score', 'service', 'is_genuine', 'draft', 'found_at']
    if not os.path.exists(CSV_FILE):
        df = pd.DataFrame(columns=headers)
        df.to_csv(CSV_FILE, index=False)
        return df
    try:
        df = pd.read_csv(CSV_FILE)
        # Ensure 'id' exists for duplicate checking
        if 'id' not in df.columns:
            df['id'] = ""
        return df
    except:
        return pd.DataFrame(columns=headers)

def get_ai_analysis(title, desc, service_type):
    prompt = f"""
    Act as a Senior Technical Lead. 
    Category: {service_type} | Job: {title} | Description: {desc}
    Task:
    1. Score relevance (0-100) for a technical individual contributor.
    2. Write a 2-sentence professional pitch referencing technical tools.
    Return ONLY JSON: {{ "score": 85, "analysis": "...", "pitch": "..." }}
    """
    try:
        response = model.generate_content(prompt)
        clean_text = response.text.strip().replace('```json', '').replace('```', '')
        result = json.loads(clean_text)
        security_keywords = ["sentinel", "wazuh", "soar", "siem", "splunk", "soc", "incident", "xsoar", "automation"]
        if any(kw in title.lower() for kw in security_keywords):
            result['score'] = min(100, result['score'] + 20)
        return result
    except:
        return {"score": 50, "analysis": "Fallback", "pitch": f"Expert support for {title}."}

def main():
    service = sys.argv[1] if len(sys.argv) > 1 else "Cyber Security"
    print(f"🚀 Multi-Platform Scan for {service}...")
    
    existing_df = load_and_repair_csv()
    
    # 1. Define keyword strings for each platform's URL format
    queries = {
        "Cyber Security": "SIEM+SOAR+Wazuh+Sentinel+Splunk+SOC+XSOAR+Automation+Playbook",
        "SOC": "SOC+Analyst+Engineer+Architect",
        "AI Agent Builder": "LLM+LangChain+Python+Automation",
        "Software Developer": "Python+Backend+FastAPI"
    }
    
    query = queries.get(service, "Python")
    
    # 2. Define multiple RSS Feed sources
    # Note: RemoteOK and Freelancer often use different path structures
    sources = [
        f"https://www.upwork.com/ab/feed/jobs/rss?q={query}",
        f"https://remoteok.com/remote-{query.replace('+', '-')}-jobs.rss",
        f"https://www.freelancer.com/rss.xml?keyword={query}"
    ]

    new_found_leads = []
    
    for rss_url in sources:
        print(f"📡 Requesting: {rss_url}")
        feed = feedparser.parse(rss_url)
        
        # Check if feed is valid
        if not feed.entries:
            print(f"⚠️ No entries found or feed unreachable at {rss_url.split('/')[2]}")
            continue

        for entry in feed.entries[:10]: # Check top 10 from each source
            # Link-based duplicate check
            if not existing_df.empty and str(entry.link) in existing_df['id'].astype(str).values:
                continue

            # Fallback for description if missing
            description = entry.get('description', entry.get('summary', 'No description available'))
            analysis = get_ai_analysis(entry.title, description, service)
            
            if analysis['score'] >= 35:
                new_found_leads.append({
                    "id": entry.link, 
                    "title": entry.title,
                    "source": entry.link,
                    "weightage_score": analysis['score'],
                    "service": service,
                    "is_genuine": "New", 
                    "draft": analysis['pitch'],
                    "found_at": datetime.now(IST).strftime("%a, %b %d - %I:%M %p")
                })

    if new_found_leads:
        new_df = pd.DataFrame(new_found_leads)
        # Combine and ensure we don't have duplicates in the same run
        final_df = pd.concat([existing_df, new_df]).drop_duplicates(subset='id', keep='last')
        final_df.to_csv(CSV_FILE, index=False)
        print(f"✅ Added {len(new_found_leads)} new leads from across platforms.")
    else:
        print(f"⚠️ No new leads passed the relevance filter in this multi-source scan.")

if __name__ == "__main__":
    main()
