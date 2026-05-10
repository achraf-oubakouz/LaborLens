import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.common.locations import known_city_values
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
        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM jobs_clean_stream"))
            return pd.DataFrame(result.mappings().all())

    path = Path(target)
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    if path.suffix == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"Target non supporte: {target}")


def _ge_dataset(df: pd.DataFrame):
    try:
        import great_expectations as gx

        return gx.from_pandas(df.copy())
    except (AttributeError, ImportError):
        from great_expectations.dataset import PandasDataset

        return PandasDataset(df.copy())


def _expectation_result(
    target: str,
    check_name: str,
    severity: str,
    result: dict[str, Any],
    total_count: int,
    details: str = "",
) -> dict[str, Any]:
    payload = result.to_json_dict() if hasattr(result, "to_json_dict") else dict(result)
    unexpected_count = payload.get("result", {}).get("unexpected_count", 0)
    return {
        "run_at": datetime.now(timezone.utc),
        "target": target,
        "check_name": check_name,
        "severity": severity,
        "status": "passed" if payload.get("success") else "failed",
        "failed_count": int(unexpected_count or 0),
        "total_count": int(total_count),
        "details": details,
    }


def run_ge_validations(df: pd.DataFrame, target: str) -> list[dict[str, Any]]:
    total = len(df)
    if "content_length" not in df.columns and "description" in df.columns:
        df = df.copy()
        df["content_length"] = df["description"].fillna("").astype(str).str.len()

    dataset = _ge_dataset(df)
    known_cities = sorted(known_city_values())
    results = []

    results.append(
        _expectation_result(
            target,
            "title_not_null",
            "error",
            dataset.expect_column_values_to_not_be_null("title"),
            total,
            "Great Expectations: title must be present.",
        )
    )
    results.append(
        _expectation_result(
            target,
            "title_not_empty",
            "error",
            dataset.expect_column_values_to_match_regex("title", r"\S+"),
            total,
            "Great Expectations: title must not be blank.",
        )
    )
    results.append(
        _expectation_result(
            target,
            "source_not_null",
            "error",
            dataset.expect_column_values_to_not_be_null("source"),
            total,
            "Great Expectations: source must be present.",
        )
    )
    results.append(
        _expectation_result(
            target,
            "source_not_empty",
            "error",
            dataset.expect_column_values_to_match_regex("source", r"\S+"),
            total,
            "Great Expectations: source must not be blank.",
        )
    )
    results.append(
        _expectation_result(
            target,
            "published_at_present_or_flagged",
            "warning",
            dataset.expect_column_values_to_not_be_null("published_at"),
            total,
            "Missing publication dates are accepted as flagged warnings.",
        )
    )
    results.append(
        _expectation_result(
            target,
            "city_known_or_non_renseigne",
            "warning",
            dataset.expect_column_values_to_be_in_set("city", known_cities),
            total,
            "City must be normalized or Non renseigne.",
        )
    )
    results.append(
        _expectation_result(
            target,
            "content_length_at_least_50",
            "warning",
            dataset.expect_column_values_to_be_between("content_length", min_value=50),
            total,
            "Short content is a warning-level rule.",
        )
    )
    if "url" in df.columns:
        url_dataset = _ge_dataset(df[df["url"].fillna("").astype(str).str.strip() != ""])
        results.append(
            _expectation_result(
                target,
                "url_unique_when_present",
                "error",
                url_dataset.expect_column_values_to_be_unique("url"),
                len(url_dataset),
                "Non-empty URLs must be unique.",
            )
        )

    return results


def _persist_results(results: list[dict[str, Any]]) -> None:
    if not results:
        return
    engine = create_engine(DATABASE_URL)
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
        connection.execute(sql, results)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Great Expectations validations for LaborLens")
    parser.add_argument("--target", default="batch", help="batch, stream, or a CSV/Parquet file path")
    parser.add_argument("--persist", action="store_true", help="Persist validation summaries to PostgreSQL")
    args = parser.parse_args()

    df = _read_dataset(args.target)
    results = run_ge_validations(df, args.target)
    for result in results:
        print(
            f"{result['status'].upper()} [{result['severity']}] {result['check_name']}: "
            f"{result['failed_count']}/{result['total_count']} failed"
        )

    if args.persist:
        _persist_results(results)

    has_error = any(result["severity"] == "error" and result["status"] == "failed" for result in results)
    return 1 if has_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
