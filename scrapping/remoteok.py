import pandas as pd
import requests

from storage_paths import STORAGE_DIR, ensure_storage

def parse_remoteok():
    print("Start scraping RemoteOK")
    
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
    for tag in search_queries:
        url = f"https://remoteok.com/api?tag={tag}"
        headers = {"User-Agent": "Mozilla/5.0"} 
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Error: {response.status_code}.")
            return pd.DataFrame()
        data = response.json()
        jobs = data[1:] 
        
        for job in jobs:
            all_jobs.append({
                'Company': job.get('company', 'Not specified'),
                'Title': job.get('position', 'Not specified'),
                'Location': job.get('location', 'Remote'),
                'Salary_Min': job.get('salary_min', 0),
                'Salary_Max': job.get('salary_max', 0),
                'Skills': ", ".join(job.get('tags', [])),
                'Link': job.get('url', '')
            })
    df = pd.DataFrame(all_jobs)
    
    if not df.empty:
        df = df.dropna(subset=['Title'])
        df = df.drop_duplicates(subset=['Link'])
        print(f"Total unique vacancies collected from RemoteOK: {len(df)}")
    else:
        print("Data not collected.")
        
    return df

if __name__ == "__main__":
    ensure_storage()
    df_remoteok = parse_remoteok()
    if not df_remoteok.empty:
        out = STORAGE_DIR / "remoteok_vacancies.csv"
        df_remoteok.to_csv(out, index=False, encoding="utf-8-sig")
        print(f"Data saved to {out}")