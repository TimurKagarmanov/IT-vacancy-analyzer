import time

import pandas as pd
import requests
from bs4 import BeautifulSoup

from storage_paths import STORAGE_DIR, ensure_storage

def parse_habr_career_full():
    base_url = "https://career.habr.com/vacancies?type=all"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    
    all_jobs = []
    page = 1 
    
    print("Start scraping Habr Career")
    while True:        
        url = f"{base_url}&page={page}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Error: {response.status_code}.")
            break
            
        soup = BeautifulSoup(response.text, 'html.parser')
        job_cards = soup.find_all('div', class_='vacancy-card')
        if not job_cards:
            print("Pages are finished, scraping is completed.")
            break

        for card in job_cards:
            title_elem = card.find('div', class_='vacancy-card__title')
            title = "Not specified"
            link = "No link"
            if title_elem:
                a_tag = title_elem.find('a')
                if a_tag:
                    title = a_tag.text.strip()
                    link = "https://career.habr.com" + a_tag.get('href')
            
            company_elem = card.find('div', class_='vacancy-card__company-title')
            company = company_elem.find('a').text.strip() if company_elem and company_elem.find('a') else "Not specified"
            
            salary_elem = card.find('div', class_='basic-salary')
            salary = salary_elem.text.strip() if salary_elem else "Not specified"
            
            date_elem = card.find('time', class_='basic-date')
            pub_date = date_elem.get('datetime') if date_elem else "Not specified"
            
            meta_elem = card.find('div', class_='vacancy-card__meta')
            meta_data = []
            if meta_elem:
                meta_items = meta_elem.find_all('span', class_='preserve-line')
                if not meta_items:
                    meta_items = meta_elem.find_all('a')
                
                for item in meta_items:
                    clean_text = item.text.strip()
                    if clean_text:
                        meta_data.append(clean_text)
            
            meta_string = " | ".join(meta_data) if meta_data else "Not specified"
            
            skills_elem = card.find('div', class_='vacancy-card__skills')
            skills = []
            if skills_elem:
                skill_tags = skills_elem.find_all('span', class_='preserve-line')
                skills = [skill.text.strip() for skill in skill_tags if skill.text.strip()]
            
            skills_string = ", ".join(skills)
            all_jobs.append({
                'Date': pub_date,
                'Company': company,
                'Title': title,
                'Salary': salary,
                'Skills': skills_string,
                'Meta_Info': meta_string,
                'Link': link
            })

        page += 1
        
        time.sleep(1) 
        if page > 200:
            print("Limit of 200 pages reached. Stopping.")
            break

    df = pd.DataFrame(all_jobs)
    df = df.dropna(subset=['Title'])
    df = df.drop_duplicates(subset=['Link'])
    return df

if __name__ == "__main__":
    ensure_storage()
    df_vacancies = parse_habr_career_full()
    out = STORAGE_DIR / "habr_vacancies_detailed.csv"
    df_vacancies.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"Data saved to {out}")