import pandas as pd

from src.common.paths import SILVER_DIR


def main() -> None:
    silver_path = SILVER_DIR / "offres_clean.csv"
    if not silver_path.exists():
        raise SystemExit(f"Fichier introuvable: {silver_path}")

    df = pd.read_csv(silver_path)
    print("Offres par source:")
    print(df["source"].value_counts(dropna=False).to_string())


if __name__ == "__main__":
    main()
