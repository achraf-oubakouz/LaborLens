import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SILVER_PATH = PROJECT_ROOT / "data" / "silver" / "offres_clean.csv"
KNOWN_CITIES = {
    "Agadir",
    "Beni Mellal-Khenifra",
    "Casablanca",
    "Casablanca-Mohammedia",
    "Dakhla",
    "Deroua",
    "El Jadida",
    "Errachidia",
    "Fes",
    "Guelmim",
    "International",
    "Laayoune",
    "Marrakech",
    "Marrakech-Safi",
    "Meknes",
    "Mohammedia",
    "Nador",
    "Nouaceur",
    "Oujda",
    "Rabat",
    "Rabat-Sale-Kenitra",
    "Safi",
    "Sale",
    "Settat",
    "Tanger",
    "Tanger-Tetouan-Al Hoceima",
    "Temara",
    "Tetouan",
    "Tout Le Maroc",
}


def main() -> int:
    if not SILVER_PATH.exists():
        print(f"Fichier introuvable: {SILVER_PATH}")
        return 1

    df = pd.read_csv(SILVER_PATH)
    errors = []
    warnings = []

    missing_titles = df["title"].fillna("").str.strip().eq("").sum()
    if missing_titles:
        errors.append(f"{missing_titles} offre(s) sans titre")

    missing_dates = df["published_at"].isna().sum()
    if missing_dates:
        warnings.append(f"{missing_dates} offre(s) sans date de publication")

    unknown_cities = sorted(set(df["city"].dropna()) - KNOWN_CITIES)
    if unknown_cities:
        warnings.append(f"Ville(s) non referencee(s): {', '.join(unknown_cities)}")

    short_content = (df["content_length"].fillna(0) < 50).sum()
    if short_content:
        warnings.append(f"{short_content} contenu(s) suspect(s), moins de 50 caracteres")

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")

    if errors:
        return 1

    print("Validation silver OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
