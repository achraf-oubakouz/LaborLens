import hashlib
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from confluent_kafka import DeserializingConsumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from sqlalchemy import create_engine, text

from src.pipelines.silver import _load_skills, extract_skills, normalize_city, normalize_required_text
from src.common.storage import put_lake_file
from src.streaming.observability import insert_consumer_batch, insert_dead_letter_job, utc_now
from src.streaming.schemas import JOB_OFFER_SCHEMA
from src.streaming.settings import DATABASE_URL, KAFKA_BOOTSTRAP_SERVERS, RAW_OFFERS_TOPIC, SCHEMA_REGISTRY_URL


PARQUET_ROOT = Path("data/lake/silver/jobs")


def make_job_id(row: dict) -> str:
    natural_key = row.get("url") or "|".join(
        [
            row.get("source") or "",
            row.get("title") or "",
            row.get("company") or "",
            row.get("city") or "",
        ]
    )
    return hashlib.sha256(natural_key.encode("utf-8")).hexdigest()


def validate_raw_offer(row: dict) -> list[str]:
    reasons = []
    source = str(row.get("source") or "").strip()
    title = str(row.get("title") or "").strip()
    description = str(row.get("description") or "").strip()
    url = str(row.get("url") or "").strip()
    fallback_identity = "|".join(
        [
            source,
            title,
            str(row.get("company") or "").strip(),
            str(row.get("city") or "").strip(),
        ]
    ).strip("|")

    if not source:
        reasons.append("missing_source")
    if not title:
        reasons.append("missing_title")
    if not url and not fallback_identity:
        reasons.append("missing_identity")
    if description and len(description) < 20:
        reasons.append("description_too_short")

    return reasons


def clean_offer(row: dict, skills_config: list[str]) -> dict:
    description = row.get("description") or ""
    skills = extract_skills(description, skills_config)
    return {
        "job_id": make_job_id(row),
        "source": normalize_required_text(row.get("source"), default="unknown"),
        "title": normalize_required_text(row.get("title"), default="Sans titre"),
        "company": normalize_required_text(row.get("company")),
        "city": normalize_city(row.get("city")),
        "sector": normalize_required_text(row.get("sector")).title(),
        "description": description,
        "experience_level": normalize_required_text(row.get("experience_level")),
        "contract_type": normalize_required_text(row.get("contract_type")).upper(),
        "published_at": row.get("published_at"),
        "url": row.get("url"),
        "content_length": len(description),
        "skills": ",".join(skills),
        "scraped_at": row.get("scraped_at"),
        "first_seen_at": datetime.now(timezone.utc).isoformat(),
        "last_seen_at": datetime.now(timezone.utc).isoformat(),
    }


def upsert_jobs(engine, rows: list[dict]) -> None:
    sql = text(
        """
        INSERT INTO jobs_clean_stream (
            job_id, source, title, company, city, sector, description,
            experience_level, contract_type, published_at, url, content_length,
            skills, scraped_at, first_seen_at, last_seen_at
        )
        VALUES (
            :job_id, :source, :title, :company, :city, :sector, :description,
            :experience_level, :contract_type, :published_at, :url, :content_length,
            :skills, :scraped_at, :first_seen_at, :last_seen_at
        )
        ON CONFLICT (job_id)
        DO UPDATE SET
            title = EXCLUDED.title,
            company = EXCLUDED.company,
            city = EXCLUDED.city,
            sector = EXCLUDED.sector,
            description = EXCLUDED.description,
            experience_level = EXCLUDED.experience_level,
            contract_type = EXCLUDED.contract_type,
            published_at = EXCLUDED.published_at,
            content_length = EXCLUDED.content_length,
            skills = EXCLUDED.skills,
            scraped_at = EXCLUDED.scraped_at,
            last_seen_at = NOW()
        """
    )
    with engine.begin() as connection:
        connection.execute(sql, rows)


