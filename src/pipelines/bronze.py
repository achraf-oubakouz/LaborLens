import re
from datetime import date, datetime
from uuid import uuid4

from src.common.io import write_avro, write_json
from src.common.paths import BRONZE_DIR
from src.common.storage import put_lake_file
from src.scrapers.emploi_ma_scraper import scrape_emploi_ma_jobs
from src.scrapers.maroc_annonces_scraper import scrape_maroc_annonces_jobs
from src.scrapers.rekrute_scraper import scrape_rekrute_jobs
from src.scrapers.sample_scraper import scrape_sample_jobs


def _write_bronze_rows(source: str, rows: list[dict], run_id: str | None = None) -> str:
    partition_date = date.today().isoformat()
    run = run_id or f"run-{datetime.now().strftime('%H%M%S')}-{uuid4().hex[:8]}"
    output_dir = BRONZE_DIR / source / partition_date / run
    write_json(output_dir / "offres.json", rows)
    output_path = output_dir / "offers.avro"
    write_avro(output_path, rows)
    put_lake_file(output_path, f"bronze/{source}/{partition_date}/{run}/offers.avro")
    return str(output_path)


def write_sample_bronze() -> str:
    rows = scrape_sample_jobs()
    return _write_bronze_rows("sample", rows)


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value or "all").strip("-").lower()
    return cleaned or "all"


def write_rekrute_bronze(max_pages: int = 1, keyword: str = "") -> str:
    rows = scrape_rekrute_jobs(max_pages=max_pages, keyword=keyword)
    if not rows:
        raise RuntimeError(f"Aucune offre collectee depuis Rekrute pour keyword='{keyword or 'all'}'")

    return _write_bronze_rows("rekrute", rows, run_id=f"{_slugify(keyword)}-{datetime.now().strftime('%H%M%S')}")


def write_emploi_ma_bronze(max_pages: int = 1, keyword: str = "") -> str:
    rows = scrape_emploi_ma_jobs(max_pages=max_pages, keyword=keyword)
    if not rows:
        raise RuntimeError(f"Aucune offre collectee depuis Emploi.ma pour keyword='{keyword or 'all'}'")

    return _write_bronze_rows("emploi_ma", rows, run_id=f"{_slugify(keyword)}-{datetime.now().strftime('%H%M%S')}")


def write_maroc_annonces_bronze(max_pages: int = 1, keyword: str = "") -> str:
    rows = scrape_maroc_annonces_jobs(max_pages=max_pages, keyword=keyword)
    if not rows:
        raise RuntimeError(f"Aucune offre collectee depuis MarocAnnonces pour keyword='{keyword or 'all'}'")

    return _write_bronze_rows(
        "maroc_annonces",
        rows,
        run_id=f"{_slugify(keyword)}-{datetime.now().strftime('%H%M%S')}",
    )
