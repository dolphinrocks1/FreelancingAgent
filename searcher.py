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
    """Generates professional analysis and forces a tailored pitch."""
    prompt = f"""
    Act as a Senior Technical Lead for an Agency. 
    Category: {service_type}
    Job: {title}
    Description: {desc}

    Task:
    1. Score relevance (0-100). Focus on technical individual contributor work. 
       Penalize HR/Management/Leadership roles heavily.
    2. Write a 2-3 sentence 'pitch' that starts with a professional hook. 
       Reference a specific tool or requirement from the description (e.g., Wazuh, Sentinel, Splunk, Python).
       Do NOT use generic placeholders like 'Keyword fallback'.

    Return ONLY JSON:
    {{
      "score": 85, 
      "analysis": "Brief technical fit explanation", 
      "pitch": "A highly tailored message for this specific client..."
    }}
    """
    try:
        response = model.generate_content(prompt)
        # Clean JSON markdown if present
        clean_text = response.text.strip().replace('```json', '').replace('```', '')
        result = json.loads(clean_text)
        
        # --- KEYWORD BOOST LOGIC ---
        # Add +20 boost for target high-value cybersecurity stack
        boost_keywords = ["sentinel", "wazuh", "soar", "siem", "splunk"]
        if any(kw in title.lower() for kw in boost_keywords):
            result['score'] = min(100, result['score'] + 20)
            
        return result
    except Exception as e:
        print(f"AI Error: {e}")
        # Dynamic fallback pitch based on job title instead of generic text
        return {
            "score": 50, 
            "analysis": "Automated fallback due to AI timeout.", 
            "pitch": f"I saw your posting for {title} and have extensive experience in {service_type} to assist immediately."
        }

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
                "weightage_score": analysis['score'], # Map to CSV expected name
                "service": service,
                "status": "New", 
                "draft": analysis['pitch'], # Map to CSV expected name
                "analysis": analysis['analysis'],
                "last_scanned": datetime.now(IST).strftime("%Y-%m-%d %I:%M %p") # UI format
            })

    # 4. State Management (The "Pro" Logic)
    if os.path.exists(CSV_FILE):
        existing_df = pd.read_csv(CSV_FILE)
        
        # A. Protect existing "Applied" Leads
        applied_leads = existing_df[existing_df['status'] == 'Applied']
        
        # B. Retain "New" leads from other services, but refresh current service
        other_leads = existing_df[(existing_df['status'] != 'New') | (existing_df['service'] != service)]
        
        # C. Combine: Current Applied + Other Services + Current Scan Results
        final_df = pd.concat([other_leads, pd.DataFrame(new_found_leads)])
        
        # D. Prevent Duplicates based on link
        final_df = final_df.drop_duplicates(subset='id', keep='last')
    else:
        final_df = pd.DataFrame(new_found_leads)

    # 5. Final Save
    final_df.to_csv(CSV_FILE, index=False)
    print(f"✅ Scan Complete. {len(new_found_leads)} fresh leads added to {CSV_FILE}.")

if __name__ == "__main__":
    main()
