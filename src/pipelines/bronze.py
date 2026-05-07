import re
from datetime import date, datetime

from src.common.io import write_json
from src.common.paths import BRONZE_DIR
from src.scrapers.emploi_ma_scraper import scrape_emploi_ma_jobs
from src.scrapers.maroc_annonces_scraper import scrape_maroc_annonces_jobs
from src.scrapers.rekrute_scraper import scrape_rekrute_jobs
from src.scrapers.sample_scraper import scrape_sample_jobs


def write_sample_bronze() -> str:
    rows = scrape_sample_jobs()
    output_path = BRONZE_DIR / "sample" / date.today().isoformat() / "offres.json"
    write_json(output_path, rows)
    return str(output_path)


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value or "all").strip("-").lower()
    return cleaned or "all"


def write_rekrute_bronze(max_pages: int = 1, keyword: str = "") -> str:
    rows = scrape_rekrute_jobs(max_pages=max_pages, keyword=keyword)
    if not rows:
        raise RuntimeError(f"Aucune offre collectee depuis Rekrute pour keyword='{keyword or 'all'}'")

    timestamp = datetime.now().strftime("%H%M%S")
    file_name = f"{_slugify(keyword)}_{timestamp}.json"
    output_path = BRONZE_DIR / "rekrute" / date.today().isoformat() / file_name
    write_json(output_path, rows)
    return str(output_path)


def write_emploi_ma_bronze(max_pages: int = 1, keyword: str = "") -> str:
    rows = scrape_emploi_ma_jobs(max_pages=max_pages, keyword=keyword)
    if not rows:
        raise RuntimeError(f"Aucune offre collectee depuis Emploi.ma pour keyword='{keyword or 'all'}'")

    timestamp = datetime.now().strftime("%H%M%S")
    file_name = f"{_slugify(keyword)}_{timestamp}.json"
    output_path = BRONZE_DIR / "emploi_ma" / date.today().isoformat() / file_name
    write_json(output_path, rows)
    return str(output_path)


def write_maroc_annonces_bronze(max_pages: int = 1, keyword: str = "") -> str:
    rows = scrape_maroc_annonces_jobs(max_pages=max_pages, keyword=keyword)
    if not rows:
        raise RuntimeError(f"Aucune offre collectee depuis MarocAnnonces pour keyword='{keyword or 'all'}'")

    timestamp = datetime.now().strftime("%H%M%S")
    file_name = f"{_slugify(keyword)}_{timestamp}.json"
    output_path = BRONZE_DIR / "maroc_annonces" / date.today().isoformat() / file_name
    write_json(output_path, rows)
    return str(output_path)
