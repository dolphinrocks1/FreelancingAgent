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

# --- Broad Keyword Map ---
NICHE_MAP = {
    "Cyber Security": "Cybersecurity SIEM SOC Splunk Sentinel Wazuh Pentest jobs",
    "AI in Cyber Security": "AI Cybersecurity ML Security LLM Red Team Threat Detection jobs",
    "AI Agent Development": "AI Agent LangChain CrewAI Agentic LLM Engineer jobs",
    "Web Development": "Python FastAPI React Streamlit Web Developer jobs",
    "Software Development": "Python Backend GoLang Rust System Architect jobs"
}

def generate_pro_analysis(title, full_content, niche):
    """Demands specific data extraction and a structured 3-paragraph pitch."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"is_match": True, "score": 70, "details": "API Key Missing", "pitch": "Check configuration."}

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # We truncate content to avoid token limits while keeping the meat of the job post
    context = full_content[:10000] if full_content else "No description available."
    
    prompt = f"""
    Act as an Expert Technical Recruiter. Analyze this raw job data for a {niche} role:
    Title: {title}
    Full Content: {context}
    
    TASKS:
    1. VALIDATE: If this is a generic 'hire me' profile or unrelated noise, set 'is_match' to false.
    2. EXTRACT: Find the specific Company Name, the exact Budget/Salary (if mentioned), and the top 3 technical requirements.
    3. PITCH: Write a high-conversion 3-paragraph pitch. 
       - Para 1: Hook them by mentioning a specific requirement found in their description.
       - Para 2: Explain how a {niche} expert solves their specific pain point.
       - Para 3: Professional call to action.

    Return ONLY JSON: 
    {{
      "is_match": true, 
      "score": 95, 
      "details": "COMPANY: [Name] | BUDGET: [Price/Range] | REQS: [Req 1, Req 2, Req 3]", 
      "pitch": "[Paragraph 1]\\n\\n[Paragraph 2]\\n\\n[Paragraph 3]"
    }}
    """
    try:
        response = model.generate_content(prompt)
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"⚠️ AI Analysis Failed: {e}")
        return {"is_match": True, "score": 70, "details": "Full analysis failed. Please check source.", "pitch": "Standard match for niche."}

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
    
    # Aggressive search query
    search_query = f"{keywords} (site:upwork.com OR site:remoteok.com OR site:wellfound.com)"
    
    print(f"🕵️ Deep-hunting: {selected_niche}")
    
    try:
        # CRITICAL CHANGE: include_raw_content=True allows Gemini to see the full page
        results = client.search(
            query=search_query, 
            search_depth="advanced", 
            max_results=15,
            include_raw_content=True
        )
        
        session = Session()
        new_leads = 0
        
        for res in results.get('results', []):
            url = res['url']
            if not session.query(Job).filter_by(id=url).first():
                # Use 'raw_content' if available, otherwise fallback to 'content' snippet
                job_body = res.get('raw_content') or res.get('content', '')
                
                analysis = generate_pro_analysis(res['title'], job_body, selected_niche)
                
                if analysis.get('is_match'):
                    new_job = Job(
                        id=url,
                        title=res['title'],
                        url=url,
                        details=analysis.get('details'),
                        score=analysis.get('score', 80),
                        niche=selected_niche,
                        pitch=analysis.get('pitch'),
                        status="New"
                    )
                    session.add(new_job)
                    new_leads += 1
        
        session.commit()
        session.close()
        print(f"✅ Deep Scan Complete: {new_leads} enriched leads found.")
        
    except Exception as e:
        print(f"❌ Search failed: {e}")

if __name__ == "__main__":
    niche_input = sys.argv[1] if len(sys.argv) > 1 else "Cyber Security"
    run_search(niche_input)
