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
    details = Column(Text) # Added to store AI extraction
    score = Column(Integer)
    niche = Column(String)
    pitch = Column(Text)
    status = Column(String, default="New")
    found_at = Column(DateTime, default=datetime.utcnow)

# --- Configuration & Keyword Map ---
NICHE_MAP = {
    "Cyber Security": "SIEM OR SOAR OR Sentinel OR Qradar OR Wazuh OR 'SIEM Administrator' OR 'Automation Engineer'",
    "AI in Cyber Security": "'AI Security' OR 'ML for Cybersecurity' OR 'LLM Red Teaming' OR 'AI Threat Detection'",
    "AI Agent Development": "'AI Agent' OR LangChain OR CrewAI OR 'AutoGPT' OR 'Agentic Workflow' OR 'LLM Engineer'",
    "Web Development": "FastAPI OR 'Full Stack' OR React OR 'Python Developer' OR 'Streamlit Expert'",
    "Software Development": "Backend OR 'Distributed Systems' OR GoLang OR 'System Architect' OR 'Python Backend'"
}

# --- AI Analysis Engine ---
def generate_pro_analysis(title, content, niche):
    """Uses Gemini to validate the niche and generate the 3-paragraph pitch."""
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Act as a Technical Sales Expert for a {niche} consultant. 
    Analyze this job:
    Title: {title}
    Description: {content}
    
    1. VALIDATE: Is this job actually about {niche}? If unrelated (like real estate), set 'is_match' to false.
    2. EXTRACT: Client/Company, Core Requirements, Budget.
    3. PITCH: Write a 3-paragraph winning pitch focusing on technical problem solving.

    Return ONLY JSON: 
    {{
      "is_match": true, 
      "score": 90, 
      "details": "Company: [Name] | Requirements: [List] | Budget: [Amount]", 
      "pitch": "The full pitch text..."
    }}
    """
    try:
        response = model.generate_content(prompt)
        # Clean potential markdown from AI response
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"⚠️ AI Skip: {e}")
        return {"is_match": False}

# --- Main Search Logic ---
def run_search(selected_niche):
    # 1. Environment Check
    db_url = os.getenv("DATABASE_URL")
    tavily_key = os.getenv("TAVILY_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    if not all([db_url, tavily_key, gemini_key]):
        print("❌ Error: Missing environment variables (DATABASE_URL, TAVILY_API_KEY, or GEMINI_API_KEY)")
        sys.exit(1)

    # 2. Database Setup
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    
    # 3. Build Search Query
    client = TavilyClient(api_key=tavily_key)
    keywords = NICHE_MAP.get(selected_niche, selected_niche)
    
    # We broaden the search slightly to ensure we catch results, then let AI filter the noise
    search_query = f"(site:upwork.com OR site:remoteok.com OR site:freelancer.com) ({keywords}) jobs"
    
    print(f"🕵️ Agent actively hunting for: {selected_niche}")
    
    try:
        # Increase max_results to 20 to give the AI more to work with
        results = client.search(query=search_query, search_depth="advanced", max_results=20)
        
        session = Session()
        new_leads = 0
        
        for res in results.get('results', []):
            url = res['url']
            
            # 4. Deduplication
            if not session.query(Job).filter_by(id=url).first():
                # 5. AI Validation & Pitch Generation
                analysis = generate_pro_analysis(res['title'], res.get('content', ''), selected_niche)
                
                if analysis.get('is_match'):
                    new_job = Job(
                        id=url,
                        title=res['title'],
                        url=url,
                        details=analysis.get('details', 'No details extracted'),
                        score=analysis.get('score', 85),
                        niche=selected_niche,
                        pitch=analysis.get('pitch', 'Pitch generation failed'),
                        status="New"
                    )
                    session.add(new_job)
                    new_leads += 1
        
        session.commit()
        session.close()
        print(f"✅ Success: Found and AI-validated {new_leads} new leads for {selected_niche}.")
        
    except Exception as e:
        print(f"❌ Search failed: {e}")

if __name__ == "__main__":
    niche_input = sys.argv[1] if len(sys.argv) > 1 else "Cyber Security"
    run_search(niche_input)
