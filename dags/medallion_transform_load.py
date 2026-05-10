from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator


DEFAULT_ARGS = {"owner": "laborlens", "retries": 1}


with DAG(
    dag_id="medallion_transform_load",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["laborlens", "medallion", "warehouse"],
) as dag:
    medallion_transform_and_load = BashOperator(
        task_id="bronze_to_silver_to_gold_to_postgres",
        bash_command="cd /opt/airflow/project && python run_pipeline.py --source all --rebuild-only --load-postgres",
    )

    record_batch_quality = BashOperator(
        task_id="record_batch_quality_summary",
        bash_command="cd /opt/airflow/project && python quality/ge_runner.py --target batch --persist",
    )

    medallion_transform_and_load >> record_batch_quality
