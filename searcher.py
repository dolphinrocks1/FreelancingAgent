import os
import json
import pandas as pd
import google.generativeai as genai
import feedparser
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from datetime import datetime

# --- CONFIGURATION ---
# Fixed: Always create directory to prevent GitHub Action "pathspec" errors
os.makedirs('data', exist_ok=True) 
CSV_FILE = 'data/jobs.csv'

# Setup AI
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def scrape_with_playwright(url):
    """Bypasses 403 Forbidden errors by using a real browser head."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        try:
            print(f"🌐 Scraping: {url}")
            page.goto(url, wait_until="networkidle", timeout=60000)
            content = page.content()
            browser.close()
            return BeautifulSoup(content, 'html.parser')
        except Exception as e:
            print(f"❌ Browser error: {e}")
            browser.close()
            return None

def get_linkedin_leads():
    """Fetches niche security roles from LinkedIn Guest Search."""
    url = "https://www.linkedin.com/jobs/search/?keywords=SIEM%20SOAR%20Splunk%20Sentinel"
    soup = scrape_with_playwright(url)
    leads = []
    if soup:
        for card in soup.select(".base-search-card"):
            title_tag = card.select_one(".base-search-card__title")
            link_tag = card.select_one(".base-card__full-link")
            if title_tag and link_tag:
                leads.append({
                    "title": title_tag.text.strip(),
                    "source": link_tag["href"].split('?')[0],
                    "snippet": "LinkedIn Search Lead"
                })
    return leads

def get_freelancer_leads():
    """Fetches automation and security roles from Freelancer.com."""
    url = "https://www.freelancer.com/jobs/?keyword=Cybersecurity%20Automation"
    soup = scrape_with_playwright(url)
    leads = []
    if soup:
        for card in soup.select(".JobSearchCard-item"):
            title_tag = card.select_one(".JobSearchCard-primary-heading-link")
            if title_tag:
                leads.append({
                    "title": title_tag.text.strip(),
                    "source": "https://www.freelancer.com" + title_tag["href"],
                    "snippet": "Freelancer.com Lead"
                })
    return leads

def fetch_rss_leads():
    """Existing RSS logic for Upwork and RemoteOK."""
    feeds = [
        "https://www.upwork.com/ab/feed/jobs/rss?q=SIEM+OR+SOAR+OR+Wazuh",
        "https://remoteok.com/remote-security-jobs.rss"
    ]
    results = []
    for url in feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]:
            results.append({"title": entry.title, "source": entry.link, "snippet": entry.description})
    return results

def get_ai_score(title, snippet):
    """Refined scoring: Prioritizes niche tools, allows 'Security Engineer'."""
    prompt = f"""
    Analyze this freelance lead for a SIEM/SOAR/Detection Engineer.
    Title: {title}
    Details: {snippet}

    SCORING RULES:
    - 80-100: Explicitly mentions Splunk, XSOAR, Sentinel, QRadar, or Wazuh.
    - 60-79: General Cybersecurity/Automation Engineer or SOC roles.
    - 0: HR, Recruitment, Management, GTM, or Compliance roles.

    Return JSON: {{"score": 90, "reason": "Mentions Splunk SOAR", "bid": "Expert pitch..."}}
    """
    try:
        response = model.generate_content(prompt)
        cleaned = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(cleaned)
    except:
        return {"score": 0, "reason": "AI Error"}

def main():
    # 1. Gather all leads
    all_raw = fetch_rss_leads() + get_linkedin_leads() + get_freelancer_leads()
    
    # 2. Setup CSV
    if not os.path.exists(CSV_FILE):
        pd.DataFrame(columns=["title", "source", "weightage_score", "is_genuine", "draft", "found_at"]).to_csv(CSV_FILE, index=False)
    
    df = pd.read_csv(CSV_FILE)
    new_data = []

    # 3. Process with LOWER threshold (60) to see results
    for lead in all_raw:
        if lead['source'] in df['source'].values: continue
            
        analysis = get_ai_score(lead['title'], lead['snippet'])
        if analysis.get('score', 0) >= 60:
            print(f"✅ Match Found: {lead['title']} ({analysis['score']})")
            new_data.append({
                "title": lead['title'],
                "source": lead['source'],
                "weightage_score": analysis['score'],
                "is_genuine": "Verified Lead",
                "draft": analysis.get('bid', "N/A"),
                "found_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            })

    # 4. Save
    if new_data:
        pd.concat([df, pd.DataFrame(new_data)], ignore_index=True).to_csv(CSV_FILE, index=False)
        print(f"🚀 Success: Added {len(new_data)} new leads.")
    else:
        print("Done. All found leads were below quality threshold.")

if __name__ == "__main__":
    main()
