import os
import sys
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from tavily import TavilyClient
from datetime import datetime

# --- Database Schema ---
Base = declarative_base()

class Job(Base):
    __tablename__ = 'jobs'
    # We use the URL as the primary key to automatically prevent duplicate leads
    id = Column(String, primary_key=True) 
    title = Column(String)
    url = Column(String)
    score = Column(Integer)
    niche = Column(String)
    pitch = Column(Text)
    status = Column(String, default="New")
    found_at = Column(DateTime, default=datetime.utcnow)

# --- Configuration & Keyword Map ---
# This map ensures that each niche uses its own specific technical "lane"
NICHE_MAP = {
    "Cyber Security": "SIEM OR SOAR OR Sentinel OR Qradar OR Wazuh OR 'SIEM Administrator' OR 'Automation Engineer'",
    "AI in Cyber Security": "'AI Security' OR 'ML for Cybersecurity' OR 'LLM Red Teaming' OR 'AI Threat Detection'",
    "AI Agent Development": "'AI Agent' OR LangChain OR CrewAI OR 'AutoGPT' OR 'Agentic Workflow' OR 'LLM Engineer'",
    "Web Development": "FastAPI OR 'Full Stack' OR React OR 'Python Developer' OR 'Streamlit Expert'",
    "Software Development": "Backend OR 'Distributed Systems' OR GoLang OR 'System Architect' OR 'Python Backend'"
}

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
    
    # Search across major freelance and remote boards
    search_query = f"(site:upwork.com OR site:remoteok.com OR site:freelancer.com) ({keywords}) jobs"
    
    print(f"🕵️ Agent actively hunting for: {selected_niche}")
    print(f"🔑 Using keywords: {keywords}")
    
    try:
        results = client.search(query=search_query, search_depth="advanced", max_results=20)
        
        session = Session()
        new_leads = 0
        
        for res in results.get('results', []):
            url = res['url']
            
            # 4. Deduplication: Only add if URL doesn't exist in Postgres
            if not session.query(Job).filter_by(id=url).first():
                new_job = Job(
                    id=url,
                    title=res['title'],
                    url=url,
                    score=85, # Default priority score
                    niche=selected_niche,
                    pitch=f"Expert technical match for {selected_niche} requirements.",
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
    # Accepts niche from command line (used by Streamlit and GitHub Actions)
    niche_input = sys.argv[1] if len(sys.argv) > 1 else "Cyber Security"
    run_search(niche_input)
