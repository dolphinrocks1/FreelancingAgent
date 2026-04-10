import os
import time
import json
import pandas as pd
import google.generativeai as genai
from datetime import datetime
from duckduckgo_search import DDGS

# 1. Configuration & API Setup
CSV_FILE = 'data/jobs.csv'
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def get_ai_analysis(title, snippet):
    """Uses Gemini to score the job and draft a professional bid."""
    prompt = f"""
    Analyze this freelance Cyber Security job:
    Title: {title}
    Description: {snippet}

    1. Score from 0-100 based on SIEM/SOAR relevance.
    2. Determine if it's a genuine job (true) or spam/vague (false).
    3. Write a 3-sentence high-impact bid as a Senior Security Engineer.

    Return ONLY a valid JSON object:
    {{"score": 85, "is_genuine": true, "bid": "..."}}
    """
    try:
        response = model.generate_content(prompt)
        # Clean the response to ensure valid JSON
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(cleaned_response)
    except Exception as e:
        print(f"AI Error: {e}")
        return {"score": 50, "is_genuine": True, "bid": "I am interested in this SIEM/SOAR role."}

def fetch_cyber_leads():
    """Finds a wider range of SOC/SIEM jobs across multiple platforms."""
    queries = [
        # Platform Specific Broad Search
        'site:upwork.com ("SIEM" OR "SOAR" OR "SOC") "Remote"',
        'site:freelancer.com ("Sentinel" OR "Splunk" OR "QRadar")',
        'site:guru.com ("Cyber Security" OR "Information Security")',
        
        # Skill-Based Niche Search
        'site:upwork.com "Splunk Engineer" OR "Splunk Admin"',
        'site:upwork.com "Microsoft Sentinel" OR "Azure Sentinel"',
        'site:upwork.com "Wazuh" OR "ELK Stack" OR "OpenSearch"',
        
        # Role-Based Search
        'site:upwork.com "Security Operations Center" OR "SOC Analyst"',
        'site:upwork.com "Detection Engineer" OR "Threat Hunting"',
        
        # International / Generic Freelance
        'site:peopleperhour.com "SIEM" OR "Security"',
        'site:remoteok.com "Security Engineer"'
    ]
    found_jobs = []
    
    with DDGS() as ddgs:
        for query in queries:
            try:
                results = ddgs.text(query, timelimit='d', max_results=5)
                for r in results:
                    if any(path in r['href'] for path in ["/jobs/", "/projects/"]):
                        found_jobs.append({
                            "title": r['title'].split(" - ")[0],
                            "source": r['href'],
                            "snippet": r['body']
                        })
                time.sleep(1) 
            except Exception as e:
                print(f"Search Error: {e}")
    return found_jobs

def process_and_save(raw_leads):
    # Ensure folder exists immediately
    os.makedirs('data', exist_ok=True)
    
    if not raw_leads:
        # Create an empty CSV with headers if it doesn't exist
        if not os.path.exists(CSV_FILE):
            pd.DataFrame(columns=["title", "source", "weightage_score", "is_genuine", "draft", "found_at"]).to_csv(CSV_FILE, index=False)
        print("No jobs found, but ensured CSV exists.")
        return

    os.makedirs('data', exist_ok=True)
    
    # Check for existing data to avoid duplicates
    if os.path.exists(CSV_FILE):
        existing_df = pd.read_csv(CSV_FILE)
        # Filter for only truly NEW URLs
        raw_leads = [l for l in raw_leads if l['source'] not in existing_df['source'].values]

    if not raw_leads:
        print("No new unique leads found.")
        return

    # Process new leads with AI
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
        time.sleep(1) # Rate limit AI calls

    # Append and Save
    new_df = pd.DataFrame(final_data)
    if os.path.exists(CSV_FILE):
        updated_df = pd.concat([pd.read_csv(CSV_FILE), new_df], ignore_index=True)
        updated_df.to_csv(CSV_FILE, index=False)
    else:
        new_df.to_csv(CSV_FILE, index=False)
    
    print(f"✅ Successfully added {len(final_data)} new AI-scored leads.")

if __name__ == "__main__":
    leads = fetch_cyber_leads()
    process_and_save(leads)
