import os
import time
import pandas as pd
from datetime import datetime
from duckduckgo_search import DDGS

# 1. Configuration
CSV_FILE = 'data/jobs.csv'

def fetch_cyber_leads():
    """Finds SIEM/SOAR jobs using DuckDuckGo as a proxy."""
    queries = [
        'site:upwork.com "SIEM" "Remote"',
        'site:upwork.com "SOAR" "Remote"',
        'site:freelancer.com "Splunk" "Sentinel"'
    ]
    found_jobs = []
    
    with DDGS() as ddgs:
        for query in queries:
            try:
                # 'timelimit=d' keeps it to the last 24 hours for max freshness
                results = ddgs.text(query, timelimit='d', max_results=5)
                for r in results:
                    if any(path in r['href'] for path in ["/jobs/", "/projects/"]):
                        found_jobs.append({
                            "project_title": r['title'].split(" - ")[0],
                            "source": r['href'],
                            "snippet": r['body'],
                            "found_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                time.sleep(2) # Prevent IP blocks
            except Exception as e:
                print(f"Error fetching {query}: {e}")
    return found_jobs

def process_and_save(new_jobs):
    """Filters duplicates and saves only new leads."""
    if not new_jobs:
        print("No jobs found in this crawl.")
        return

    os.makedirs('data', exist_ok=True)
    new_df = pd.DataFrame(new_jobs)

    if os.path.exists(CSV_FILE):
        existing_df = pd.read_csv(CSV_FILE)
        # Unique ID check via the 'source' URL
        fresh_leads = new_df[~new_df['source'].isin(existing_df['source'])]
        
        if not fresh_leads.empty:
            # We'll add a 'weightage_score' column for the UI to read
            # (In the next step, we'll replace this static 70 with real AI scoring)
            fresh_leads['weightage_score'] = 70 
            fresh_leads['is_genuine'] = True
            
            updated_df = pd.concat([existing_df, fresh_leads], ignore_index=True)
            updated_df.to_csv(CSV_FILE, index=False)
            print(f"✅ Saved {len(fresh_leads)} new leads.")
        else:
            print("p All found jobs are already in the database.")
    else:
        new_df['weightage_score'] = 70
        new_df['is_genuine'] = True
        new_df.to_csv(CSV_FILE, index=False)
        print("🚀 Initialized job database.")

if __name__ == "__main__":
    leads = fetch_cyber_leads()
    process_and_save(leads)
