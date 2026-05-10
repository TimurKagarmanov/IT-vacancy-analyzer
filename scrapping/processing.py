from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

try:
    from scrapping.storage_paths import STORAGE_DIR, ensure_storage
except ImportError:
    from storage_paths import STORAGE_DIR, ensure_storage


DEFAULT_FILES = {
    "wwr": STORAGE_DIR / "wwr_vacancies.csv",
    "remoteok": STORAGE_DIR / "remoteok_vacancies.csv",
    "trudvsem": STORAGE_DIR / "trudvsem_vacancies.csv",
    "rabota": STORAGE_DIR / "rabota_vacancies.csv",
    "habr": STORAGE_DIR / "habr_vacancies_detailed.csv",
    "superjob": STORAGE_DIR / "superjob_vacancies.csv",
}

OUTPUT_DEFAULT = STORAGE_DIR / "vacancies_merged.csv"

_BAD_SALARY_TEXT_EXACT = frozenset(
    {
        "",
        "nan",
        "none",
        "not specified",
        "не указана",
        "не указано",
        "не указан",
        "по договоренности",
        "по договорённости",
    }
)

_SUPERJOB_DOUBLE_ORIGIN = re.compile(
    r"^https?://(?:www\.)?superjob\.ru(https://[^\s]+)$",
    re.IGNORECASE,
)


def _normalize_vacancy_url(url: object) -> str:
    u = "" if url is None or pd.isna(url) else str(url).strip()
    if not u:
        return u
    m = _SUPERJOB_DOUBLE_ORIGIN.match(u)
    return m.group(1) if m else u


