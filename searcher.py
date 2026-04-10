import pandas as pd
import os
from datetime import datetime

# 1. Configuration
CSV_FILE = 'data/jobs.csv'

def save_jobs(new_jobs_list):
    """
    Saves a list of job dictionaries to CSV, preventing duplicates based on URL.
    """
    # Create the data directory if it doesn't exist for the GitHub Action
    os.makedirs('data', exist_ok=True)
    
    # Convert new findings to a DataFrame
    new_df = pd.DataFrame(new_jobs_list)
    
    if os.path.exists(CSV_FILE):
        # Load existing data
        existing_df = pd.read_csv(CSV_FILE)
        
        # Filter: Only keep jobs where the 'source' URL isn't already in our CSV
        # This is the "De-duplication" magic line
        fresh_leads = new_df[~new_df['source'].isin(existing_df['source'])]
        
        if not fresh_leads.empty:
            # Append new leads to the end of the existing file
            updated_df = pd.concat([existing_df, fresh_leads], ignore_index=True)
            updated_df.to_csv(CSV_FILE, index=False)
            print(f"✅ Added {len(fresh_leads)} new unique leads.")
        else:
            print("p No new leads found this hour.")
    else:
        # First time running? Create the file from scratch
        new_df.to_csv(CSV_FILE, index=False)
        print(f"🚀 Initialized database with {len(new_df)} leads.")

# --- MOCK AGENT LOGIC (Replace this with your actual scraping/LLM code) ---
def run_agent():
    # In the real version, this would be your DuckDuckGo + LLM logic
    mock_results = [
        {
            "project_title": "Sentinel Specialist Needed",
            "source": "https://upwork.com/jobs/123", # Unique ID
            "weightage_score": 95,
            "tech": "Sentinel",
            "is_genuine": True,
            "bid_draft": "I can optimize your Sentinel KQL...",
            "found_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
    ]
    save_jobs(mock_results)

if __name__ == "__main__":
    run_agent()
