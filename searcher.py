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
    """Initializes or repairs the CSV to ensure all columns exist for the UI."""
    headers = ['id', 'title', 'source', 'weightage_score', 'service', 'is_genuine', 'draft', 'found_at']
    
    if not os.path.exists(CSV_FILE):
        df = pd.DataFrame(columns=headers)
        df.to_csv(CSV_FILE, index=False)
        return df
    
    try:
        df = pd.read_csv(CSV_FILE)
        # Standardize naming for UI compatibility
        if 'status' in df.columns and 'is_genuine' not in df.columns:
            df = df.rename(columns={'status': 'is_genuine'})
        if 'last_scanned' in df.columns and 'found_at' not in df.columns:
            df = df.rename(columns={'last_scanned': 'found_at'})
            
        for col in headers:
            if col not in df.columns:
                df[col] = "New" if col == 'is_genuine' else ("General" if col == 'service' else "")
        return df
    except:
        return pd.DataFrame(columns=headers)

def get_ai_analysis(title, desc, service_type):
    """Uses Gemini to score and pitch the job."""
    prompt = f"""
    Act as a Senior Technical Lead. 
    Category: {service_type} | Job: {title} | Description: {desc}

    Task:
    1. Score relevance (0-100) for a technical individual contributor.
    2. Write a 2-sentence professional pitch referencing technical tools.

    Return ONLY JSON:
    {{ "score": 85, "analysis": "...", "pitch": "..." }}
    """
    try:
        response = model.generate_content(prompt)
        clean_text = response.text.strip().replace('```json', '').replace('```', '')
        result = json.loads(clean_text)
        
        # Priority keyword boost for Security roles
        security_keywords = ["sentinel", "wazuh", "soar", "siem", "splunk", "soc", "incident"]
        if any(kw in title.lower() for kw in security_keywords):
            result['score'] = min(100, result['score'] + 20)
        return result
    except:
        return {"score": 50, "analysis": "Fallback", "pitch": f"Technical support for {title}."}

def main():
    service = sys.argv[1] if len(sys.argv) > 1 else "SOC"
    print(f"🚀 Scanning for {service}...")
    
    existing_df = load_and_repair_csv()
    
    # Define Niche Categories
    queries = {
        "Cyber Security": '("SIEM" OR "SOAR" OR "Wazuh" OR "Sentinel" OR "Splunk" OR "XSOAR" OR "Automation")',
        "SOC": '("SOC Analyst" OR "SOC Engineer" OR "SOC" OR "Security Operation Center Architect" OR "SOC Architect")',
        "AI Agent Builder": '("LLM" OR "LangChain" OR "AI Agent" OR "AutoGPT")',
        "Software Developer": '("Python" OR "Backend" OR "FastAPI" OR "Microservices")'
    }
    
    # Build URL with safe encoding
    raw_query = queries.get(service, "Python")
    encoded_query = quote(raw_query)
    rss_url = f"https://www.upwork.com/ab/feed/jobs/rss?q={encoded_query}"
    
    print(f"📡 Requesting: {rss_url}")
    feed = feedparser.parse(rss_url)
    
    if hasattr(feed, 'bozo_exception') and feed.bozo_exception:
        # Note: 'not well-formed' is often a transient Upwork RSS error.
        print(f"⚠️ RSS Feed Note: {feed.bozo_exception}")

    new_found_leads = []
    
    for entry in feed.entries[:15]:
        # Check for duplicates using the link as a unique ID
        if not existing_df.empty and str(entry.link) in existing_df['id'].astype(str).values:
            continue

        analysis = get_ai_analysis(entry.title, entry.description, service)
        
        if analysis['score'] >= 35:
            new_found_leads.append({
                "id": entry.link, 
                "title": entry.title,
                "source": entry.link,
                "weightage_score": analysis['score'],
                "service": service,
                "is_genuine": "New", 
                "draft": analysis['pitch'],
                "found_at": datetime.now(IST).strftime("%A, %b %d - %I:%M %p")
            })

    if new_found_leads:
        new_df = pd.DataFrame(new_found_leads)
        final_df = pd.concat([existing_df, new_df]).drop_duplicates(subset='id', keep='last')
        final_df.to_csv(CSV_FILE, index=False)
        print(f"✅ Successfully added {len(new_found_leads)} new leads.")
    else:
        print(f"⚠️ No new leads passed the relevance filter for {service}.")

if __name__ == "__main__":
    main()
