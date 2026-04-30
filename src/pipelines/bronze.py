from datetime import date

from src.common.io import write_json
from src.common.paths import BRONZE_DIR
from src.scrapers.rekrute_scraper import scrape_rekrute_jobs
from src.scrapers.sample_scraper import scrape_sample_jobs


def write_sample_bronze() -> str:
    rows = scrape_sample_jobs()
    output_path = BRONZE_DIR / "sample" / date.today().isoformat() / "offres.json"
    write_json(output_path, rows)
    return str(output_path)


def write_rekrute_bronze(max_pages: int = 1, keyword: str = "") -> str:
    rows = scrape_rekrute_jobs(max_pages=max_pages, keyword=keyword)
    output_path = BRONZE_DIR / "rekrute" / date.today().isoformat() / "offres.json"
    write_json(output_path, rows)
    return str(output_path)
