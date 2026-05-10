import argparse
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from quality.checks import QualityResult, run_job_quality_checks
from src.common.paths import SILVER_DIR
from src.streaming.settings import DATABASE_URL


def _read_dataset(target: str) -> pd.DataFrame:
    if target == "batch":
        parquet_path = SILVER_DIR / "offres_clean.parquet"
        csv_path = SILVER_DIR / "offres_clean.csv"
        if parquet_path.exists():
            return pd.read_parquet(parquet_path)
        if csv_path.exists():
            return pd.read_csv(csv_path)
        raise FileNotFoundError(f"Aucun fichier Silver trouve: {parquet_path} ou {csv_path}")

    if target == "stream":
        engine = create_engine(DATABASE_URL)
        return pd.read_sql("SELECT * FROM jobs_clean_stream", engine)

    path = Path(target)
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    if path.suffix == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"Target non supporte: {target}")


def _persist_results(target: str, results: list[QualityResult]) -> None:
    engine = create_engine(DATABASE_URL)
    run_at = datetime.now(timezone.utc).isoformat()
    rows = [
        {
            "run_at": run_at,
            "target": target,
            "check_name": result.check_name,
            "severity": result.severity,
            "status": result.status,
            "failed_count": result.failed_count,
            "total_count": result.total_count,
            "details": result.details,
        }
        for result in results
    ]
    sql = text(
        """
        INSERT INTO data_quality_results (
            run_at, target, check_name, severity, status, failed_count, total_count, details
        )
        VALUES (
            :run_at, :target, :check_name, :severity, :status, :failed_count, :total_count, :details
        )
        """
    )
    with engine.begin() as connection:
        connection.execute(sql, rows)


def _print_results(results: list[QualityResult]) -> None:
    for result in results:
        print(
            f"{result.status.upper()} [{result.severity}] {result.check_name}: "
            f"{result.failed_count}/{result.total_count} failed"
        )
        if result.details:
            print(f"  {result.details}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run LaborLens data quality checks")
    parser.add_argument("--target", default="batch", help="batch, stream, or a CSV/Parquet file path")
    parser.add_argument("--persist", action="store_true", help="Persist results to PostgreSQL")
    args = parser.parse_args()

    df = _read_dataset(args.target)
    results = run_job_quality_checks(df)
    _print_results(results)

    if args.persist:
        _persist_results(args.target, results)

    has_error = any(result.severity == "error" and result.status == "failed" for result in results)
    return 1 if has_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
