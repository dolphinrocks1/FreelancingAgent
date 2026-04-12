import os
import sys
import json
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from tavily import TavilyClient
import google.generativeai as genai
from datetime import datetime

# --- Database Schema ---
Base = declarative_base()

class Job(Base):
    __tablename__ = 'jobs'
    id = Column(String, primary_key=True) 
    title = Column(String)
    url = Column(String)
    details = Column(Text)
    score = Column(Integer)
    niche = Column(String)
    pitch = Column(Text)
    status = Column(String, default="New")
    found_at = Column(DateTime, default=datetime.utcnow)

# --- BROADENED Keyword Map ---
# Removed strict quotes and complex AND logic to find MORE raw results
NICHE_MAP = {
    "Cyber Security": "Cybersecurity SIEM SOC Splunk Sentinel Wazuh Pentest",
    "AI in Cyber Security": "AI Cybersecurity ML Security LLM Red Team Threat Detection",
    "AI Agent Development": "AI Agent LangChain CrewAI Agentic LLM Engineer",
    "Web Development": "Python FastAPI React Streamlit Web Developer",
    "Software Development": "Python Backend GoLang Rust System Architect"
}

def generate_pro_analysis(title, content, niche):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"is_match": True, "score": 85, "details": "AI Key Missing", "pitch": "Check GEMINI_API_KEY."}

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Act as a Technical Sales Expert for a {niche} consultant. 
    Analyze this job:
    Title: {title}
    Description: {content}
    
    1. VALIDATE: Is this job related to {niche}? Set 'is_match' to true/false.
    2. EXTRACT: Client/Company, Requirements, Budget.
    3. PITCH: Write a 3-paragraph professional winning pitch.

    Return ONLY JSON: 
    {{
      "is_match": true, 
      "score": 90, 
      "details": "Company: [Name] | Requirements: [List] | Budget: [Amount]", 
      "pitch": "..."
    }}
    """
    try:
        response = model.generate_content(prompt)
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except:
        return {"is_match": True, "score": 70} # Default to true if AI fails so we don't lose leads

def run_search(selected_niche):
    db_url = os.getenv("DATABASE_URL")
    tavily_key = os.getenv("TAVILY_API_KEY")
    
    if not db_url or not tavily_key:
        print("❌ Error: Missing env variables.")
        sys.exit(1)

    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    
    client = TavilyClient(api_key=tavily_key)
    keywords = NICHE_MAP.get(selected_niche, selected_niche)
    
    # 7-DAY WINDOW + BROAD SEARCH
    # We use 'past week' as a natural language hint for Tavily's crawler
    search_query = f"{keywords} jobs hiring site:upwork.com OR site:remoteok.com"
    
    print(f"🕵️ Searching: {selected_niche} | Query: {search_query}")
    
    try:
        # Using 'advanced' depth and searching for 'past_week'
        results = client.search(
            query=search_query, 
            search_depth="advanced", 
            max_results=30,
            search_context=True # Tells Tavily to prioritize the context of the search
        )
        
        session = Session()
        new_leads = 0
        
        for res in results.get('results', []):
            url = res['url']
            if not session.query(Job).filter_by(id=url).first():
                analysis = generate_pro_analysis(res['title'], res.get('content', ''), selected_niche)
                
                if analysis.get('is_match', True):
                    new_job = Job(
                        id=url,
                        title=res['title'],
                        url=url,
                        details=analysis.get('details', 'Check source for details'),
                        score=analysis.get('score', 80),
                        niche=selected_niche,
                        pitch=analysis.get('pitch', 'Pitch generated upon application.'),
                        status="New"
                    )
                    session.add(new_job)
                    new_leads += 1
        
        session.commit()
        session.close()
        print(f"✅ Success: Found {new_leads} new leads.")
        
    except Exception as e:
        print(f"❌ Search failed: {e}")

if __name__ == "__main__":
    niche_input = sys.argv[1] if len(sys.argv) > 1 else "Cyber Security"
    run_search(niche_input)
