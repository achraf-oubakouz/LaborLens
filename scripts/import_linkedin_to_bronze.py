import argparse

from src.pipelines.bronze import _write_bronze_rows
from src.scrapers.linkedin_importer import DEFAULT_LINKEDIN_CSV, import_linkedin_jobs


def main() -> None:
    parser = argparse.ArgumentParser(description="Import local LinkedIn CSV rows into Bronze")
    parser.add_argument("--csv", default=str(DEFAULT_LINKEDIN_CSV), help="Path to local LinkedIn CSV export")
    parser.add_argument("--keyword", default="", help="Optional keyword filter")
    parser.add_argument("--skip-missing", action="store_true", help="Exit successfully when the CSV is absent")
    args = parser.parse_args()

    try:
        rows = import_linkedin_jobs(args.csv, keyword=args.keyword)
    except FileNotFoundError:
        if args.skip_missing:
            print(f"LinkedIn CSV not present, skipping: {args.csv}")
            return
        raise

    if not rows:
        print("LinkedIn CSV contained no rows after filtering.")
        return

    output_path = _write_bronze_rows("linkedin", rows)
    print(f"LinkedIn Bronze: {output_path}")


if __name__ == "__main__":
    main()
