import random
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.exceptions import ChunkedEncodingError
from requests.exceptions import ConnectionError as RequestsConnectionError

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scrapping.processing import is_it_vacancy
from scrapping.storage_paths import STORAGE_DIR, ensure_storage

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.rabota.ru/",
}

LIST_URL = "https://www.rabota.ru/vacancy"
_ID_RE = re.compile(r"/vacancy/(\d+)/")

_NETWORK_ERRORS = (
    RequestsConnectionError,
    ChunkedEncodingError,
    ConnectionResetError,
    BrokenPipeError,
)


def _read_csv_safe(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except pd.errors.EmptyDataError:
        return pd.DataFrame()

RABOTA_CSV = STORAGE_DIR / "rabota_vacancies.csv"

SEARCH_QUERIES = [
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
    "Техническая поддержка", "Helpdesk",
]


def _normalize_vacancy_url(url: str) -> str:
    u = url.strip()
    if u.endswith("/"):
        return u[:-1]
    return u


def _get(
    url: str,
    session: requests.Session,
    timeout: int = 45,
    *,
    retries: int = 4,
    base_delay: float = 2.0,
) -> str | None:
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            r = session.get(url, headers=HEADERS, timeout=timeout)
            r.raise_for_status()
            return r.text
        except _NETWORK_ERRORS as e:
            print(f"[ABORT] Network error GET {url}: {e}")
            raise
        except requests.RequestException as e:
            last_err = e
            wait = base_delay * (2**attempt) + random.uniform(0, 1.5)
            print(f"[WARN] GET {url} attempt {attempt + 1}/{retries}: {e} — sleep {wait:.1f}s")
            time.sleep(wait)
    print(f"[WARN] GET {url}: gave up after {retries} attempts ({last_err})")
    return None


def collect_vacancy_ids_from_list(html: str) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for m in _ID_RE.finditer(html):
        vid = m.group(1)
        if vid not in seen:
            seen.add(vid)
            ordered.append(vid)
    return ordered


def parse_vacancy_page(html: str, url: str) -> dict | None:
    soup = BeautifulSoup(html, "html.parser")

    h1 = soup.select_one("h1.vacancy-card__title") or soup.select_one(".vacancy-card__title")
    title = h1.get_text(strip=True) if h1 else ""
    if not title:
        return None

    desc_el = soup.select_one('[itemprop="description"]') or soup.select_one(".vacancy-card__description")
    description = desc_el.get_text(" ", strip=True) if desc_el else ""

    skill_nodes = soup.select(".vacancy-card__skills-item")
    skills = ", ".join(s.get_text(strip=True) for s in skill_nodes)

    skills_for_filter = skills if skills.strip() else description[:800]
    if not is_it_vacancy(title, skills_for_filter):
        return None

    company_el = soup.select_one("[itemprop='legalName']") or soup.select_one(".vacancy-company-stats__name")
    company = company_el.get_text(strip=True) if company_el else "Not specified"

    city_el = soup.select_one(".vacancy-requirements__city") or soup.select_one(".vacancy-card__location")
    region = city_el.get_text(strip=True) if city_el else "Russia"

    salary_el = soup.select_one(".vacancy-card__salary")
    salary_text = (
        salary_el.get_text(" ", strip=True).replace("\xa0", " ") if salary_el else "Not specified"
    )

    smin, smax = 0, 0
    base = soup.select_one('span[itemprop="baseSalary"]')
    if base:
        min_meta = base.find("meta", itemprop="minValue")
        max_meta = base.find("meta", itemprop="maxValue")
        if min_meta and min_meta.get("content"):
            try:
                smin = int(float(min_meta["content"]))
            except (TypeError, ValueError):
                pass
        if max_meta and max_meta.get("content"):
            try:
                smax = int(float(max_meta["content"]))
            except (TypeError, ValueError):
                pass

    return {
        "Title": title,
        "Company": company,
        "Salary_Min": smin,
        "Salary_Max": smax,
        "Region": region,
        "Skills_Req": skills or description[:500],
        "Link": url,
        "Salary_Text": salary_text,
    }


def load_existing_links(csv_path: Path) -> set[str]:
    prev = _read_csv_safe(csv_path)
    if prev.empty or "Link" not in prev.columns:
        return set()
    out: set[str] = set()
    for raw in prev["Link"].dropna().astype(str).str.strip():
        out.add(raw)
        out.add(_normalize_vacancy_url(raw))
    return out


_RABOTA_COLUMNS = [
    "Title",
    "Company",
    "Salary_Min",
    "Salary_Max",
    "Region",
    "Skills_Req",
    "Link",
    "Salary_Text",
]


def merge_and_save_rabota_csv(csv_path: Path, new_df: pd.DataFrame) -> pd.DataFrame:
    ensure_storage()
    old = _read_csv_safe(csv_path)
    if old.empty and len(old.columns) == 0:
        old = pd.DataFrame(columns=_RABOTA_COLUMNS)

    if new_df.empty:
        merged = old
    elif old.empty:
        merged = new_df
    else:
        merged = pd.concat([old, new_df], ignore_index=True)

    if not merged.empty:
        merged = merged.drop_duplicates(subset=["Link"], keep="last")
    merged.to_csv(csv_path, index=False, encoding="utf-8-sig")
    return merged


def parse_rabota(
    queries=None,
    max_pages_per_query: int = 5,
    *,
    existing_links: set[str] | None = None,
    csv_path: Path | None = None,
) -> tuple[pd.DataFrame, bool, int]:
    if queries is None:
        queries = SEARCH_QUERIES
    path = csv_path or RABOTA_CSV
    if existing_links is None:
        existing_links = load_existing_links(path)

    session = requests.Session()
    seen_ids: set[str] = set()
    rows: list[dict] = []
    aborted = False
    last_file_row_count = 0

    n_queries = len(queries)
    for qi, q in enumerate(queries):
        rows_at_q_start = len(rows)
        print(f"Parsing: {q}")
        try:
            for page in range(1, max_pages_per_query + 1):
                url = f"{LIST_URL}?query={quote(q)}&page={page}"
                html = _get(url, session)
                if not html:
                    break

                page_ids = collect_vacancy_ids_from_list(html)
                if not page_ids:
                    break

                for vid in page_ids:
                    if vid in seen_ids:
                        continue
                    seen_ids.add(vid)

                    vurl = f"https://www.rabota.ru/vacancy/{vid}/"
                    if vurl in existing_links or _normalize_vacancy_url(vurl) in existing_links:
                        continue

                    vhtml = _get(vurl, session)
                    if not vhtml:
                        continue

                    rec = parse_vacancy_page(vhtml, vurl)
                    if rec:
                        rows.append(rec)

                    time.sleep(1)

                print(f"   Page {page}: +{len(page_ids)} vacancies")
                time.sleep(2)
        except _NETWORK_ERRORS as e:
            print(f"[ABORT] Stopping scrape after network error: {e}")
            aborted = True

        batch = rows[rows_at_q_start:]
        batch_df = pd.DataFrame(batch)
        if not batch_df.empty:
            batch_df = batch_df.drop_duplicates(subset=["Link"])
            merged = merge_and_save_rabota_csv(path, batch_df)
            last_file_row_count = len(merged)
            for link in batch_df["Link"].astype(str).str.strip():
                existing_links.add(link)
                existing_links.add(_normalize_vacancy_url(link))
            print(f"[SAVE] After query {q!r}: +{len(batch_df)} rows → {path} (total {last_file_row_count})")
        else:
            print(f"[SAVE] After query {q!r}: nothing new to append")

        if aborted:
            break

        if qi < n_queries - 1:
            time.sleep(random.uniform(4.0, 9.0))

    if last_file_row_count == 0:
        tail = _read_csv_safe(path)
        last_file_row_count = len(tail)

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.drop_duplicates(subset=["Link"])
    return df, aborted, last_file_row_count


if __name__ == "__main__":
    ensure_storage()
    out = RABOTA_CSV
    existing = load_existing_links(out)
    print(f"Already in CSV (skip by Link): {len(existing)}")

    new_df, aborted, total_in_file = parse_rabota(existing_links=existing, csv_path=out)

    print(f"New rows this run: {len(new_df)}, rows in {out}: {total_in_file}")
    if aborted:
        sys.exit(1)