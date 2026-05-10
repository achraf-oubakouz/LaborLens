import json
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import create_engine, text

from src.streaming.settings import DATABASE_URL


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def get_engine():
    return create_engine(DATABASE_URL)


def start_producer_run(source: str, keyword: str, pages: int) -> str:
    run_id = new_id("producer")
    sql = text(
        """
        INSERT INTO stream_producer_runs (
            run_id, source, keyword, pages, started_at, status
        )
        VALUES (
            :run_id, :source, :keyword, :pages, :started_at, 'running'
        )
        """
    )
    with get_engine().begin() as connection:
        connection.execute(
            sql,
            {
                "run_id": run_id,
                "source": source,
                "keyword": keyword,
                "pages": pages,
                "started_at": utc_now(),
            },
        )
    return run_id


def finish_producer_run(run_id: str, status: str, rows_published: int = 0, error_message: str | None = None) -> None:
    sql = text(
        """
        UPDATE stream_producer_runs
        SET finished_at = :finished_at,
            status = :status,
            rows_published = :rows_published,
            error_message = :error_message
        WHERE run_id = :run_id
        """
    )
    with get_engine().begin() as connection:
        connection.execute(
            sql,
            {
                "run_id": run_id,
                "finished_at": utc_now(),
                "status": status,
                "rows_published": rows_published,
                "error_message": error_message,
            },
        )


def insert_consumer_batch(
    topic: str,
    started_at: str,
    status: str,
    rows_processed: int = 0,
    skills_processed: int = 0,
    parquet_path: str | None = None,
    error_message: str | None = None,
) -> None:
    sql = text(
        """
        INSERT INTO stream_consumer_batches (
            batch_id, topic, started_at, finished_at, status, rows_processed,
            skills_processed, parquet_path, error_message
        )
        VALUES (
            :batch_id, :topic, :started_at, :finished_at, :status, :rows_processed,
            :skills_processed, :parquet_path, :error_message
        )
        """
    )
    with get_engine().begin() as connection:
        connection.execute(
            sql,
            {
                "batch_id": new_id("consumer_batch"),
                "topic": topic,
                "started_at": started_at,
                "finished_at": utc_now(),
                "status": status,
                "rows_processed": rows_processed,
                "skills_processed": skills_processed,
                "parquet_path": parquet_path,
                "error_message": error_message,
            },
        )


def insert_dead_letter_job(topic: str, row: dict, reason: str) -> None:
    sql = text(
        """
        INSERT INTO stream_dead_letter_jobs (
            dead_letter_id, topic, source, url, title, reason, raw_payload, created_at
        )
        VALUES (
            :dead_letter_id, :topic, :source, :url, :title, :reason,
            CAST(:raw_payload AS JSONB), :created_at
        )
        """
    )
    with get_engine().begin() as connection:
        connection.execute(
            sql,
            {
                "dead_letter_id": new_id("dead_letter"),
                "topic": topic,
                "source": row.get("source"),
                "url": row.get("url"),
                "title": row.get("title"),
                "reason": reason,
                "raw_payload": json.dumps(row, ensure_ascii=False),
                "created_at": utc_now(),
            },
        )
