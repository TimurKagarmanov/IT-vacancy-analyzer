import sys
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scrapping.processing import is_it_vacancy
from scrapping.storage_paths import STORAGE_DIR, ensure_storage


def parse_trudvsem():
    print("Start scraping TrudVsem")
    base_url = "https://opendata.trudvsem.ru/api/v1/vacancies"
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
    all_jobs = []
    for query in search_queries:
        offset = 0
        limit = 100
        while True:
            params = {"text": query, "limit": limit, "offset": offset}
            response = requests.get(base_url, params=params, timeout=60)
            if response.status_code != 200:
                print(f"Error: HTTP {response.status_code}")
                break
            data = response.json()
            if "results" not in data or "vacancies" not in data["results"]:
                break
            vacancies = data["results"]["vacancies"]
            if not vacancies:
                print(f"Done query '{query}'")
                break
            for item in vacancies:
                vac = item["vacancy"]
                title = vac.get("job-name", "Not specified")
                company = vac.get("company", {}).get("name", "Not specified")
                salary_min = vac.get("salary_min", 0)
                salary_max = vac.get("salary_max", 0)
                region = vac.get("region", {}).get("name", "Not specified")
                link = vac.get("vac_url", "No link")
                requirement = vac.get("requirement", {}).get("qualification", "Not specified")
                if not is_it_vacancy(title, requirement):
                    continue
                all_jobs.append(
                    {
                        "Title": title,
                        "Company": company,
                        "Salary_Min": salary_min,
                        "Salary_Max": salary_max,
                        "Region": region,
                        "Skills_Req": requirement,
                        "Link": link,
                    }
                )
            print(f"Collected offset {offset} (+{len(vacancies)}) query '{query}'...")
            offset += limit
            time.sleep(1)
    df = pd.DataFrame(all_jobs)
    if not df.empty:
        df = df.drop_duplicates(subset=["Link"])
        print(f"Total unique IT vacancies: {len(df)}")
    else:
        print("No data collected.")
    return df


if __name__ == "__main__":
    ensure_storage()
    df_vacancies = parse_trudvsem()
    out = STORAGE_DIR / "trudvsem_vacancies.csv"
    df_vacancies.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"Saved {out}")
