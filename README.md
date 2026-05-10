# IT vacancy analyzer
**IT vacancy analyzer** is a small data pipeline plus a Streamlit dashboard. Scrapers write
per-site CSVs into `storage/`, `scrapping/processing.py` merges them into `storage/vacancies_merged.csv`,
and `app.py` visualizes the result: filters, metrics, bar charts, and salary boxplots. The UI
labels salaries as **RUB** where shown.
**Live app:** https://it-vacancy-analyzer-uqwuec5hdn6x2fpbsw9m5j.streamlit.app/
**Local run:** install dependencies from `requirements.txt`, run the merge script, then
`python -m streamlit run app.py`.

Scrapers collect vacancy listings into `storage/`. `scrapping/processing.py` merges sources into `storage/vacancies_merged.csv`. `app.py` is a Streamlit dashboard over that file.

## Requirements

```bash
pip install -r requirements.txt
```

## Merge CSVs

From the project root:

```bash
python scrapping/processing.py
```

## Streamlit

```bash
python -m streamlit run app.py
```

The app looks for `vacancies_merged.csv` in `storage/` first, then next to `app.py`.

## Scrapers

Run individual modules from the project root so imports resolve, for example:

```bash
python scrapping/habr.py
python scrapping/rabota.py
```
