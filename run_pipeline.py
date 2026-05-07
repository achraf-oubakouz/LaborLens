import argparse

from src.pipelines.bronze import (
    write_emploi_ma_bronze,
    write_maroc_annonces_bronze,
    write_rekrute_bronze,
    write_sample_bronze,
)
from src.pipelines.gold import silver_to_gold
from src.pipelines.postgres import load_gold_to_postgres
from src.pipelines.silver import all_bronze_to_silver, bronze_to_silver, sources_bronze_to_silver


REAL_SOURCES = ["rekrute", "maroc_annonces"]


def _split_keywords(value: str) -> list[str]:
    return [keyword.strip() for keyword in value.split(",") if keyword.strip()]


def _scrape_keywords(source: str, keywords: list[str], pages: int) -> list[str]:
    writers = {
        "rekrute": write_rekrute_bronze,
        "emploi_ma": write_emploi_ma_bronze,
        "maroc_annonces": write_maroc_annonces_bronze,
    }
    bronze_paths = []

    for keyword in keywords:
        try:
            bronze_paths.append(writers[source](max_pages=pages, keyword=keyword))
        except RuntimeError as exc:
            print(f"WARNING: {exc}")

    return bronze_paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline emploi Maroc Bronze/Silver/Gold")
    parser.add_argument("--sample", action="store_true", help="Utilise les offres exemple")
    parser.add_argument("--source", choices=["sample", "rekrute", "emploi_ma", "maroc_annonces", "all"], default="sample")
    parser.add_argument("--pages", type=int, default=1, help="Nombre de pages a scraper")
    parser.add_argument("--keyword", default="", help="Mot-cle de recherche optionnel")
    parser.add_argument("--keywords", default="", help="Liste de mots-cles separes par des virgules")
    parser.add_argument("--all-bronze", action="store_true", help="Reconstruit Silver/Gold depuis tout Bronze")
    parser.add_argument("--rebuild-only", action="store_true", help="Reconstruit Silver/Gold sans nouveau scraping")
    parser.add_argument("--load-postgres", action="store_true", help="Charge les tables Gold dans PostgreSQL")
    args = parser.parse_args()

    source = "sample" if args.sample else args.source
    bronze_paths = []
    silver_source = None if source == "all" else source

    if args.rebuild_only:
        silver_path = sources_bronze_to_silver(REAL_SOURCES) if source == "all" else all_bronze_to_silver(source=silver_source)
    elif source == "sample":
        bronze_paths.append(write_sample_bronze())
        silver_path = all_bronze_to_silver(source=source) if args.all_bronze else bronze_to_silver(bronze_paths[0])
    elif source in {"rekrute", "emploi_ma", "maroc_annonces"}:
        keywords = _split_keywords(args.keywords) or [args.keyword]
        bronze_paths = _scrape_keywords(source, keywords, args.pages)
        if not bronze_paths:
            raise SystemExit(f"Aucune donnee {source} collectee. Essayez moins de pages ou relancez plus tard.")
        if args.all_bronze or len(bronze_paths) > 1:
            silver_path = all_bronze_to_silver(source=source)
        else:
            silver_path = bronze_to_silver(bronze_paths[0])
    elif source == "all":
        keywords = _split_keywords(args.keywords) or [args.keyword]
        bronze_paths.extend(_scrape_keywords("rekrute", keywords, args.pages))
        bronze_paths.extend(_scrape_keywords("maroc_annonces", [""], args.pages))
        if not bronze_paths:
            raise SystemExit("Aucune donnee collectee. Essayez moins de pages ou relancez plus tard.")
        silver_path = sources_bronze_to_silver(REAL_SOURCES)
    else:
        raise SystemExit(f"Source non supportee: {source}")

    gold_paths = silver_to_gold(silver_path)

    if bronze_paths:
        print("Bronze:")
        for path in bronze_paths:
            print(f"- {path}")
    else:
        print(f"Bronze: reutilisation des fichiers existants pour {source}")
    print(f"Silver: {silver_path}")
    print("Gold:")
    for path in gold_paths:
        print(f"- {path}")

    if args.load_postgres:
        tables = load_gold_to_postgres()
        print("PostgreSQL:")
        for table in tables:
            print(f"- {table}")


if __name__ == "__main__":
    main()
