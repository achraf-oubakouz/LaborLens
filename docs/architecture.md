# LaborLens Architecture

LaborLens is a data platform for analyzing the Moroccan job market. It helps answer:

- which jobs are currently most requested;
- which skills recruiters mention most often;
- which Moroccan cities offer the most opportunities;
- which sectors and contract types are active.

## Sources

| Source | Status | Notes |
|---|---|---|
| Rekrute | Active | Scraped with Python requests and BeautifulSoup. |
| MarocAnnonces | Active | Scraped with Python requests and BeautifulSoup. |
| Emploi.ma | Experimental | Often blocks automated requests. |
| LinkedIn | Import | Supported through CSV/API-style import, not direct scraping. |

## Batch Architecture

```text
Scrapers
  -> MinIO Bronze Avro + local JSON/Avro debug files
  -> MinIO Silver Parquet + local CSV/Parquet debug files
  -> MinIO Gold CSVs
  -> PostgreSQL
  -> Great Expectations validation summaries
  -> Superset
```

The batch path is still useful for backfills, full rebuilds, and reproducible analytics.

## Streaming Architecture

```text
Scrapers / imports
  -> Kafka topic raw_job_offers with Avro messages
  -> Python streaming consumer
       -> jobs_clean_stream in PostgreSQL
       -> job_skills_stream in PostgreSQL
       -> Parquet micro-batches in MinIO and data/lake/silver/jobs
       -> stream_dead_letter_jobs for invalid records
  -> Superset streaming dashboard
```

The streaming path is designed for local near-real-time simulation. With a 60-second scraper interval, dashboard freshness is approximately 1-2 minutes after a source page is scraped.

## Medallion Layers

| Layer | Format | Purpose |
|---|---|---|
| Bronze | Avro in MinIO, local debug mirror | Raw records as collected. |
| Silver | Parquet in MinIO, local debug mirror | Cleaned, normalized, deduplicated offers. |
| Gold | CSV in MinIO and PostgreSQL tables | Dashboard-ready tables and streaming serving layer. |

## Core Services

| Service | Tool |
|---|---|
| Streaming broker | Apache Kafka |
| Schema management | Confluent Schema Registry |
| Warehouse / serving | PostgreSQL |
| Data lake | MinIO |
| Orchestration | Apache Airflow |
| Dashboard | Apache Superset |
| Local containers | Docker Compose |
| Quality checks | Great Expectations plus persisted summaries |
| Governance | CSV catalog, lineage, and transformation versions in `governance/` |
