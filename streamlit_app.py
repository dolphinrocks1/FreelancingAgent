import os, sys, pandas as pd, feedparser, json, google.generativeai as genai
from datetime import datetime
import pytz

# Configuration
IST = pytz.timezone('Asia/Kolkata')
CSV_FILE = "data/jobs.csv"
os.makedirs("data", exist_ok=True)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def get_ai_analysis(title, desc, service_type):
    """Generates professional analysis and a high-conversion pitch"""
    prompt = f"""
    Act as a Senior Technical Lead for an Agency. 
    Category: {service_type}
    Job: {title}
    Description: {desc}

    Task:
    1. Score relevance (0-100). Focus on technical IC work. Penalize HR/Management/Leadership roles.
    2. Write a 3-sentence high-conversion 'hook'. Mention specific stack components like 
       Wazuh, Sentinel, Splunk, Python, or LLMs where relevant to {service_type}.
    
    Return ONLY JSON:
    {{"score": 85, "analysis": "Brief technical fit explanation", "pitch": "The pitch starting with 'Hi, I can help with...' "}}
    """
    try:
        response = model.generate_content(prompt)
        # Clean JSON markdown if present
        clean_text = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(clean_text)
    except Exception as e:
        print(f"AI Error: {e}")
        return {"score": 50, "analysis": "Automated match based on category keywords.", "pitch": "I am a senior developer/engineer ready to assist with your project."}

def main():
    # 1. Handle Inputs (Service Type)
    service = sys.argv[1] if len(sys.argv) > 1 else "Cyber Security"
    print(f"🚀 Scout Agent: Starting scan for {service}...")
    
    # 2. Define Niche Queries
    queries = {
        "Cyber Security": "SIEM+SOAR+Wazuh+Sentinel+Splunk",
        "AI Agent Builder": "LLM+LangChain+AutoGPT+OpenAI+Automation",
        "App Developer": "Flutter+React+Native+iOS+Android",
        "Software Developer": "Python+Backend+FastAPI+Microservices"
    }
    
    query = queries.get(service, "Python+Developer")
    url = f"https://www.upwork.com/ab/feed/jobs/rss?q={query}"
    
    # 3. Poll and Analyze
    feed = feedparser.parse(url)
    new_found_leads = []
    
    for entry in feed.entries[:15]:
        analysis = get_ai_analysis(entry.title, entry.description, service)
        if analysis['score'] >= 40: # Quality Threshold
            new_found_leads.append({
                "id": entry.link, 
                "title": entry.title,
                "source": entry.link,
                "score": analysis['score'],
                "service": service,
                "status": "New", 
                "pitch": analysis['pitch'],
                "analysis": analysis['analysis'],
                "found_at": datetime.now(IST).strftime("%Y-%m-%d %H:%M")
            })

    # 4. State Management (The "Pro" Logic)
    if os.path.exists(CSV_FILE):
        existing_df = pd.read_csv(CSV_FILE)
        
        # A. Protect the "Applied" Leads: Keep them regardless of current scan
        applied_leads = existing_df[existing_df['status'] == 'Applied']
        
        # B. Clean "New" Leads: Remove old 'New' leads for THIS service only
        # This prevents the 'New' tab from becoming an endless pile of old data.
        other_leads = existing_df[(existing_df['status'] != 'New') | (existing_df['service'] != service)]
        
        # C. Combine: Current Applied + Other Services + Current Scan Results
        final_df = pd.concat([other_leads, pd.DataFrame(new_found_leads)])
        # Use Link (id) as the source of truth to prevent duplicates
        final_df = final_df.drop_duplicates(subset='id', keep='last')
    else:
        final_df = pd.DataFrame(new_found_leads)

    # 5. Final Save
    final_df.to_csv(CSV_FILE, index=False)
    print(f"✅ Scan Complete. {len(new_found_leads)} fresh leads available in Tab 1.")

if __name__ == "__main__":
    main()
