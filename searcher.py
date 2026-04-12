import os, sys, json
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from tavily import TavilyClient
import google.generativeai as genai
from datetime import datetime, timedelta

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
    status = Column(String, default="New")
    found_at = Column(DateTime, default=datetime.utcnow)

# Ensure engine doesn't crash if URL is missing during local testing
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("❌ ERROR: DATABASE_URL not found in environment.")
    sys.exit(1)

engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
ai_model = genai.GenerativeModel('gemini-1.5-flash')

def generate_pro_analysis(title, niche):
    # Requirement: Multi-paragraph winning pitch + strict niche validation
    prompt = f"""
    Act as a Technical Recruiter and Sales Expert for a {niche} consultant.
    Analyze the job: "{title}"
    
    1. VALIDATE: Is this job actually about {niche}? (e.g., SIEM, SOC, AI Agents). If it's unrelated (like Real Estate), set 'is_match' to false.
    2. EXTRACT: Client Name, Core Technical Requirements, Budget/Price, and Post Date.
    3. PITCH: Write a 3-paragraph winning pitch. 
       - Para 1: Hook the client by identifying their technical problem.
       - Para 2: Detail your specific solution using industry tools (Splunk, LangChain, etc).
       - Para 3: Professional call to action.

    Return ONLY JSON: {{"is_match": true, "score": 92, "details": "Company: ... | Budget: ...", "pitch": "..."}}
    """
    try:
        response = ai_model.generate_content(prompt)
        data = json.loads(response.text.replace('```json', '').replace('```', '').strip())
        return data
    except:
        return {"is_match": False}

def run_search(niche):
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    # Requirement #6: 48 hour limit
    query = f"site:upwork.com OR site:remoteok.com '{niche}' jobs posted last 48 hours"
    
    results = client.search(query=query, search_depth="advanced")
    session = Session()
    
    for res in results.get('results', []):
        url = res['url']
        # Requirement #5: Duplicacy check (Check New, Applied, and Purged)
        if not session.query(Job).filter_by(id=url).first():
            analysis = generate_pro_analysis(res['title'], niche)
            if analysis.get('is_match'):
                session.add(Job(
                    id=url, title=res['title'], details=analysis['details'],
                    score=analysis['score'], pitch=analysis['pitch'],
                    niche=niche, url=url
                ))
    
    session.commit()
    session.close()

if __name__ == "__main__":
    run_search(sys.argv[1] if len(sys.argv) > 1 else "Cyber Security")
