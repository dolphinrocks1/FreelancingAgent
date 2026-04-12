import os, sys, json
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from tavily import TavilyClient
from datetime import datetime

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

# Database Setup
db_url = os.getenv("DATABASE_URL")
if not db_url: sys.exit("Missing DATABASE_URL")
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

# Niche Keyword Map
NICHE_MAP = {
    "Cyber Security": "SIEM OR SOAR OR Sentinel OR Qradar OR Wazuh OR 'SIEM Administrator'",
    "AI in Cyber Security": "'AI Security' OR 'ML for Cybersecurity' OR 'LLM Red Teaming'",
    "AI Agent Development": "'AI Agent' OR LangChain OR CrewAI OR 'Agentic Workflow'",
    "Web Development": "FastAPI OR React OR 'Python Developer' OR Streamlit",
    "Software Development": "Backend OR 'Distributed Systems' OR GoLang OR Python"
}

def run_search(selected_niche):
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    keywords = NICHE_MAP.get(selected_niche, selected_niche)
    query = f"(site:upwork.com OR site:remoteok.com) ({keywords}) jobs posted in last 24h"
    
    results = client.search(query=query, search_depth="advanced")
    session = Session()
    for res in results.get('results', []):
        if not session.query(Job).filter_by(id=res['url']).first():
            session.add(Job(id=res['url'], title=res['title'], url=res['url'], 
                            score=85, niche=selected_niche, pitch="Expert match."))
    session.commit()
    session.close()

if __name__ == "__main__":
    run_search(sys.argv[1] if len(sys.argv) > 1 else "Cyber Security")
