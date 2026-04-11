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
        
        # +20 boost for target high-value cybersecurity stack
        boost_keywords = ["sentinel", "wazuh", "soar", "siem", "splunk"]
        if any(kw in title.lower() for kw in boost_keywords):
            result['score'] = min(100, result['score'] + 20)
        return result
    except:
        return {"score": 50, "analysis": "Fallback", "pitch": f"Expert {service_type} support for {title}."}

def main():
    service = sys.argv[1] if len(sys.argv) > 1 else "Cyber Security"
    print(f"🚀 Freelancing Job Hunter: Scanning for {service}...")
    
    queries = {
        "Cyber Security": "SIEM+SOAR+Wazuh+Sentinel+Splunk",
        "AI Agent Builder": "LLM+LangChain+AutoGPT+OpenAI+Automation",
        "App Developer": "Flutter+React+Native+iOS+Android",
        "Software Developer": "Python+Backend+FastAPI+Microservices"
    }
    
    query = queries.get(service, "Python+Developer")
    feed = feedparser.parse(f"https://www.upwork.com/ab/feed/jobs/rss?q={query}")
    new_found_leads = []
    
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

    if os.path.exists(CSV_FILE):
        existing_df = pd.read_csv(CSV_FILE)
        other_leads = existing_df[(existing_df['status'] != 'New') | (existing_df['service'] != service)]
        final_df = pd.concat([other_leads, pd.DataFrame(new_found_leads)]).drop_duplicates(subset='id', keep='last')
    else:
        final_df = pd.DataFrame(new_found_leads)

    final_df.to_csv(CSV_FILE, index=False)
    print(f"✅ Scan Complete for {service}.")

if __name__ == "__main__":
    main()