def upsert_skills(engine, rows: list[dict]) -> int:
    skill_rows = []
    for row in rows:
        for skill in [value.strip() for value in row["skills"].split(",") if value.strip()]:
            skill_rows.append(
                {
                    "job_id": row["job_id"],
                    "source": row["source"],
                    "title": row["title"],
                    "company": row["company"],
                    "city": row["city"],
                    "contract_type": row["contract_type"],
                    "published_at": row["published_at"],
                    "url": row["url"],
                    "skill": skill,
                }
            )

    if not skill_rows:
        return 0

    sql = text(
        """
        INSERT INTO job_skills_stream (
            job_id, source, title, company, city, contract_type, published_at, url, skill
        )
        VALUES (
            :job_id, :source, :title, :company, :city, :contract_type, :published_at, :url, :skill
        )
        ON CONFLICT (job_id, skill)
        DO UPDATE SET
            source = EXCLUDED.source,
            title = EXCLUDED.title,
            company = EXCLUDED.company,
            city = EXCLUDED.city,
            contract_type = EXCLUDED.contract_type,
            published_at = EXCLUDED.published_at,
            url = EXCLUDED.url,
            last_seen_at = NOW()
        """
    )
    with engine.begin() as connection:
        connection.execute(sql, skill_rows)
    return len(skill_rows)


def write_parquet_batch(rows: list[dict]) -> str | None:
    if not rows:
        return None

    df = pd.DataFrame(rows)
    now = datetime.now(timezone.utc)
    output_dir = PARQUET_ROOT / f"date={now.date()}" / f"hour={now.hour:02d}"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"part-{now.strftime('%H%M%S')}.parquet"
    df.to_parquet(output_path, index=False)
    put_lake_file(output_path, f"silver/jobs/date={now.date()}/hour={now.hour:02d}/{output_path.name}")
    return str(output_path)


def _make_consumer() -> DeserializingConsumer:
    schema_registry = SchemaRegistryClient({"url": SCHEMA_REGISTRY_URL})
    avro_deserializer = AvroDeserializer(schema_registry, JOB_OFFER_SCHEMA)
    return DeserializingConsumer(
        {
            "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
            "group.id": "laborlens-cleaner",
            "auto.offset.reset": "earliest",
            "key.deserializer": lambda key, ctx: key.decode("utf-8") if key else None,
            "value.deserializer": avro_deserializer,
        }
    )


def flush_batch(engine, rows: list[dict]) -> None:
    if not rows:
        return
    started_at = utc_now()
    try:
        upsert_jobs(engine, rows)
        skills_processed = upsert_skills(engine, rows)
        parquet_path = write_parquet_batch(rows)
        insert_consumer_batch(
            topic=RAW_OFFERS_TOPIC,
            started_at=started_at,
            status="success",
            rows_processed=len(rows),
            skills_processed=skills_processed,
            parquet_path=parquet_path,
        )
        print(f"Processed {len(rows)} streamed offer(s)")
    except Exception as exc:
        insert_consumer_batch(
            topic=RAW_OFFERS_TOPIC,
            started_at=started_at,
            status="failed",
            rows_processed=len(rows),
            error_message=str(exc),
        )
        raise


def main() -> None:
    engine = create_engine(DATABASE_URL)
    skills_config = _load_skills()
    consumer = _make_consumer()
    consumer.subscribe([RAW_OFFERS_TOPIC])

    batch = []
    last_flush = datetime.now(timezone.utc)

    try:
        while True:
            message = consumer.poll(1.0)
            if message is None:
                seconds_since_flush = (datetime.now(timezone.utc) - last_flush).total_seconds()
                if seconds_since_flush >= 60:
                    flush_batch(engine, batch)
                    batch.clear()
                    last_flush = datetime.now(timezone.utc)
                continue
            if message.error():
                print(message.error())
                continue

            raw_offer = message.value()
            validation_errors = validate_raw_offer(raw_offer)
            if validation_errors:
                insert_dead_letter_job(RAW_OFFERS_TOPIC, raw_offer, ",".join(validation_errors))
                print(f"Dead-lettered offer: {','.join(validation_errors)}")
                continue

            batch.append(clean_offer(raw_offer, skills_config))
            seconds_since_flush = (datetime.now(timezone.utc) - last_flush).total_seconds()
            if len(batch) >= 500 or seconds_since_flush >= 60:
                flush_batch(engine, batch)
                batch.clear()
                last_flush = datetime.now(timezone.utc)
    finally:
        flush_batch(engine, batch)
        consumer.close()


if __name__ == "__main__":
    main()
