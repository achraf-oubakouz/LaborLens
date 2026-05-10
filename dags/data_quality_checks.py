from __future__ import annotations

from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator


DEFAULT_ARGS = {"owner": "laborlens", "retries": 0}


with DAG(
    dag_id="data_quality_checks",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["laborlens", "great-expectations", "quality"],
) as dag:
    validate_silver = BashOperator(
        task_id="validate_offres_clean_silver",
        bash_command="cd /opt/airflow/project && python quality/ge_runner.py --target batch --persist",
    )

    validate_stream = BashOperator(
        task_id="validate_jobs_clean_stream",
        bash_command="cd /opt/airflow/project && python quality/ge_runner.py --target stream --persist",
    )

    validate_silver >> validate_stream
