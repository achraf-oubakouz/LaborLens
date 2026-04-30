import re
from pathlib import Path

import pandas as pd

from src.common.io import read_json
from src.common.paths import CONFIG_DIR, SILVER_DIR


CITY_ALIASES = {
    "casa": "Casablanca",
    "casablanca": "Casablanca",
    "rabat": "Rabat",
    "marrakech": "Marrakech",
    "marrakesh": "Marrakech",
    "tanger": "Tanger",
    "fes": "Fes",
    "fès": "Fes",
    "agadir": "Agadir",
}


def _load_skills() -> list[str]:
    lines = (CONFIG_DIR / "skills.yml").read_text(encoding="utf-8").splitlines()
    return [line.strip()[2:].strip() for line in lines if line.strip().startswith("- ")]


def normalize_city(value: str) -> str:
    cleaned = str(value or "").strip().lower()
    return CITY_ALIASES.get(cleaned, str(value or "").strip().title())


def extract_skills(text: str, skills: list[str]) -> list[str]:
    found = []
    normalized_text = f" {str(text or '').lower()} "
    for skill in skills:
        pattern = r"(?<![\w.+-])" + re.escape(skill.lower()) + r"(?![\w.+-])"
        if re.search(pattern, normalized_text):
            found.append(skill)
    return found


def bronze_to_silver(bronze_path: str | Path) -> str:
    rows = read_json(Path(bronze_path))
    skills = _load_skills()
    df = pd.DataFrame(rows)

    expected_columns = [
        "source",
        "title",
        "company",
        "city",
        "sector",
        "description",
        "experience_level",
        "contract_type",
        "published_at",
        "url",
    ]
    for column in expected_columns:
        if column not in df.columns:
            df[column] = ""

    df = df[expected_columns].copy()
    df["title"] = df["title"].fillna("").str.strip()
    df["company"] = df["company"].fillna("").str.strip()
    df["city"] = df["city"].apply(normalize_city)
    df["sector"] = df["sector"].fillna("Non renseigne").str.strip().str.title()
    df["contract_type"] = df["contract_type"].fillna("Non renseigne").str.strip().str.upper()
    df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce").dt.date
    df["content_length"] = df["description"].fillna("").str.len()
    df["skills"] = df["description"].apply(lambda text: ",".join(extract_skills(text, skills)))

    df = df[df["title"] != ""]
    df = df.drop_duplicates(subset=["source", "title", "company", "city", "url"])

    output_path = SILVER_DIR / "offres_clean.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")
    return str(output_path)
