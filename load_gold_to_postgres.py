from src.pipelines.postgres import load_gold_to_postgres


def main() -> None:
    tables = load_gold_to_postgres()
    print("Tables chargees dans PostgreSQL:")
    for table in tables:
        print(f"- {table}")


if __name__ == "__main__":
    main()
