# DWAV Bonus Assignment

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
