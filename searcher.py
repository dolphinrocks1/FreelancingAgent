import os
import time
import json
import pandas as pd
import google.generativeai as genai
import feedparser 
from datetime import datetime, timedelta

# --- CONFIGURATION ---
CSV_FILE = 'data/jobs.csv'
LAST_RUN_FILE = 'data/last_run.txt'
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def update_timestamp():
    os.makedirs('data', exist_ok=True)
    ist_time = datetime.now() + timedelta(hours=5, minutes=30)
    now_str = ist_time.strftime("%A, %b %d - %I:%M %p")
    with open(LAST_RUN_FILE, 'w') as f:
        f.write(now_str)

def fetch_live_leads():
    """Directly hits live RSS feeds for instant updates."""
    feeds = [
        # Upwork Niche Feed with specific tool keywords
        "https://www.upwork.com/ab/feed/jobs/rss?q=(SIEM+OR+SOAR+OR+QRadar+OR+Sentinel+OR+Splunk+OR+Wazuh+OR+XSOAR+OR+XSIAM+OR+%22Playbook+Developer%22)&sort=recency",
        
        # Security Specific Remote Feeds
        "https://weworkremotely.com/categories/remote-security-jobs.rss",
        "https://remoteok.com/remote-security-jobs.rss"
    ]
    
    found_jobs = []
    for url in feeds:
        try:
            print(f"📡 Polling live feed: {url[:50]}...")
            feed = feedparser.parse(url)
            for entry in feed.entries:
                found_jobs.append({
                    "title": entry.title,
                    "source": entry.link,
                    "snippet": entry.description[:700] # Increased slightly for better AI context
                })
        except Exception as e:
            print(f"Feed error: {e}")
            
    return found_jobs

def get_ai_analysis(title, snippet):
    """Generates niche-focused score and consultative bid proposal."""
    prompt = f"""
    Analyze this SIEM/SOAR job posting:
    Title: {title}
    Details: {snippet}
    
    1. Give a Relevance Score (0-100) based on these keywords: QRadar, Sentinel, Splunk, Wazuh, XSOAR, XSIAM, Playbook Automation.
    2. Write a Professional Bid Proposal using this structure:
       - HOOK: Acknowledge the specific technical pain point (e.g. migration, integration, playbook creation).
       - EXPERTISE: Mention specific experience in building automated playbooks and SOC integration.
       - SOLUTION: Suggest a high-level technical approach (e.g. custom decoders, workbook optimization).
       - CALL TO ACTION: Ask a technical discovery question to start the conversation.
    
    Output STRICTLY in JSON format: {{"score": 85, "bid": "Expert pitch text..."}}
    """
    try:
        response = model.generate_content(prompt)
        cleaned = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(cleaned)
    except:
        # Fallback with neutral score
        return {"score": 50, "bid": "I noticed you're looking for a SIEM/SOAR expert. I specialize in automation and detection engineering and would love to help optimize your environment."}

def process_and_save(raw_leads):
    os.makedirs('data', exist_ok=True)
    if not raw_leads:
        print("No live listings found in this cycle.")
        return

    existing_sources = []
    if os.path.exists(CSV_FILE):
        try:
            existing_sources = pd.read_csv(CSV_FILE)['source'].tolist()
        except:
            existing_sources = []

    final_data = []
    for lead in raw_leads:
        # Avoid duplicate analysis
        if lead['source'] in existing_sources:
            continue
            
        analysis = get_ai_analysis(lead['title'], lead['snippet'])
        
        # CRITICAL: Filter for high-quality niche leads (score >= 70)
        if analysis.get('score', 0) >= 70: 
            final_data.append({
                "title": lead['title'],
                "source": lead['source'],
                "weightage_score": analysis.get('score', 70),
                "is_genuine": True,
                "draft": analysis.get('bid', "Drafting pitch..."),
                "found_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            })

    if final_data:
        new_df = pd.DataFrame(final_data)
        if os.path.exists(CSV_FILE):
            existing_df = pd.read_csv(CSV_FILE)
            combined = pd.concat([existing_df, new_df], ignore_index=True)
            # Keep only the latest 100 leads to maintain performance
            combined.tail(100).to_csv(CSV_FILE, index=False)
        else:
            new_df.to_csv(CSV_FILE, index=False)
        print(f"🚀 Found and saved {len(final_data)} niche-specific live leads!")

if __name__ == "__main__":
    try:
        leads = fetch_live_leads()
        process_and_save(leads)
    finally:
        update_timestamp()
