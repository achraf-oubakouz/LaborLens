import os
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
from sqlalchemy.exc import OperationalError
from sqlalchemy import create_engine, text

from src.common.paths import GOLD_DIR, SILVER_DIR
from src.common.versions import SILVER_TRANSFORM_VERSION, SKILLS_EXTRACTION_VERSION


DEFAULT_DATABASE_URL = "postgresql+psycopg2://emploi:emploi@127.0.0.1:5432/emploi_maroc"

GOLD_TABLES = (
    ("offres_par_jour.csv", "offres_par_jour"),
    ("offres_par_ville.csv", "offres_par_ville"),
    ("offres_par_secteur.csv", "offres_par_secteur"),
    ("offres_par_contrat.csv", "offres_par_contrat"),
    ("top_competences.csv", "top_competences"),
    ("offer_skills.csv", "offer_skills"),
)


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def record_pipeline_run(
    run_id: str,
    pipeline_name: str,
    started_at: datetime,
    status: str,
    bronze_paths: list[str] | None = None,
    silver_path: str | None = None,
    gold_paths: list[str] | None = None,
    error_message: str | None = None,
    database_url: str | None = None,
) -> None:
    engine = create_engine(database_url or get_database_url())
    sql = text(
        """
        INSERT INTO pipeline_run_metadata (
            run_id, pipeline_name, started_at, finished_at, status, bronze_paths,
            silver_path, gold_paths, silver_transform_version,
            skills_extraction_version, error_message
        )
        VALUES (
            :run_id, :pipeline_name, :started_at, :finished_at, :status, :bronze_paths,
            :silver_path, :gold_paths, :silver_transform_version,
            :skills_extraction_version, :error_message
        )
        ON CONFLICT (run_id)
        DO UPDATE SET
            finished_at = EXCLUDED.finished_at,
            status = EXCLUDED.status,
            bronze_paths = EXCLUDED.bronze_paths,
            silver_path = EXCLUDED.silver_path,
            gold_paths = EXCLUDED.gold_paths,
            error_message = EXCLUDED.error_message
        """
    )
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS pipeline_run_metadata (
                    run_id TEXT PRIMARY KEY,
                    pipeline_name VARCHAR(100) NOT NULL,
                    started_at TIMESTAMP NOT NULL,
                    finished_at TIMESTAMP,
                    status VARCHAR(20) NOT NULL,
                    bronze_paths TEXT,
                    silver_path TEXT,
                    gold_paths TEXT,
                    silver_transform_version VARCHAR(80),
                    skills_extraction_version VARCHAR(80),
                    error_message TEXT
                )
                """
            )
        )
        connection.execute(
            sql,
            {
                "run_id": run_id,
                "pipeline_name": pipeline_name,
                "started_at": started_at,
                "finished_at": datetime.now(timezone.utc),
                "status": status,
                "bronze_paths": "\n".join(bronze_paths or []),
                "silver_path": silver_path,
                "gold_paths": "\n".join(gold_paths or []),
                "silver_transform_version": SILVER_TRANSFORM_VERSION,
                "skills_extraction_version": SKILLS_EXTRACTION_VERSION,
                "error_message": error_message,
            },
        )


def load_gold_to_postgres(
    gold_dir: str | Path = GOLD_DIR,
    silver_path: str | Path = SILVER_DIR / "offres_clean.parquet",
    database_url: str | None = None,
) -> list[str]:
    gold_path = Path(gold_dir)
    silver_file = Path(silver_path)
    missing_files = [name for name, _ in GOLD_TABLES if not (gold_path / name).exists()]
    if missing_files:
        joined = ", ".join(missing_files)
        raise FileNotFoundError(f"Fichier(s) Gold introuvable(s): {joined}")
    if not silver_file.exists():
        raise FileNotFoundError(f"Fichier Silver introuvable: {silver_file}")

    engine = create_engine(database_url or get_database_url())
    loaded_tables = []

    try:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE offres_clean ADD COLUMN IF NOT EXISTS silver_transform_version VARCHAR(80)"))
            connection.execute(text("ALTER TABLE offres_clean ADD COLUMN IF NOT EXISTS skills_extraction_version VARCHAR(80)"))
            if silver_file.suffix == ".parquet":
                silver_df = pd.read_parquet(silver_file)
            else:
                silver_df = pd.read_csv(silver_file)
            connection.execute(text("TRUNCATE TABLE offres_clean"))
            silver_df.to_sql("offres_clean", connection, if_exists="append", index=False)
            loaded_tables.append("offres_clean")

            for file_name, table_name in GOLD_TABLES:
                df = pd.read_csv(gold_path / file_name)
                connection.execute(text(f"TRUNCATE TABLE {table_name}"))
                df.to_sql(table_name, connection, if_exists="append", index=False)
                loaded_tables.append(table_name)
    except OperationalError as exc:
        raise RuntimeError(
            "Impossible de se connecter a PostgreSQL. Verifiez que Docker Desktop est lance, "
            "que le conteneur postgres est actif avec `docker compose ps`, et que le port 5432 "
            "n'est pas utilise par une autre base locale."
        ) from exc

    return loaded_tables
