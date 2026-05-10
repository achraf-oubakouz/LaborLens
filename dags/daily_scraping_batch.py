from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator


DEFAULT_ARGS = {"owner": "laborlens", "retries": 1}


with DAG(
    dag_id="daily_scraping_batch",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["laborlens", "scraping", "bronze"],
) as dag:
    setup_minio = BashOperator(
        task_id="setup_minio_bucket",
        bash_command="cd /opt/airflow/project && python setup_minio_bucket.py",
    )

    scrape_rekrute = BashOperator(
        task_id="scrape_rekrute",
        bash_command=(
            "cd /opt/airflow/project && "
            "python run_pipeline.py --source rekrute --pages 1 --keyword data --all-bronze"
        ),
    )

    scrape_maroc_annonces = BashOperator(
        task_id="scrape_maroc_annonces",
        bash_command=(
            "cd /opt/airflow/project && "
            "python run_pipeline.py --source maroc_annonces --pages 1 --all-bronze"
        ),
    )

    import_linkedin_csv = BashOperator(
        task_id="import_linkedin_csv_if_present",
        bash_command=(
            "cd /opt/airflow/project && "
            "python scripts/import_linkedin_to_bronze.py --skip-missing"
        ),
    )

    setup_minio >> [scrape_rekrute, scrape_maroc_annonces, import_linkedin_csv]
