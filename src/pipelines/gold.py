from pathlib import Path
from datetime import date

import pandas as pd

from src.common.paths import GOLD_DIR
from src.common.storage import put_lake_file


def _write(df: pd.DataFrame, name: str) -> None:
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    output_path = GOLD_DIR / name
    df.to_csv(output_path, index=False, encoding="utf-8")
    table_name = Path(name).stem
    dated_path = GOLD_DIR / table_name / f"{date.today().isoformat()}.csv"
    dated_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(dated_path, index=False, encoding="utf-8")
    put_lake_file(dated_path, f"gold/{table_name}/{dated_path.name}")


def _read_silver(path: str | Path) -> pd.DataFrame:
    silver_path = Path(path)
    if silver_path.suffix == ".parquet":
        return pd.read_parquet(silver_path)
    return pd.read_csv(silver_path)


def silver_to_gold(silver_path: str | Path) -> list[str]:
    df = _read_silver(silver_path)
    df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce")
    df["week"] = df["published_at"].dt.to_period("W").astype(str)

    offres_par_jour = (
        df.groupby(df["published_at"].dt.date, dropna=False)
        .size()
        .reset_index(name="nb_offres")
        .rename(columns={"published_at": "date"})
    )
    _write(offres_par_jour, "offres_par_jour.csv")

    offres_par_ville = df.groupby("city").size().reset_index(name="nb_offres")
    _write(offres_par_ville.sort_values("nb_offres", ascending=False), "offres_par_ville.csv")

    offres_par_secteur = df.groupby("sector").size().reset_index(name="nb_offres")
    _write(offres_par_secteur.sort_values("nb_offres", ascending=False), "offres_par_secteur.csv")

    offres_par_contrat = df.groupby("contract_type").size().reset_index(name="nb_offres")
    _write(offres_par_contrat.sort_values("nb_offres", ascending=False), "offres_par_contrat.csv")

    skills = (
        df[
            [
                "source",
                "title",
                "company",
                "city",
                "contract_type",
                "published_at",
                "url",
                "skills",
            ]
        ]
        .assign(skill=df["skills"].fillna("").str.split(","))
        .explode("skill")
        .assign(skill=lambda data: data["skill"].str.strip())
    )
    skills = skills[skills["skill"] != ""]
    offer_skills = skills.drop(columns=["skills"]).copy()
    _write(offer_skills, "offer_skills.csv")

    top_competences = skills.groupby("skill").size().reset_index(name="nb_mentions")
    _write(top_competences.sort_values("nb_mentions", ascending=False), "top_competences.csv")

    return [str(path) for path in sorted(GOLD_DIR.glob("*.csv"))]
