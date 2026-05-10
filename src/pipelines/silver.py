import re
from datetime import date, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd

from src.common.io import read_avro, read_json
from src.common.locations import extract_city
from src.common.paths import BRONZE_DIR, CONFIG_DIR, SILVER_DIR
from src.common.storage import put_lake_file
from src.common.versions import SILVER_TRANSFORM_VERSION, SKILLS_EXTRACTION_VERSION


def _load_skills() -> list[str]:
    lines = (CONFIG_DIR / "skills.yml").read_text(encoding="utf-8").splitlines()
    return [line.strip()[2:].strip() for line in lines if line.strip().startswith("- ")]


def normalize_city(value: str) -> str:
    return extract_city(value)


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


def normalize_required_text(value: str, default: str = "Non renseigne") -> str:
    cleaned = str(value or "").strip()
    if not cleaned or cleaned.lower() in {"nan", "none", "n/a", "na"}:
        return default
    return cleaned


def extract_skills(text: str, skills: list[str]) -> list[str]:
    found = []
    normalized_text = f" {str(text or '').lower()} "
    for skill in skills:
        pattern = r"(?<![\w.+-])" + re.escape(skill.lower()) + r"(?![\w.+-])"
        if re.search(pattern, normalized_text):
            found.append(skill)
    return found


def _read_bronze_file(path: Path) -> list[dict]:
    if path.suffix == ".avro":
        return read_avro(path)
    if path.suffix == ".json":
        return read_json(path)
    raise ValueError(f"Format Bronze non supporte: {path}")


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
    df["sector"] = df["sector"].apply(normalize_required_text).str.title()
    df["contract_type"] = df["contract_type"].apply(normalize_required_text).str.upper()
    df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce").dt.date
    df["content_length"] = df["description"].fillna("").str.len()
    df["skills"] = df["description"].apply(lambda text: ",".join(extract_skills(text, skills)))
    df["silver_transform_version"] = SILVER_TRANSFORM_VERSION
    df["skills_extraction_version"] = SKILLS_EXTRACTION_VERSION

    df = df[df["title"] != ""]
    df = df.drop_duplicates(subset=["source", "title", "company", "city", "url"])

    output_path = SILVER_DIR / "offres_clean.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    df.to_csv(SILVER_DIR / "offres_clean.csv", index=False, encoding="utf-8")

    partition_date = date.today().isoformat()
    run_id = f"run-{datetime.now().strftime('%H%M%S')}-{uuid4().hex[:8]}"
    partition_dir = SILVER_DIR / "jobs" / f"date={partition_date}"
    partition_dir.mkdir(parents=True, exist_ok=True)
    partition_path = partition_dir / f"part-{run_id}.parquet"
    df.to_parquet(partition_path, index=False)
    put_lake_file(partition_path, f"silver/jobs/date={partition_date}/{partition_path.name}")
    return str(output_path)


def bronze_to_silver(bronze_path: str | Path) -> str:
    return _write_rows_to_silver(_read_bronze_file(Path(bronze_path)))


def all_bronze_to_silver(source: str | None = None) -> str:
    root = BRONZE_DIR / source if source else BRONZE_DIR
    bronze_files = sorted(root.glob("**/*.avro")) or sorted(root.glob("**/*.json"))
    if not bronze_files:
        raise FileNotFoundError(f"Aucun fichier Bronze trouve dans {root}")

    rows = []
    for bronze_file in bronze_files:
        rows.extend(_read_bronze_file(bronze_file))

    return _write_rows_to_silver(rows)


def sources_bronze_to_silver(sources: list[str]) -> str:
    bronze_files = []
    for source in sources:
        source_root = BRONZE_DIR / source
        source_files = sorted(source_root.glob("**/*.avro")) or sorted(source_root.glob("**/*.json"))
        bronze_files.extend(source_files)

    if not bronze_files:
        joined = ", ".join(sources)
        raise FileNotFoundError(f"Aucun fichier Bronze trouve pour les sources: {joined}")

    rows = []
    for bronze_file in bronze_files:
        rows.extend(_read_bronze_file(bronze_file))

    return _write_rows_to_silver(rows)
