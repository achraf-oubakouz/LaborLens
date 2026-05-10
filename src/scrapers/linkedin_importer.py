from pathlib import Path

import pandas as pd


DEFAULT_LINKEDIN_CSV = Path("data/imports/linkedin_jobs.csv")

COLUMN_ALIASES = {
    "title": ["title", "job_title", "position"],
    "company": ["company", "company_name", "organization"],
    "city": ["city", "location", "job_location"],
    "sector": ["sector", "industry"],
    "description": ["description", "job_description", "summary"],
    "experience_level": ["experience_level", "seniority", "level"],
    "contract_type": ["contract_type", "employment_type", "job_type"],
    "published_at": ["published_at", "date_posted", "posted_at"],
    "url": ["url", "job_url", "link"],
}


def _pick(row: pd.Series, names: list[str]) -> str:
    for name in names:
        if name in row and pd.notna(row[name]):
            return str(row[name]).strip()
    return ""


def import_linkedin_jobs(csv_path: str | Path = DEFAULT_LINKEDIN_CSV, keyword: str = "") -> list[dict[str, str]]:
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Fichier LinkedIn introuvable: {path}. "
            "Ajoutez un CSV local ou utilisez --linkedin-csv."
        )

    df = pd.read_csv(path)
    df.columns = [column.strip().lower() for column in df.columns]
    rows = []

    for _, row in df.iterrows():
        job = {
            "source": "linkedin",
            "title": _pick(row, COLUMN_ALIASES["title"]),
            "company": _pick(row, COLUMN_ALIASES["company"]),
            "city": _pick(row, COLUMN_ALIASES["city"]),
            "sector": _pick(row, COLUMN_ALIASES["sector"]) or "Non renseigne",
            "description": _pick(row, COLUMN_ALIASES["description"]),
            "experience_level": _pick(row, COLUMN_ALIASES["experience_level"]),
            "contract_type": _pick(row, COLUMN_ALIASES["contract_type"]),
            "published_at": _pick(row, COLUMN_ALIASES["published_at"]),
            "url": _pick(row, COLUMN_ALIASES["url"]),
        }

        if keyword:
            haystack = " ".join([job["title"], job["company"], job["city"], job["description"]]).lower()
            if keyword.lower() not in haystack:
                continue

        rows.append(job)

    return rows
