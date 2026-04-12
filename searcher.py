import os, sys, json
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from tavily import TavilyClient
import google.generativeai as genai
from datetime import datetime

# 1. Database Schema
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

# 2. Environment & Database Setup
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("❌ ERROR: DATABASE_URL not found in environment.")
    sys.exit(1)

engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

# 3. AI Engine Configuration
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
ai_model = genai.GenerativeModel('gemini-1.5-flash')

# 4. Niche-to-Keyword Mapping
NICHE_MAP = {
    "Cyber Security": "(site:upwork.com OR site:remoteok.com) 'Cyber Security' (SIEM OR SOC OR Sentinel OR Splunk OR 'Incident Response')",
    "AI in Cyber Security": "(site:upwork.com OR site:wellfound.com) 'AI' ('Cyber Security' OR 'Red Teaming' OR 'LLM Security')",
    "AI Agent Development": "(site:upwork.com OR site:ycombinator.com/jobs) ('AI Agent' OR 'LangChain' OR 'CrewAI' OR 'Agentic')",
    "Web Development": "(site:upwork.com OR site:remoteok.com) ('FastAPI' OR 'React' OR 'Streamlit' OR 'Next.js')",
    "Software Development": "(site:upwork.com OR site:github.com) ('Python Backend' OR 'GoLang' OR 'Microservices' OR 'Rust')"
}

def generate_pro_analysis(title, content, niche):
    """Passes both title and description to Gemini for extraction."""
    prompt = f"""
    Act as a Technical Sales Expert for a {niche} consultant. 
    Analyze this job posting:
    Title: {title}
    Description/Snippet: {content}
    
    1. VALIDATE: Does this job specifically require technical skills in {niche}? If it's unrelated (e.g., real estate, admin), set 'is_match' to false.
    2. EXTRACT: Find the Client/Company, Core Requirements, Budget/Price, and Date.
    3. PITCH: Write a winning 3-paragraph pitch. 
       - Para 1: Hook the client by identifying the technical pain point.
       - Para 2: Detail a solution using tools like Splunk, LangChain, or specific SOC frameworks.
       - Para 3: Professional call to action.

    Return ONLY JSON: 
    {{
      "is_match": true, 
      "score": 90, 
      "details": "Company: [Name] | Requirements: [List] | Budget: [Amount]", 
      "pitch": "Full 3-paragraph pitch here"
    }}
    """
    try:
        response = ai_model.generate_content(prompt)
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"⚠️ AI skipped {title[:30]}... Reason: {e}")
        return {"is_match": False}

def run_search(niche):
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    
    # Use the NICHE_MAP to get professional keywords
    search_query = NICHE_MAP.get(niche, niche)
    final_query = f"{search_query} jobs posted this week"
    
    print(f"🕵️ Searching for {niche} using high-intent keywords...")
    results = client.search(query=final_query, search_depth="advanced", max_results=20)
    
    session = Session()
    new_jobs_found = 0
    
    for res in results.get('results', []):
        url = res['url']
        # Check if we already know this lead
        if not session.query(Job).filter_by(id=url).first():
            # Pass BOTH title and description content to Gemini
            analysis = generate_pro_analysis(res['title'], res.get('content', ''), niche)
            
            if analysis.get('is_match'):
                job = Job(
                    id=url,
                    title=res['title'],
                    details=analysis.get('details', 'Extraction failed'),
                    score=analysis.get('score', 70),
                    pitch=analysis.get('pitch', 'Standard pitch applied'),
                    niche=niche,
                    url=url
                )
                session.add(job)
                new_jobs_found += 1
    
    session.commit()
    session.close()
    print(f"✅ Found and validated {new_jobs_found} new {niche} leads.")

if __name__ == "__main__":
    # Get niche from command line or default to Cyber Security
    target_niche = sys.argv[1] if len(sys.argv) > 1 else "Cyber Security"
    run_search(target_niche)
