import pandas as pd
import requests
from bs4 import BeautifulSoup

from storage_paths import STORAGE_DIR, ensure_storage

def parse_wwr_rss():
    print("Start scraping We Work Remotely (RSS)")
    
    urls = [
        "https://weworkremotely.com/categories/remote-programming-jobs.rss",
        "https://weworkremotely.com/categories/remote-data-jobs.rss",
        "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss"
    ]
    
    all_jobs = []
    
    for url in urls:
        print(f"Loading feed: {url.split('/')[-1]}")
        response = requests.get(url)
        
        soup = BeautifulSoup(response.content, 'xml')
        items = soup.find_all('item')
        
        for item in items:
            full_title = item.title.text if item.title else ""
            if ":" in full_title:
                company, title = full_title.split(":", 1)
            else:
                company, title = "Not specified", full_title
                
            link = item.link.text if item.link else ""
            pub_date = item.pubDate.text if item.pubDate else ""
            
            all_jobs.append({
                'Company': company.strip(),
                'Title': title.strip(),
                'Location': 'Remote',
                'Salary': 'Not specified',
                'Link': link.strip()
            })
            
    df = pd.DataFrame(all_jobs)
    if not df.empty:
        df = df.drop_duplicates(subset=['Link'])
        print(f"Total unique vacancies collected from WWR: {len(df)}")
    return df

if __name__ == "__main__":
    ensure_storage()
    df_wwr = parse_wwr_rss()
    df_wwr.to_csv(STORAGE_DIR / "wwr_vacancies.csv", index=False, encoding="utf-8-sig")