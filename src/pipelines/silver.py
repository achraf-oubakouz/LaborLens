import re
import unicodedata
from pathlib import Path

import pandas as pd

from src.common.io import read_json
from src.common.paths import BRONZE_DIR, CONFIG_DIR, SILVER_DIR


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

CITY_ALIASES.update(
    {
        "beni mellal-khenifra": "Beni Mellal-Khenifra",
        "casablanca-mohammedia": "Casablanca-Mohammedia",
        "dakhla": "Dakhla",
        "deroua": "Deroua",
        "el jadida": "El Jadida",
        "errachidia": "Errachidia",
        "guelmim": "Guelmim",
        "international": "International",
        "laayoune": "Laayoune",
        "marrakech-safi": "Marrakech-Safi",
        "meknes": "Meknes",
        "mohammedia": "Mohammedia",
        "nador": "Nador",
        "nouaceur": "Nouaceur",
        "oujda": "Oujda",
        "rabat-sale-kenitra": "Rabat-Sale-Kenitra",
        "safi": "Safi",
        "sale": "Sale",
        "settat": "Settat",
        "tanger-tetouan-al hoceima": "Tanger-Tetouan-Al Hoceima",
        "temara": "Temara",
        "tetouan": "Tetouan",
        "tout le maroc": "Tout Le Maroc",
    }
)


def _load_skills() -> list[str]:
    lines = (CONFIG_DIR / "skills.yml").read_text(encoding="utf-8").splitlines()
    return [line.strip()[2:].strip() for line in lines if line.strip().startswith("- ")]


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    return normalized.encode("ascii", "ignore").decode("ascii")


def normalize_city(value: str) -> str:
    raw_value = str(value or "").strip()
    cleaned = _strip_accents(raw_value).lower()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return CITY_ALIASES.get(cleaned, _strip_accents(raw_value).title())


def _title_from_slug(value: str) -> str:
    cleaned = re.sub(r"[-_]+", " ", value or "").strip()
    return cleaned.title()


def infer_company(row: pd.Series) -> str:
    company = str(row.get("company") or "").strip()
    if company and company.lower() not in {"nan", "n/a", "na"}:
        return company

    source = str(row.get("source") or "").strip()
    url = str(row.get("url") or "").strip()

    if source == "rekrute":
        match = re.search(r"-recrutement-(.*?)(?:-[a-z]+)?-\d+\.html", url)
        if match:
            slug = re.sub(r"\b(casablanca|rabat|marrakech|tanger|fes|agadir|sale|kenitra)\b$", "", match.group(1))
            return _title_from_slug(slug)

    return "Non renseigne"


def extract_skills(text: str, skills: list[str]) -> list[str]:
    found = []
    normalized_text = f" {str(text or '').lower()} "
    for skill in skills:
        pattern = r"(?<![\w.+-])" + re.escape(skill.lower()) + r"(?![\w.+-])"
        if re.search(pattern, normalized_text):
            found.append(skill)
    return found


def _write_rows_to_silver(rows: list[dict]) -> str:
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
    df["company"] = df.apply(infer_company, axis=1)
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


def bronze_to_silver(bronze_path: str | Path) -> str:
    return _write_rows_to_silver(read_json(Path(bronze_path)))


def all_bronze_to_silver(source: str | None = None) -> str:
    root = BRONZE_DIR / source if source else BRONZE_DIR
    bronze_files = sorted(root.glob("**/*.json"))
    if not bronze_files:
        raise FileNotFoundError(f"Aucun fichier Bronze trouve dans {root}")

    rows = []
    for bronze_file in bronze_files:
        rows.extend(read_json(bronze_file))

    return _write_rows_to_silver(rows)


def sources_bronze_to_silver(sources: list[str]) -> str:
    bronze_files = []
    for source in sources:
        source_root = BRONZE_DIR / source
        bronze_files.extend(sorted(source_root.glob("**/*.json")))

    if not bronze_files:
        joined = ", ".join(sources)
        raise FileNotFoundError(f"Aucun fichier Bronze trouve pour les sources: {joined}")

    rows = []
    for bronze_file in bronze_files:
        rows.extend(read_json(bronze_file))

    return _write_rows_to_silver(rows)
