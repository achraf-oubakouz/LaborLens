import argparse
import time
from datetime import datetime, timezone

from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer

from src.scrapers.linkedin_importer import DEFAULT_LINKEDIN_CSV, import_linkedin_jobs
from src.scrapers.maroc_annonces_scraper import scrape_maroc_annonces_jobs
from src.scrapers.rekrute_scraper import scrape_rekrute_jobs
from src.streaming.observability import finish_producer_run, start_producer_run
from src.streaming.schemas import JOB_OFFER_SCHEMA
from src.streaming.settings import KAFKA_BOOTSTRAP_SERVERS, RAW_OFFERS_TOPIC, SCHEMA_REGISTRY_URL


SCRAPERS = {
    "rekrute": scrape_rekrute_jobs,
    "maroc_annonces": scrape_maroc_annonces_jobs,
}


def _make_producer() -> SerializingProducer:
    schema_registry = SchemaRegistryClient({"url": SCHEMA_REGISTRY_URL})
    avro_serializer = AvroSerializer(schema_registry, JOB_OFFER_SCHEMA)
    return SerializingProducer(
        {
            "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
            "key.serializer": lambda key, ctx: key.encode("utf-8"),
            "value.serializer": avro_serializer,
        }
    )


def _message_key(row: dict) -> str:
    return row.get("url") or "|".join(
        [
            row.get("source") or "",
            row.get("title") or "",
            row.get("company") or "",
            row.get("city") or "",
        ]
    )


def publish_once(source: str, pages: int = 1, keyword: str = "", linkedin_csv: str = str(DEFAULT_LINKEDIN_CSV)) -> int:
    run_id = start_producer_run(source=source, keyword=keyword, pages=pages)
    try:
        if source == "linkedin":
            rows = import_linkedin_jobs(linkedin_csv, keyword=keyword)
        else:
            scraper = SCRAPERS[source]
            rows = scraper(max_pages=pages, keyword=keyword)
        producer = _make_producer()
        scraped_at = datetime.now(timezone.utc).isoformat()

        for row in rows:
            row["scraped_at"] = scraped_at
            producer.produce(RAW_OFFERS_TOPIC, key=_message_key(row), value=row)

        producer.flush()
        finish_producer_run(run_id, status="success", rows_published=len(rows))
        print(f"Published {len(rows)} offer(s) from {source}")
        return len(rows)
    except Exception as exc:
        finish_producer_run(run_id, status="failed", error_message=str(exc))
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish scraped job offers to Kafka")
    parser.add_argument("--source", choices=sorted([*SCRAPERS, "linkedin"]), default="rekrute")
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--keyword", default="")
    parser.add_argument("--linkedin-csv", default=str(DEFAULT_LINKEDIN_CSV))
    parser.add_argument("--loop", action="store_true", help="Run continuously")
    parser.add_argument("--interval-seconds", type=int, default=60)
    args = parser.parse_args()

    while True:
        publish_once(args.source, pages=args.pages, keyword=args.keyword, linkedin_csv=args.linkedin_csv)
        if not args.loop:
            break
        time.sleep(args.interval_seconds)


if __name__ == "__main__":
    main()
