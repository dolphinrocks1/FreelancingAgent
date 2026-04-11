import os
import sys
import pandas as pd
import feedparser
import json
import google.generativeai as genai
from datetime import datetime
import pytz

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
        
        # 1. Standardize naming if older columns exist
        if 'status' in df.columns and 'is_genuine' not in df.columns:
            df = df.rename(columns={'status': 'is_genuine'})
        if 'last_scanned' in df.columns and 'found_at' not in df.columns:
            df = df.rename(columns={'last_scanned': 'found_at'})
            
        # 2. Force injection of missing required columns to prevent KeyErrors
        for col in headers:
            if col not in df.columns:
                if col == 'is_genuine':
                    df[col] = "New"
                elif col == 'service':
                    df[col] = "General"
                else:
                    df[col] = ""
        
        return df
    except Exception:
        # If file is unreadable/corrupt, start fresh with headers
        return pd.DataFrame(columns=headers)

def get_ai_analysis(title, desc, service_type):
    """Uses Gemini to score and pitch the job."""
    prompt = f"""
    Act as a Senior Technical Lead for an Agency. 
    Category: {service_type}
    Job: {title}
    Description: {desc}

    Task:
    1. Score relevance (0-100). Focus on technical individual contributor work. 
    2. Write a 2-3 sentence 'pitch' starting with a professional hook. 
       Reference a specific tool (e.g., Wazuh, Sentinel, Splunk, Python).

    Return ONLY JSON:
    {{ "score": 85, "analysis": "fit explanation", "pitch": "tailored message" }}
    """
    try:
        response = model.generate_content(prompt)
        clean_text = response.text.strip().replace('```json', '').replace('```', '')
        result = json.loads(clean_text)
        
        # Keyword boost for Cybersecurity
        boost_keywords = ["sentinel", "wazuh", "soar", "siem", "splunk", "qradar"]
        if any(kw in title.lower() for kw in boost_keywords):
            result['score'] = min(100, result['score'] + 20)
        return result
    except:
        return {"score": 50, "analysis": "Fallback", "pitch": f"Expert {service_type} engineering for {title}."}

def main():
    # Use command line arg or default to Cyber Security
    service = sys.argv[1] if len(sys.argv) > 1 else "Cyber Security"
    print(f"🚀 Scanning for {service}...")
    
    # Load and repair data BEFORE starting search to prevent filter crashes
    existing_df = load_and_repair_csv()
    
    queries = {
        "Cyber Security": "SIEM+SOAR+Wazuh+Sentinel+Splunk",
        "AI Agent Builder": "LLM+LangChain+AutoGPT+OpenAI+Automation",
        "App Development": "Flutter+React+Native+iOS+Android",
        "Software Developer": "Python+Backend+FastAPI+Microservices"
    }
    
    query = queries.get(service, "Python+Developer")
    feed = feedparser.parse(f"https://www.upwork.com/ab/feed/jobs/rss?q={query}")
    new_found_leads = []
    
    # Process top 10 results
    for entry in feed.entries[:10]:
        # Duplicate check
        if not existing_df.empty and entry.link in existing_df['id'].values:
            continue

        analysis = get_ai_analysis(entry.title, entry.description, service)
        if analysis['score'] >= 40:
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

    # Combine data
    if new_found_leads:
        new_df = pd.DataFrame(new_found_leads)
        # We preserve ALL existing data (including Applied leads) and append new ones
        final_df = pd.concat([existing_df, new_df]).drop_duplicates(subset='id', keep='last')
        final_df.to_csv(CSV_FILE, index=False)
        print(f"✅ Successfully added {len(new_found_leads)} new leads.")
    else:
        print(f"⚠️ No high-relevance new leads found for {service} in this scan.")

if __name__ == "__main__":
    main()
