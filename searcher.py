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
    """Initializes or repairs the CSV to ensure all columns exist."""
    # Define the official schema required by both the script and UI
    headers = ['id', 'title', 'source', 'weightage_score', 'service', 'status', 'draft', 'last_scanned']
    
    if not os.path.exists(CSV_FILE):
        df = pd.DataFrame(columns=headers)
        df.to_csv(CSV_FILE, index=False)
        return df
    
    try:
        df = pd.read_csv(CSV_FILE)
        # Ensure 'status' and 'service' exist to prevent GitHub Action crashes
        if 'status' not in df.columns:
            df['status'] = 'New'
        if 'service' not in df.columns:
            df['service'] = 'General'
        
        # Fill any missing data in required columns
        df['status'] = df['status'].fillna('New')
        df['service'] = df['service'].fillna('General')
        return df
    except Exception:
        return pd.DataFrame(columns=headers)

def get_ai_analysis(title, desc, service_type):
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
        
        # Boost for high-value cybersecurity stack
        boost_keywords = ["sentinel", "wazuh", "soar", "siem", "splunk", "qradar"]
        if any(kw in title.lower() for kw in boost_keywords):
            result['score'] = min(100, result['score'] + 20)
        return result
    except:
        return {"score": 50, "analysis": "Fallback", "pitch": f"Providing expert {service_type} engineering for {title}."}

def main():
    service = sys.argv[1] if len(sys.argv) > 1 else "Cyber Security"
    print(f"🚀 Freelancing Job Hunter: Scanning for {service}...")
    
    # Load and repair data BEFORE starting search
    existing_df = load_and_repair_csv()
    
    queries = {
        "Cyber Security": "SIEM+SOAR+Wazuh+Sentinel+Splunk",
        "AI Agent Builder": "LLM+LangChain+AutoGPT+OpenAI+Automation",
        "App Developer": "Flutter+React+Native+iOS+Android",
        "Software Developer": "Python+Backend+FastAPI+Microservices"
    }
    
    query = queries.get(service, "Python+Developer")
    feed = feedparser.parse(f"https://www.upwork.com/ab/feed/jobs/rss?q={query}")
    new_found_leads = []
    
    # Process top 15 results
    for entry in feed.entries[:15]:
        analysis = get_ai_analysis(entry.title, entry.description, service)
        if analysis['score'] >= 40:
            new_found_leads.append({
                "id": entry.link, 
                "title": entry.title,
                "source": entry.link,
                "weightage_score": analysis['score'],
                "service": service,
                "status": "New", 
                "draft": analysis['pitch'],
                "last_scanned": datetime.now(IST).strftime("%Y-%m-%d %I:%M %p")
            })

    # Filter out old leads for this specific niche to avoid duplicates
    # This logic now has guaranteed 'status' and 'service' columns
    status_col = 'is_genuine' if 'is_genuine' in existing_df.columns else 'status'
    other_leads = existing_df[existing_df[status_col] != 'New']
    ]
    
    if new_found_leads:
        new_df = pd.DataFrame(new_found_leads)
        final_df = pd.concat([other_leads, new_df]).drop_duplicates(subset='id', keep='last')
        final_df.to_csv(CSV_FILE, index=False)
        print(f"✅ Saved {len(new_found_leads)} leads for {service}.")
    else:
        print(f"⚠️ No high-relevance leads found for {service} in this scan.")

if __name__ == "__main__":
    main()
