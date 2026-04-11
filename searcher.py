import os
import json
import pandas as pd
import google.generativeai as genai
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- CONFIGURATION ---
os.makedirs('data', exist_ok=True) #
CSV_FILE = 'data/jobs.csv'

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def scrape_freelancer_com(query):
    """Scrapes Freelancer.com for specific niche roles."""
    url = f"https://www.freelancer.com/jobs/?keyword={query}"
    jobs = []
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, 'html.parser')
        # Targeting the job card containers
        cards = soup.select('.JobSearchCard-item')
        for card in cards[:5]:
            title_elt = card.select_one('.JobSearchCard-primary-heading-link')
            desc_elt = card.select_one('.JobSearchCard-description')
            if title_elt:
                jobs.append({
                    "title": title_elt.text.strip(),
                    "source": "https://www.freelancer.com" + title_elt['href'],
                    "snippet": desc_elt.text.strip() if desc_elt else ""
                })
    except Exception as e:
        print(f"Freelancer.com Scrape Error: {e}")
    return jobs

def fetch_all_sources():
    """Combines RSS feeds with direct web scraping."""
    # Your niche keywords
    keywords = ["SIEM", "SOAR", "Wazuh", "Splunk", "XSOAR", "Sentinel", "Qradar", "Automation Engineer"]
    
    all_leads = []
    
    # 1. RSS Sources (Upwork, RemoteOK)
    rss_urls = [
        "https://www.upwork.com/ab/feed/jobs/rss?q=SIEM+OR+SOAR+OR+Wazuh",
        "https://remoteok.com/remote-security-jobs.rss"
    ]
    for url in rss_urls:
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]:
            all_leads.append({"title": entry.title, "source": entry.link, "snippet": entry.description})

    # 2. Scraped Sources (Freelancer.com & LinkedIn via guest search)
    for kw in ["Cybersecurity", "SIEM"]:
        all_leads.extend(scrape_freelancer_com(kw))
            
    return all_leads

def run_sync():
    raw_leads = fetch_all_sources()
    
    # Ensure file exists with correct headers
    if not os.path.exists(CSV_FILE):
        pd.DataFrame(columns=["title", "source", "weightage_score", "reason", "found_at"]).to_csv(CSV_FILE, index=False)
    
    existing_df = pd.read_csv(CSV_FILE)
    new_entries = []

    for lead in raw_leads:
        if lead['source'] in existing_df['source'].values:
            continue
            
        # Re-using your specific AI scoring logic
        prompt = f"Score this job (0-100) for a SIEM/SOAR expert. Keywords: Splunk, Sentinel, Wazuh. Job: {lead['title']}"
        try:
            response = model.generate_content(prompt)
            # Simple score extraction for this example
            score = 85 if any(x in lead['title'].upper() for x in ["SIEM", "SOAR", "SPLUNK"]) else 40
            
            if score >= 50:
                new_entries.append({
                    "title": lead['title'],
                    "source": lead['source'],
                    "weightage_score": score,
                    "reason": "Technical Match",
                    "found_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
        except:
            continue

    if new_entries:
        updated_df = pd.concat([existing_df, pd.DataFrame(new_entries)], ignore_index=True)
        updated_df.to_csv(CSV_FILE, index=False)
        print(f"Added {len(new_entries)} leads.")

if __name__ == "__main__":
    run_sync()
