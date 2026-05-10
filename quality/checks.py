from dataclasses import dataclass

import pandas as pd

from src.common.locations import known_city_values


@dataclass
class QualityResult:
    check_name: str
    severity: str
    status: str
    failed_count: int
    total_count: int
    details: str = ""


def _result(check_name: str, severity: str, failed_count: int, total_count: int, details: str = "") -> QualityResult:
    status = "passed" if failed_count == 0 else "failed"
    return QualityResult(check_name, severity, status, int(failed_count), int(total_count), details)


def run_job_quality_checks(df: pd.DataFrame) -> list[QualityResult]:
    total = len(df)
    results = []

    results.append(
        _result(
            "title_not_empty",
            "error",
            df.get("title", pd.Series(dtype=str)).fillna("").astype(str).str.strip().eq("").sum(),
            total,
            "Offres sans titre.",
        )
    )

    if "url" in df.columns:
        duplicate_urls = df["url"].fillna("").astype(str).str.strip()
        duplicate_urls = duplicate_urls[duplicate_urls != ""]
        duplicate_count = duplicate_urls.duplicated().sum()
    else:
        duplicate_count = 0
    results.append(_result("url_unique_when_present", "error", duplicate_count, total, "URLs dupliquees."))

    if "published_at" in df.columns:
        missing_dates = pd.to_datetime(df["published_at"], errors="coerce").isna().sum()
    else:
        missing_dates = total
    results.append(_result("published_at_present", "warning", missing_dates, total, "Date de publication manquante."))

    if "city" in df.columns:
        cities = df["city"].fillna("Non renseigne").astype(str).str.strip()
        unknown = sorted(set(cities) - known_city_values())
        unknown_count = cities.isin(unknown).sum()
    else:
        unknown = []
        unknown_count = total
    results.append(
        _result(
            "city_known_or_normalized",
            "warning",
            unknown_count,
            total,
            f"Villes non referencees: {', '.join(unknown[:20])}" if unknown else "",
        )
    )

    if "content_length" in df.columns:
        short_content = pd.to_numeric(df["content_length"], errors="coerce").fillna(0).lt(50).sum()
    elif "description" in df.columns:
        short_content = df["description"].fillna("").astype(str).str.len().lt(50).sum()
    else:
        short_content = total
    results.append(_result("content_length_at_least_50", "warning", short_content, total, "Contenu trop court."))

    if "source" in df.columns:
        missing_source = df["source"].fillna("").astype(str).str.strip().eq("").sum()
    else:
        missing_source = total
    results.append(_result("source_not_empty", "error", missing_source, total, "Source manquante."))

    return results

