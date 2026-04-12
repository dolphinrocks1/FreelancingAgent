import os
import sys
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from tavily import TavilyClient
from datetime import datetime

# --- Database Setup ---
Base = declarative_base()
class Job(Base):
    __tablename__ = 'jobs'
    id = Column(String, primary_key=True)
    title = Column(String)
    url = Column(String)
    score = Column(Integer)
    niche = Column(String)
    pitch = Column(Text)
    status = Column(String, default="New")
    found_at = Column(DateTime, default=datetime.utcnow)

engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

# --- Niche Keyword Configuration ---
NICHE_MAP = {
    "Cyber Security": "SIEM OR SOAR OR Sentinel OR Qradar OR Wazuh OR 'SIEM Administrator' OR 'Automation Engineer'",
    "AI in Cyber Security": "'AI Security' OR 'ML for Cybersecurity' OR 'LLM Red Teaming' OR 'AI Threat Detection'",
    "AI Agent Development": "'AI Agent' OR LangChain OR CrewAI OR 'AutoGPT' OR 'Agentic Workflow' OR 'LLM Engineer'",
    "Web Development": "FastAPI OR 'Full Stack' OR React OR 'Python Developer' OR 'Streamlit Expert'",
    "Software Development": "Backend OR 'Distributed Systems' OR GoLang OR 'System Architect' OR 'Python Backend'"
}

def run_search(selected_niche):
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    
    # Get keywords from our predefined map
    keywords = NICHE_MAP.get(selected_niche, selected_niche)
    
    # Build a pro-level search query
    # We target specific high-value sites and combine with our technical keywords
    search_query = f"(site:upwork.com OR site:remoteok.com OR site:freelancer.com) ({keywords}) jobs"
    
    print(f"🕵️ Agent actively hunting for: {selected_niche}")
    print(f"🔑 Using keywords: {keywords}")
    
    results = client.search(query=search_query, search_depth="advanced", max_results=15)
    
    session = Session()
    new_count = 0
    
    for res in results.get('results', []):
        url = res['url']
        if not session.query(Job).filter_by(id=url).first():
            new_job = Job(
                id=url,
                title=res['title'],
                url=url,
                score=85, # Default high score for keyword matches
                niche=selected_niche,
                pitch=f"Expert match for your {selected_niche} requirements using the latest industry tools.",
                status="New"
            )
            session.add(new_job)
            new_count += 1
    
    session.commit()
    session.close()
    print(f"✅ Found {new_count} new technical leads for {selected_niche}.")

if __name__ == "__main__":
    niche_from_ui = sys.argv[1] if len(sys.argv) > 1 else "Cyber Security"
    run_search(niche_from_ui)
