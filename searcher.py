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
    # Primary key remains the URL to prevent duplicates automatically
    id = Column(String, primary_key=True) 
    title = Column(String)
    url = Column(String)
    details = Column(Text)  # Necessary for the new Streamlit UI
    score = Column(Integer)
    niche = Column(String)
    pitch = Column(Text)    # Necessary for the new Streamlit UI
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
    # Ensure key exists before configuring
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"is_match": True, "score": 85, "details": "AI Key Missing", "pitch": "Please check your GEMINI_API_KEY."}

    genai.configure(api_key=api_key)
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
    
    if not db_url or not tavily_key:
        print("❌ Error: Missing environment variables (DATABASE_URL or TAVILY_API_KEY)")
        sys.exit(1)

    # 2. Database Setup
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    
    # 3. Build Search Query
    client = TavilyClient(api_key=tavily_key)
    keywords = NICHE_MAP.get(selected_niche, selected_niche)
    
    # UPDATED: Search query accommodates last 7 days
    search_query = f"(site:upwork.com OR site:remoteok.com OR site:freelancer.com) ({keywords}) jobs posted last 7 days"
    
    print(f"🕵️ Agent actively hunting for: {selected_niche}")
    print(f"🔑 Using keywords: {keywords}")
    
    try:
        results = client.search(query=search_query, search_depth="advanced", max_results=20)
        
        session = Session()
        new_leads = 0
        
        for res in results.get('results', []):
            url = res['url']
            
            # 4. Deduplication
            if not session.query(Job).filter_by(id=url).first():
                # 5. AI Enrichment
                analysis = generate_pro_analysis(res['title'], res.get('content', ''), selected_niche)
                
                # Only add if the AI confirms it matches your technical niche
                if analysis.get('is_match', True):
                    new_job = Job(
                        id=url,
                        title=res['title'],
                        url=url,
                        details=analysis.get('details', 'Details extraction failed'),
                        score=analysis.get('score', 85),
                        niche=selected_niche,
                        pitch=analysis.get('pitch', 'Pitch generation failed'),
                        status="New"
                    )
                    session.add(new_job)
                    new_leads += 1
        
        session.commit()
        session.close()
        print(f"✅ Success: Found {new_leads} new leads for {selected_niche}.")
        
    except Exception as e:
        print(f"❌ Search failed: {e}")

if __name__ == "__main__":
    niche_input = sys.argv[1] if len(sys.argv) > 1 else "Cyber Security"
    run_search(niche_input)
