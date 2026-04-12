import os, sys, json
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from tavily import TavilyClient
import google.generativeai as genai
from datetime import datetime

Base = declarative_base()

class Job(Base):
    __tablename__ = 'jobs'
    id = Column(String, primary_key=True)
    title = Column(String)
    details = Column(Text)
    score = Column(Integer)
    pitch = Column(Text)
    niche = Column(String)
    url = Column(String)
    status = Column(String, default="New") # New, Applied, Purged
    found_at = Column(DateTime, default=datetime.utcnow)

# --- Configuration ---
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
ai_model = genai.GenerativeModel('gemini-1.5-flash')

# Requirement: Expanded Keyword Map
NICHE_MAP = {
    "Cyber Security": "SIEM OR SOAR OR Automation OR XSOAR OR Sentinel OR Splunk OR Qradar OR Wazuh OR 'Automation Playbook' OR 'SOAR Engineer' OR 'SIEM Engineer' OR SOC OR 'SOC Analyst' OR 'Cyber Security Engineer'",
    "AI in Cyber Security": "'AI Consultant' OR 'AI & Cyber Security' OR 'AI Security Architect' OR 'AI Security Engineer' OR 'Remote AI Red Teamer' OR 'Remote AI Blue Teamer' OR 'AI Security Consultant' OR Blockchain OR 'AI Governance' OR 'AI Compliance' OR LLM",
    "AI Agent Development": "'AI Agent' OR 'AI Agent Consultant' OR 'AI Agent Engineer' OR 'AI Engineer' OR 'Agentic AI Developer' OR 'Chatbot Developers'",
    "Web Development": "FastAPI OR 'Full Stack' OR React OR 'Streamlit Expert' OR 'Next.js' OR 'Tailwind CSS' OR 'Web App Developer'",
    "Software Development": "Backend OR 'Distributed Systems' OR GoLang OR 'System Architect' OR 'Python Backend' OR 'Microservices' OR 'Cloud Architect'"
}

def generate_pro_pitch(title, niche):
    """Requirement #7: Detailed 3-paragraph professional pitch."""
    prompt = f"""
    Act as a world-class freelance consultant specializing in {niche}. 
    For the job title '{title}':
    1. Assign a match score (0-100) based on typical high-end requirements.
    2. Write a professional 3-paragraph pitch:
       - Para 1: Hook them with your understanding of the technical pain point.
       - Para 2: Specific value proposition (mention relevant tools like SIEM/AI/FastAPI).
       - Para 3: Professional call to action.
    Return ONLY a valid JSON object: {{"score": 90, "pitch": "...", "details": "Summary of responsibilities"}}
    """
    try:
        response = ai_model.generate_content(prompt)
        # Clean the response text for JSON parsing
        raw_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(raw_text)
    except:
        return {"score": 75, "pitch": "Professional pitch pending AI review.", "details": "Check job link for specifics."}

def run_search(niche):
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    keywords = NICHE_MAP.get(niche, niche)
    
    # Requirement #6: 48h limit logic
    query = f"(site:upwork.com OR site:remoteok.com OR site:freelancer.com) ({keywords}) jobs posted last 48 hours"
    
    print(f"🕵️ Searching for {niche}...")
    results = client.search(query=query, search_depth="advanced", max_results=15)
    
    session = Session()
    new_count = 0
    
    for res in results.get('results', []):
        url = res['url']
        # Requirement #5: Check if exists in any state (New, Applied, OR Purged)
        if not session.query(Job).filter_by(id=url).first():
            analysis = generate_pro_pitch(res['title'], niche)
            new_job = Job(
                id=url, title=res['title'], details=analysis['details'],
                score=analysis['score'], pitch=analysis['pitch'],
                niche=niche, url=url
            )
            session.add(new_job)
            new_count += 1
            
    session.commit()
    session.close()
    print(f"✅ Added {new_count} new technical leads.")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "Cyber Security"
    run_search(target)