SPECIALTY_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("Full Stack", (
        "full stack", "fullstack", "full-stack", "fullstack developer",
        "фулстек", "фул стек", "фул-стек", "полный стек", "фуллстек",
        "full-stack engineer", "fullstack engineer", "full stack engineer",
        "fullstack разработчик", "full stack разработчик",
    )),
    ("Data Science / ML", (
        "data scientist", "data science", "machine learning", "machine-learning",
        " ml ", "ml-engineer", "ml engineer", "mle ", "deep learning",
        "deep-learning", "reinforcement learning", "computer vision",
        "computer-vision", "nlp ", " nlp", "natural language",
        " ai ", "ai engineer", "artificial intelligence", "искусственн интеллект",
        "искусственный интеллект", "нейросет", "нейронн сет", "машинн обучен",
        "машинное обучение", "специалист по ml", "специалист по машинному",
        "учёный по данным", "ученый по данным", "research scientist",
        "applied scientist", "cv engineer", "nlp engineer",
        "pytorch", "tensorflow", "keras", "scikit-learn", "sklearn",
        "llm ", " large language", "generative ai", "genai",
        "mlops", "mlopps", " mloops", "research engineer", "r&d engineer",
        "data mining", "predictive model", "рекомендательн систем",
    )),
    ("Data Engineer", (
        "data engineer", "data-engineer", "инженер данных", "инженер по данным",
        "инженер данных и", "data architect", "архитектор данных",
        "архитектор хранилищ", "etl", "elt developer", "data warehouse", "dwh",
        "apache spark", " spark ", " spark,", " spark.", "apache kafka", "kafka ",
        "hadoop", "hdfs", "airflow", "apache airflow", "dbt ", "dbt,", "snowflake",
        "databricks", "big data", "больших данных", "инженер big data",
        "bigdata", "хранилищ данных", "data lake", "data pipeline",
        "pipeline engineer", "streaming data", "real-time data",
        "data platform", "data infrastructure", "инженер по инфраструктуре данных",
    )),
    ("Data Analyst / BI", (
        "data analyst", "data-analyst", "аналитик данных", "аналитик по данным",
        "bi developer", "bi engineer", "bi-разработчик", "bi разработчик",
        "business intelligence", "power bi", "tableau", "looker", "qlik",
        "метрик", "продуктовый аналитик", "product analyst", "crm-аналитик",
        "crm аналитик", "dba analyst", " отчетности ", " дашборд ", "дашборд",
        "data visualization", "аналитик отчетности", "аналитик отчётности",
        "старший аналитик данных", "junior data analyst", "sql analyst",
        "excel ", "google analytics", "web analyst", "маркетинговый аналитик",
    )),
    ("Database / DBA", (
        "database administrator", "database admin", "dba ", " dba",
        "администратор баз данных", "администратор бд", "админ бд",
        "администратор субд", "database engineer", "db engineer",
        "postgres dba", "postgresql dba", "oracle dba", "mysql dba",
        "ms sql dba", "sql server dba", "mongodb admin", "redis admin",
        "database reliability", "database operations", "операционист бд",
    )),
    ("Security", (
        "security engineer", "application security", "appsec", "cybersecurity",
        "cyber security", "information security", "infosec", "iso 27001",
        "pentest", "penetration test", "пентест", "пентестер", "red team",
        "blue team", "кибербезопасн", "кибер безопас", "информационной безопасности",
        " специалист по иб", " специалист по информационной безопасности",
        "инженер по иб", "soc analyst", "security analyst", "vulnerability",
        "governance risk", "grc ", "ciso", "devsecops",
    )),
    ("DevOps / SRE", (
        "devops", "dev ops", "devops engineer", "devops-инженер", "sre",
        "site reliability", "reliability engineer", "kubernetes", "k8s",
        "docker", "ansible", "terraform", "pulumi", "jenkins", "gitlab ci",
        "github actions", "ci/cd", "cicd", "continuous integration",
        "continuous deployment", "platform engineer", "cloud engineer",
        "cloud architect", "aws engineer", "azure devops", "gcp engineer",
        "google cloud engineer", "облачн инженер", "инженер облач",
        "девапс", "девопс", "инженер devops", "инженер по devops",
        "администратор kubernetes", "администратор ci", "helm ", "argo cd",
        "istio", "prometheus", "grafana", "observability",
    )),
    ("Network", (
        "network engineer", "network administrator", "network admin",
        "сетевой инженер", "сетевой администратор", " ccna ", " ccnp ", " ccie ",
        "juniper", "cisco ", "администратор сет", "сетевых технологий",
        "network security", "сетевой специалист", "инженер связи",
        "wlan", "voip engineer", "sdn ", "nfv ",
    )),
    ("SysAdmin", (
        "system administrator", "systems administrator", "sysadmin",
        "системный администратор", "админ ", " админ", "администратор сервер",
        "администратор linux", "администратор windows", "linux administrator",
        "windows administrator", "vmware", "hyper-v", "active directory",
        "администратор инфраструктуры", "инженер по серверам",
    )),
    ("IT Support", (
        "support engineer", "helpdesk", "help desk", "help-desk", "technical support",
        "tech support", "it support", "it technician", "it техник",
        "техподдержка", "служба поддержки", "специалист поддержки",
        "специалист технической поддержки", "техническая поддержка",
        "1-я линия", "1 линия поддержки", "2 линия поддержки", "desktop support",
        "service desk", "l1 support", "l2 support", "l3 support",
        "специалист сервисного стола", "customer support engineer",
    )),
    ("QA / Testing", (
        "qa engineer", " qa ", "qa automation", "quality assurance", "aq engineer",
        "aqe ", "sdet", "software development engineer in test",
        "test engineer", "software test", "testing engineer", "automation qa",
        "manual qa", "тестировщик", "инженер по тестированию", "инженер по качеству",
        "контроль качества по", "автотестировщик", "автоматизация тест",
        "manual testing", "автоматизатор тестирования", "qa lead", "head of qa",
        "selenium", "cypress", "playwright", "pytest", "junit", "postman",
        "performance test", "нагрузочн тест", "инженер по нагрузочному",
    )),
    ("Embedded / IoT", (
        "embedded", "embedded software", "embedded linux", "firmware",
        "iot engineer", "iot ", "rtos", "микроконтроллер", "встроен",
        "прошивк", "bare metal", "stm32", "arduino", "raspberry pi",
        "fpga", "vhdl", "verilog", "hardware engineer", "аппаратн разработчик",
    )),
    ("Game Development", (
        "game developer", "game designer", "gameplay", "unity developer",
        "unity ", "unreal engine", "unreal ", "ue4", "ue5", "геймдев",
        "разработчик игр", "игровых проектов", "game programmer",
    )),
    ("Blockchain / Web3", (
        "blockchain", "web3", "solidity", "smart contract", "crypto engineer",
        "defi", "nft ", "блокчейн", "разработчик solidity", "rust blockchain",
    )),
    ("ERP / 1C / SAP", (
        "1с", "1с:", "1c ", "1c:", "программист 1с", "разработчик 1с",
        "инженер 1с", " sap ", "sap-", "sap/", "консультант sap", "sap consultant",
        "erp ", "erp-", "erp/", "внедрен erp", "erp разработчик",
        "dynamics", "axapta", "microsoft dynamics", "oracle ebs", "oracle erp",
    )),
    ("Mobile", (
        "mobile developer", "mobile engineer", "ios developer", "android developer",
        "swift developer", "swiftui", " swift ", "kotlin developer", " kotlin ",
        "flutter", "react native",
        "react-native", "мобильн разработчик", "разработчик ios",
        "разработчик android", "разработчик под ios", "разработчик под android",
        "xamarin", "maui ", ".net maui", "ionic", "cordova", "capacitor",
        "watchos", "tvos", "ipad os",
    )),
    ("Backend", (
        "backend", "back-end", "back end", "server-side", "serverside",
        "бэкенд", "бекенд", "бэк-енд", "серверн разработчик",
        " разработчик api ", "api developer", " микросервис", "microservice",
        "spring boot", "spring ", "django", "fastapi", "flask", "tornado",
        "node.js", "nodejs", "node ", "express.js", "nest.js", "nestjs",
        ".net backend", "asp.net", "laravel", "symfony", "ruby on rails",
        " rails ", "rails developer", "gin framework", "go echo", "go fiber",
        "grpc", "graphql server", "kafka consumer", "event-driven",
        "go developer", " golang ", " go ", " rust backend", "php backend",
    )),
    ("UX / UI", (
        "ux designer", "ui designer", "ux/ui", "ui/ux", "ux ui", "product designer",
        "ux researcher", "ui artist", "user experience", " ux ",
        " дизайнер интерфейс", "дизайнер ux", "дизайнер ui", "дизайнер продукт",
        "графический дизайнер", "графический дизайнер интерфейс", " figma ",
        "sketch ", "wireframe", "прототипирован", "interaction designer",
        "motion designer", "visual designer", "brand designer", "иллюстратор ui",
        "ui engineer", "ux engineer", "design system", "дизайн систем",
    )),
    ("Frontend", (
        "frontend", "front-end", "front end", " react ", " react,", "react.js",
        " vue ", "vue.js", "nuxt", " angular ", "angularjs", "next.js", "nextjs",
        "svelte", "sveltekit", "webpack", "vite ", "parcel ", "rollup",
        "фронтенд", "фронт-енд", "фронт разработчик", "верстальщик",
        "верстка", " html ", " css ", "html/css", "scss", "sass", "less ",
        "tailwind", "bootstrap", "material ui", "mui ", "chakra", "styled-components",
        "typescript", "javascript", " js ", "d3.js", " d3 ", "chart.js",
        "ember.js", "backbone", "jquery", "spa ", "single page",
        "web ui", "client-side", "клиентск разработчик", "frontend engineer",
    )),
    ("Technical Writer", (
        "technical writer", "технический писатель", "documentation engineer",
        "технический автор", "написан документации", "technical author",
        "developer advocate", "devrel", "developer relations",
    )),
    ("Product", (
        "product manager", "product owner", "продакт-менеджер", "продакт менеджер",
        "продуктовый менеджер", "менеджер продукта", "руководитель продукта",
        "product lead", "cpo ", "chief product", "vp product", "head of product",
        "associate product manager", "apm ", "product marketing",
    )),
    ("Project Manager", (
        "project manager", "project management", "проджект-менеджер",
        "программный менеджер", "менеджер проектов", "руководитель проектов",
        "project lead", "project coordinator", "scrum master", "scrum-master",
        " agile coach", "agile коуч", "delivery manager", "координатор проектов",
        "release manager", "program manager", "портфель проектов",
        "pmp ", " prince2", "safe agile",
    )),
    ("Business Analyst", (
        "business analyst", "business analytics", "бизнес-аналитик", "бизнес аналитик",
        "системный аналитик", "аналитик требований", "анализ требований",
        " ba ", "функциональный аналитик", "аналитик интеграц",
        "аналитик процессов", "process analyst", "data steward",
    )),
    ("Architect / Tech Lead", (
        "solution architect", "software architect", "enterprise architect",
        "technical architect", "архитект", "архитектор решений",
        "архитектор приложений", "tech lead", "technical lead", "team lead",
        "teamlead", "тимлид", "тим лид", "ведущий разработчик", "lead developer",
        "engineering lead", "staff engineer", "principal engineer",
        "главный архитект", "ведущий архитект", "главный инженер",
        "engineering manager", "head of engineering", "r&d lead",
    )),
    ("IT Management", (
        "it manager", "it director", "it head", "директор по ит",
        "руководитель ит", "начальник ит", " cto ", "chief technology",
        "технический директор", "chief information officer", "cio ",
        "vp engineering", "vp of engineering", "директор по технологиям",
        "руководитель направления ит", "it officer", "head of it",
    )),
    ("Marketing / Growth (tech)", (
        "growth engineer", "growth hacker", "marketing engineer",
        "performance marketing", "marketing technologist", "crm маркетолог tech",
        "marketing automation", "seo engineer", "sem specialist tech",
    )),
    ("IT / Digital (general)", (
        " it ", " ит ", "ит-", "-ит", "ит специалист", "специалист ит",
        "специалист по ит", "инженер ит", "инженер по ит", "it specialist",
        "it analyst", "it engineer", "it developer", "it programmer",
        "информационных технологий", "информационные технологии",
        "информационных систем", "информационные системы",
        "цифровизации", "цифровых технологий", "цифров трансформац",
        "специалист по информационным системам",
        "специалист по информационным технологиям",
        "digital transformation", "chief digital", "digital officer",
        "специалист ит", "специалист информационных технологий",
    )),
    ("Software Engineer", (
        "software engineer", "software developer", "sw engineer", "swe ",
        "developer", "программист", "разработчик", "инженер-программист",
        "инженер программист", "ведущий программист", "старший разработчик",
        "junior developer", "middle developer", "senior developer",
        "инженер по разработке", "разработчик по", "разработчик программного",
        "web developer", "веб-разработчик", "веб разработчик",
        "software development", "coding ", "кодер", "coder",
        " python ", " java ", " golang ", " go lang ", " c++ ", " cpp ",
        " c# ", " csharp ", ".net ", " javascript ", " js ", " php ", " ruby ",
        " rust ", " scala ", " kotlin ", " swift ", " perl ", "haskell",
        "elixir", "clojure", "typescript", "delphi", "objective-c",
        "postgresql", "postgres ", "mongodb", "redis ", "mysql", "mariadb",
        "oracle plsql", "t-sql", "pl/sql", "sql developer", "oracle developer",
        "sharepoint developer", "salesforce developer", "mendix", "outsystems",
    )),
]

