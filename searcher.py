import os
import sys
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from tavily import TavilyClient
import google.generativeai as genai
from datetime import datetime
import json

# --- Database Setup ---
Base = declarative_base()
class Job(Base):
    __tablename__ = 'jobs'
    id = Column(String, primary_key=True) # We'll use the URL as ID
    title = Column(String)
    url = Column(String)
    score = Column(Integer)
    niche = Column(String)
    pitch = Column(Text)
    status = Column(String, default="New") # New, Applied, Archived
    found_at = Column(DateTime, default=datetime.utcnow)

# Connect to Neon Postgres
engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

# --- AI Setup ---
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
ai_model = genai.GenerativeModel('gemini-1.5-flash')

def get_ai_score(title, niche):
    prompt = f"Score this job title '{title}' for a '{niche}' freelancer on a scale of 0-100. Return ONLY a JSON object: {{'score': 85, 'pitch': 'Short 2-sentence pitch'}}"
    try:
        response = ai_model.generate_content(prompt)
        data = json.loads(response.text.replace('```json', '').replace('```', ''))
        return data
    except:
        return {"score": 50, "pitch": "Interested in this role."}

def run_search(niche):
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    # Broad search across known job boards
    query = f"site:upwork.com OR site:remoteok.com OR site:freelancer.com '{niche}' jobs posted in last 24 hours"
    
    print(f"🚀 Searching for {niche} leads...")
    search_result = client.search(query=query, search_depth="advanced")
    
    session = Session()
    new_count = 0
    
    for res in search_result.get('results', []):
        url = res['url']
        # Duplicate check
        if not session.query(Job).filter_by(id=url).first():
            analysis = get_ai_score(res['title'], niche)
            
            if analysis['score'] >= 40:
                new_job = Job(
                    id=url,
                    title=res['title'],
                    url=url,
                    score=analysis['score'],
                    niche=niche,
                    pitch=analysis['pitch']
                )
                session.add(new_job)
                new_count += 1
                
    session.commit()
    session.close()
    print(f"✅ Found {new_count} new high-quality leads.")

if __name__ == "__main__":
    niche_input = sys.argv[1] if len(sys.argv) > 1 else "Cyber Security"
    run_search(niche_input)
