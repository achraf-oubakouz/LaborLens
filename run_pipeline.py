import argparse

from src.pipelines.bronze import write_rekrute_bronze, write_sample_bronze
from src.pipelines.gold import silver_to_gold
from src.pipelines.postgres import load_gold_to_postgres
from src.pipelines.silver import bronze_to_silver


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline emploi Maroc Bronze/Silver/Gold")
    parser.add_argument("--sample", action="store_true", help="Utilise les offres exemple")
    parser.add_argument("--source", choices=["sample", "rekrute"], default="sample")
    parser.add_argument("--pages", type=int, default=1, help="Nombre de pages a scraper")
    parser.add_argument("--keyword", default="", help="Mot-cle de recherche optionnel")
    parser.add_argument("--load-postgres", action="store_true", help="Charge les tables Gold dans PostgreSQL")
    args = parser.parse_args()

    source = "sample" if args.sample else args.source

    if source == "sample":
        bronze_path = write_sample_bronze()
    elif source == "rekrute":
        bronze_path = write_rekrute_bronze(max_pages=args.pages, keyword=args.keyword)
    else:
        raise SystemExit(f"Source non supportee: {source}")

    silver_path = bronze_to_silver(bronze_path)
    gold_paths = silver_to_gold(silver_path)

    print(f"Bronze: {bronze_path}")
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
