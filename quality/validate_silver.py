import sys
from pathlib import Path

import pandas as pd

from quality.checks import run_job_quality_checks


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SILVER_PARQUET_PATH = PROJECT_ROOT / "data" / "silver" / "offres_clean.parquet"
SILVER_CSV_PATH = PROJECT_ROOT / "data" / "silver" / "offres_clean.csv"


def main() -> int:
    if SILVER_PARQUET_PATH.exists():
        df = pd.read_parquet(SILVER_PARQUET_PATH)
    elif SILVER_CSV_PATH.exists():
        df = pd.read_csv(SILVER_CSV_PATH)
    else:
        print(f"Fichier introuvable: {SILVER_PARQUET_PATH} ou {SILVER_CSV_PATH}")
        return 1

    results = run_job_quality_checks(df)
    for result in results:
        prefix = "ERROR" if result.severity == "error" else "WARNING"
        if result.status == "failed":
            print(f"{prefix}: {result.check_name} ({result.failed_count}/{result.total_count}) {result.details}")

    if any(result.severity == "error" and result.status == "failed" for result in results):
        return 1

    print("Validation silver OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