OTHER_SPECIALTY = "Other"


def _match_specialty(blob: object) -> str:
    if not isinstance(blob, str):
        return OTHER_SPECIALTY
    s = blob.strip().lower()
    if len(s) < 2:
        return OTHER_SPECIALTY
    t = " " + re.sub(r"\s+", " ", s) + " "
    for label, patterns in SPECIALTY_RULES:
        for p in patterns:
            if p in t:
                return label
    return OTHER_SPECIALTY


def _skills_for_match(skills: object) -> str:
    if not isinstance(skills, str) or not skills.strip():
        return ""
    s = skills.lower()
    s = s.replace("‑", "-").replace("–", "-").replace("—", "-")
    s = re.sub(r"[,;/|\n]+", " ", s)
    s = re.sub(r"[\u00a0\t]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def resolve_specialty(title: object, skills: object) -> str:
    parts: list[str] = []
    if isinstance(title, str) and title.strip():
        parts.append(title.strip())
    if isinstance(skills, str) and skills.strip():
        parts.append(skills.strip())
    if not parts:
        return OTHER_SPECIALTY
    merged = " ".join(parts)
    blob = _skills_for_match(merged)
    if not blob:
        return OTHER_SPECIALTY
    return _match_specialty(blob)


def is_it_vacancy(title: object, skills: object) -> bool:
    return resolve_specialty(title, skills) != OTHER_SPECIALTY


def infer_specialty(title: object) -> str:
    return _match_specialty(title if isinstance(title, str) else "")


def _read_csv_safe(path: Path) -> pd.DataFrame:
    if not path.exists():
        print(f"[WARN] Missing file: {path.name}, skip.")
        return pd.DataFrame()
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except Exception as e:
        print(f"[WARN] Read error {path.name}: {e}")
        return pd.DataFrame()


def _fmt_salary(min_val: object, max_val: object) -> str:
    mn = pd.to_numeric(min_val, errors="coerce")
    mx = pd.to_numeric(max_val, errors="coerce")
    has_min = pd.notna(mn) and mn != 0
    has_max = pd.notna(mx) and mx != 0

    if has_min and has_max:
        return f"{int(mn)} – {int(mx)}"
    if has_min:
        return f"from {int(mn)}"
    if has_max:
        return f"to {int(mx)}"
    return "Not specified"


def _salary_mid_from_numbers(sm: object, sx: object) -> float | pd.NA:
    sm = pd.to_numeric(sm, errors="coerce")
    sx = pd.to_numeric(sx, errors="coerce")
    both = pd.notna(sm) and pd.notna(sx) and sm > 0 and sx > 0
    if both:
        return float((sm + sx) / 2)
    if pd.notna(sm) and sm > 0:
        return float(sm)
    if pd.notna(sx) and sx > 0:
        return float(sx)
    return pd.NA


def _guess_mid_from_text(text: object) -> float | pd.NA:
    if not isinstance(text, str):
        return pd.NA
    s = text.replace("\u202f", " ").replace("\xa0", " ")
    raw: list[int] = []
    for m in re.finditer(r"\d[\d\s]*", s):
        chunk = re.sub(r"\D", "", m.group(0))
        if not chunk:
            continue
        raw.append(int(chunk))
    salary_like = [n for n in raw if n >= 1000]
    if not salary_like:
        salary_like = [n for n in raw if 100 <= n < 1000]
    salary_like = [n for n in salary_like if not (1900 <= n <= 2030)]
    if not salary_like:
        return pd.NA
    lo = min(salary_like)
    hi = max(salary_like)
    return float((lo + hi) / 2)


def _row_has_meaningful_salary(row: pd.Series) -> bool:
    sm = pd.to_numeric(row.get("salary_min"), errors="coerce")
    sx = pd.to_numeric(row.get("salary_max"), errors="coerce")
    num_ok = (pd.notna(sm) and sm > 0) or (pd.notna(sx) and sx > 0)

    txt_raw = row.get("salary_text")
    txt = "" if txt_raw is None or pd.isna(txt_raw) else str(txt_raw).strip().lower()
    bad_exact = txt in _BAD_SALARY_TEXT_EXACT
    bad_pattern = (
        bool(re.search(r"не\s*указ", txt))
        or ("not specified" in txt)
        or ("по договоренности" in txt)
        or ("по договорённости" in txt)
    )
    text_has_digits = bool(re.search(r"\d{4,}", re.sub(r"\s+", "", txt)))

    text_ok = len(txt) > 3 and not bad_exact and not bad_pattern and text_has_digits

    return bool(num_ok or text_ok)


def _combine_skills(row: pd.Series) -> str:
    parts: list[str] = []
    skip = {"nan", "not specified", "не указано", "не указана"}
    for col in ("skills", "requirements_text"):
        if col in row.index and pd.notna(row[col]):
            s = str(row[col]).strip()
            if s and s.lower() not in skip:
                parts.append(s)
    return " | ".join(parts)


def normalize_generic(df: pd.DataFrame, source_name: str, mapping: dict) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    res = pd.DataFrame(index=df.index)
    res["source"] = source_name

    for target_col, source_col in mapping.items():
        if source_col in df.columns:
            res[target_col] = df[source_col]
        else:
            res[target_col] = pd.NA

    s_min = pd.to_numeric(res.get("salary_min"), errors="coerce")
    s_max = pd.to_numeric(res.get("salary_max"), errors="coerce")

    if "salary_text" not in res.columns or res["salary_text"].isna().all():
        res["salary_text"] = [_fmt_salary(mn, mx) for mn, mx in zip(s_min, s_max)]

    return res


def _finalize_frame(out: pd.DataFrame) -> pd.DataFrame:
    df = out.copy()

    df["title"] = df["title"].astype(str).str.strip()
    df["company"] = df["company"].fillna("").astype(str).str.strip().replace({"": "Unknown"})

    loc = df.get("location", pd.Series(pd.NA, index=df.index))
    loc = loc.fillna("").astype(str).str.strip()
    loc = loc.mask(loc.str.lower().isin({"", "nan", "none"}), "Unknown")
    df["location"] = loc

    df["salary_min"] = pd.to_numeric(df["salary_min"], errors="coerce")
    df["salary_max"] = pd.to_numeric(df["salary_max"], errors="coerce")

    mids = [_salary_mid_from_numbers(sm, sx) for sm, sx in zip(df["salary_min"], df["salary_max"], strict=False)]
    df["salary_mid"] = pd.Series(mids, dtype="Float64")

    guess_mask = df["salary_mid"].isna()
    if guess_mask.any():
        for idx in df.index[guess_mask]:
            g = _guess_mid_from_text(df.at[idx, "salary_text"])
            if pd.notna(g):
                df.at[idx, "salary_mid"] = g

    df["skills"] = df.apply(_combine_skills, axis=1)
    df["specialty"] = df.apply(lambda r: resolve_specialty(r["title"], r["skills"]), axis=1)

    before_other = len(df)
    df = df[df["specialty"] != OTHER_SPECIALTY].copy()
    dropped_other = before_other - len(df)
    if dropped_other:
        print(f"   Dropped '{OTHER_SPECIALTY}' specialty rows: {dropped_other}")

    pub = pd.to_datetime(df.get("published_at"), errors="coerce")
    df["published_at"] = pd.NA
    df.loc[pub.notna(), "published_at"] = pub.loc[pub.notna()].dt.strftime("%Y-%m-%d")

    if df["salary_mid"].notna().any():
        cap_hi = float(df["salary_mid"].quantile(0.995))
        df = df[df["salary_mid"].isna() | (df["salary_mid"] <= cap_hi)]

    cols = [
        "source",
        "title",
        "company",
        "location",
        "salary_min",
        "salary_max",
        "salary_mid",
        "salary_text",
        "skills",
        "specialty",
        "published_at",
        "url",
    ]
    return df[cols]


def merge_all() -> pd.DataFrame:
    configs = {
        "wwr": {
            "title": "Title",
            "company": "Company",
            "location": "Location",
            "salary_text": "Salary",
            "url": "Link",
        },
        "remoteok": {
            "title": "Title",
            "company": "Company",
            "location": "Location",
            "salary_min": "Salary_Min",
            "salary_max": "Salary_Max",
            "skills": "Skills",
            "url": "Link",
        },
        "trudvsem": {
            "title": "Title",
            "company": "Company",
            "location": "Region",
            "salary_min": "Salary_Min",
            "salary_max": "Salary_Max",
            "requirements_text": "Skills_Req",
            "url": "Link",
        },
        "rabota": {
            "title": "Title",
            "company": "Company",
            "location": "Region",
            "salary_min": "Salary_Min",
            "salary_max": "Salary_Max",
            "requirements_text": "Skills_Req",
            "salary_text": "Salary_Text",
            "published_at": "Date",
            "url": "Link",
        },
        "habr": {
            "title": "Title",
            "company": "Company",
            "salary_text": "Salary",
            "skills": "Skills",
            "published_at": "Date",
            "url": "Link",
        },
        "superjob": {
            "title": "Title",
            "company": "Company",
            "location": "Region",
            "salary_text": "Salary",
            "url": "Link",
        },
    }

    frames: list[pd.DataFrame] = []
    for source, path in DEFAULT_FILES.items():
        raw_df = _read_csv_safe(path)
        if not raw_df.empty:
            frames.append(normalize_generic(raw_df, source, configs[source]))

    if not frames:
        print("[ERROR] No input data to merge.")
        return pd.DataFrame()

    out = pd.concat(frames, ignore_index=True)

    out["url"] = out["url"].map(_normalize_vacancy_url)
    out = out[out["url"].str.startswith("http") & (out["url"].str.len() > 12)]

    out["title"] = out["title"].astype(str).str.strip()
    out = out[out["title"].str.len() >= 5]

    before_sal = len(out)
    out = out.loc[out.apply(_row_has_meaningful_salary, axis=1)].copy()
    print(f"   After salary filter: {len(out)} (was {before_sal})")

    out = _finalize_frame(out)

    before_mid = len(out)
    out = out[out["salary_mid"].notna()].copy()
    print(f"   Rows with salary_mid: {len(out)} (was {before_mid})")

    before_dup = len(out)
    out = out.drop_duplicates(subset=["url"], keep="first")
    out = out.drop_duplicates(subset=["title", "company"], keep="first")
    print(f"   After dedup: {len(out)} (was {before_dup})")

    print("[OK] Merge complete.")
    return out


def main() -> None:
    ensure_storage()
    merged = merge_all()
    if merged.empty:
        print("[WARN] Empty output, CSV not written.")
        return
    merged.to_csv(OUTPUT_DEFAULT, index=False, encoding="utf-8-sig")
    print(f"[SAVE] {OUTPUT_DEFAULT} ({len(merged)} rows)")


if __name__ == "__main__":
    main()
