import random
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup

from storage_paths import STORAGE_DIR, ensure_storage


def parse_superjob():
    print("Start scraping SuperJob")
    search_queries = [
        "Data Scientist", "Data Analyst", "Аналитик данных", "Data Engineer",
        "Machine Learning", "ML Engineer", "Computer Vision", "NLP Engineer",
        "Deep Learning", "AI Engineer", "Big Data", "Data Architect", 
        "BI Analyst", "BI разработчик", "Системный аналитик", "Mlopps", "Spark",
        "Python", "Django", "FastAPI", "Flask", "Golang", "Go developer",
        "Java", "Spring Boot", "C#", ".NET", "C++", "Rust", "PHP", "Laravel",
        "Node.js", "Ruby", "Ruby on Rails", "Backend Developer", "Backend разработчик",
        "Frontend", "Frontend разработчик", "JavaScript", "TypeScript", "React",
        "Vue.js", "Angular", "Next.js", "D3.js", "HTML/CSS", "Web Developer",
        "Веб-разработчик", "Верстальщик",
        "iOS Developer", "Android Developer", "Swift", "Kotlin", "Flutter",
        "React Native", "Mobile Developer", "Мобильный разработчик",
        "DevOps", "Site Reliability Engineer", "SRE", "Cloud Engineer",
        "Docker", "Kubernetes", "K8s", "Terraform", "Ansible", "Linux",
        "System Administrator", "Системный администратор", "Админ", 
        "Network Engineer", "Сетевой инженер",
        "Тестировщик", "QA Engineer", "QA Automation", "Manual QA", 
        "Автотестировщик", "SDET", "AQA",
        "Product Manager", "Project Manager", "Product Owner", "Scrum Master",
        "Agile Coach", "Business Analyst", "Бизнес-аналитик", "Team Lead",
        "Tech Lead", "Delivery Manager", "IT Manager", "IT Director", "СТО",
        "UX/UI Designer", "Product Designer", "Web Designer", "Графический дизайнер",
        "Figma", "User Experience",
        "Information Security", "Кибербезопасность", "Пентестер", "Security Engineer",
        "Database Administrator", "Администратор баз данных", "SQL", "PostgreSQL",
        "Game Developer", "Unity", "Unreal Engine", "Embedded Developer", 
        "Blockchain", "Solidity", "ERP", "SAP", "1C программист", "1С разработчик",
        "Программист", "Разработчик", "Инженер-программист", "Специалист ИТ",
        "Информационные технологии", "IT Specialist", "IT Analyst", "IT Engineer",
        "IT Developer", "IT Programmer", "IT Technician", "IT Support",
        "Техническая поддержка", "Helpdesk"
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.superjob.ru/",
    }
    all_jobs = []
    for query in search_queries:
        print(f"Query: {query}")
        for page in range(1, 11):
            url = f"https://www.superjob.ru/vacancy/search/?keywords={query}&page={page}"
            try:
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code != 200:
                    print(f"HTTP {response.status_code} page {page}")
                    break
                soup = BeautifulSoup(response.text, "html.parser")
                vacancy_links = [
                    a for a in soup.find_all("a", href=True) if "/vakansii/" in a["href"] and a.text.strip()
                ]
                if not vacancy_links:
                    print(f"No vacancies page {page}")
                    break
                page_count = 0
                for link_tag in vacancy_links:
                    container = link_tag.find_parent("div")
                    for _ in range(3):
                        if container and container.name != "div":
                            container = container.parent
                    if not container:
                        continue
                    title = link_tag.text.strip()
                    url_vac = "https://www.superjob.ru" + link_tag["href"]
                    if any(j["Link"] == url_vac for j in all_jobs):
                        continue
                    salary = "Not specified"
                    company = "Not specified"
                    text_elements = container.get_text(separator="|").split("|")
                    for text in text_elements:
                        text = text.strip()
                        if "₽" in text or "от" in text.lower() or "до" in text.lower():
                            salary = text
                        elif len(text) > 3 and text not in title and text not in salary:
                            company = text
                    all_jobs.append(
                        {
                            "Title": title,
                            "Company": company,
                            "Salary": salary,
                            "Region": "Russia",
                            "Link": url_vac,
                        }
                    )
                    page_count += 1
                print(f"Page {page}: +{page_count}")
                time.sleep(random.uniform(1.5, 3.0))
            except Exception as e:
                print(f"Error: {e}")
                break
    df = pd.DataFrame(all_jobs)
    return df


if __name__ == "__main__":
    ensure_storage()
    df_sj = parse_superjob()
    if not df_sj.empty:
        df_sj = df_sj.drop_duplicates(subset=["Link"])
        out = STORAGE_DIR / "superjob_vacancies.csv"
        df_sj.to_csv(out, index=False, encoding="utf-8-sig")
        print(f"Saved {len(df_sj)} rows to {out}")
    else:
        print("Empty result.")
