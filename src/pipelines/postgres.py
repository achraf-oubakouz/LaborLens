import os
from pathlib import Path

import pandas as pd
from sqlalchemy.exc import OperationalError
from sqlalchemy import create_engine, text

from src.common.paths import GOLD_DIR


DEFAULT_DATABASE_URL = "postgresql+psycopg2://emploi:emploi@127.0.0.1:5432/emploi_maroc"

GOLD_TABLES = (
    ("offres_par_jour.csv", "offres_par_jour"),
    ("offres_par_ville.csv", "offres_par_ville"),
    ("offres_par_secteur.csv", "offres_par_secteur"),
    ("offres_par_contrat.csv", "offres_par_contrat"),
    ("top_competences.csv", "top_competences"),
)


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def load_gold_to_postgres(
    gold_dir: str | Path = GOLD_DIR,
    database_url: str | None = None,
) -> list[str]:
    gold_path = Path(gold_dir)
    missing_files = [name for name, _ in GOLD_TABLES if not (gold_path / name).exists()]
    if missing_files:
        joined = ", ".join(missing_files)
        raise FileNotFoundError(f"Fichier(s) Gold introuvable(s): {joined}")

    engine = create_engine(database_url or get_database_url())
    loaded_tables = []

    try:
        with engine.begin() as connection:
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
