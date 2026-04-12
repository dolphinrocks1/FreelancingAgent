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

engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
ai_model = genai.GenerativeModel('gemini-1.5-flash')

NICHE_MAP = {
    "Cyber Security": "SIEM OR SOAR OR Automation OR XSOAR OR Sentinel OR Splunk OR Qradar OR Wazuh OR 'SOC Analyst'",
    "AI in Cyber Security": "'AI Security Engineer' OR 'LLM Red Teaming' OR 'AI Compliance'",
    "AI Agent Development": "'AI Agent' OR 'Agentic AI' OR 'LangChain' OR 'CrewAI'",
    "Web Development": "FastAPI OR React OR 'Streamlit' OR 'Full Stack'",
    "Software Development": "Backend OR 'Python Developer' OR 'GoLang'"
}

def generate_pro_analysis(title, niche):
    prompt = f"""
    Act as a high-end Freelance Acquisition Expert. Analyze this job: '{title}' for the '{niche}' niche.
    1. EXTRACT: Company/Client Name (if visible), Core Requirements, Estimated Budget (if found), and Posting Date.
    2. SCORE: 0-100 based on niche relevance.
    3. PITCH: Write a winning 3-paragraph pitch. 
       - Para 1: Hook based on their specific technical pain.
       - Para 2: Value prop mentioning tools like SIEM, SOAR, or AI Agents.
       - Para 3: Professional CTA.
    Return ONLY JSON: {{"score": 95, "details": "Company: X | Req: Y | Budget: Z", "pitch": "FULL 3-PARA PITCH HERE"}}
    """
    try:
        response = ai_model.generate_content(prompt)
        return json.loads(response.text.replace('```json', '').replace('```', '').strip())
    except:
        return {"score": 80, "details": "Analysis Pending", "pitch": "Standard winning pitch for " + niche}

def run_search(niche):
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    keywords = NICHE_MAP.get(niche, niche)
    query = f"(site:upwork.com OR site:remoteok.com) ({keywords}) jobs posted last 48 hours"
    
    results = client.search(query=query, search_depth="advanced")
    session = Session()
    for res in results.get('results', []):
        if not session.query(Job).filter_by(id=res['url']).first():
            analysis = generate_pro_analysis(res['title'], niche)
            session.add(Job(
                id=res['url'], title=res['title'], details=analysis['details'],
                score=analysis['score'], pitch=analysis['pitch'],
                niche=niche, url=res['url']
            ))
    session.commit()
    session.close()

if __name__ == "__main__":
    run_search(sys.argv[1] if len(sys.argv) > 1 else "Cyber Security")
