# Data Dictionary

The machine-readable final catalog is in `governance/data_dictionary.csv`. Lineage and transformation versions are in `governance/lineage.csv` and `governance/transformation_versions.csv`.

## jobs_clean_stream

Streaming serving table for cleaned job offers.

| Column | Description |
|---|---|
| job_id | Deterministic hash used for deduplication. |
| source | Source site or import source. |
| title | Job title. |
| company | Company name when available. |
| city | Normalized city or region. |
| sector | Business sector when available. |
| description | Offer description or listing text. |
| experience_level | Required experience level. |
| contract_type | CDI, CDD, Stage, Freelance, etc. |
| published_at | Offer publication date. |
| url | Source URL. |
| content_length | Description length. |
| skills | Comma-separated detected skills. |
| scraped_at | Time the source was scraped. |
| first_seen_at | First time this offer was loaded. |
| last_seen_at | Last time this offer was observed. |

## job_skills_stream

One row per offer and detected skill.

| Column | Description |
|---|---|
| job_id | Offer identifier. |
| source | Source site. |
| title | Job title. |
| company | Company name. |
| city | Normalized city. |
| contract_type | Contract type. |
| published_at | Publication date. |
| url | Source URL. |
| skill | Detected skill. |
| last_seen_at | Last update time. |

## stream_producer_runs

Tracks scraper/import publish attempts.

| Column | Description |
|---|---|
| run_id | Producer run identifier. |
| source | Source being scraped/imported. |
| keyword | Optional keyword. |
| pages | Pages requested. |
| started_at | Run start time. |
| finished_at | Run finish time. |
| status | running, success, or failed. |
| rows_published | Number of Kafka messages published. |
| error_message | Failure details. |

## stream_consumer_batches

Tracks consumer flushes into PostgreSQL and Parquet.

| Column | Description |
|---|---|
| batch_id | Consumer batch identifier. |
| topic | Kafka topic consumed. |
| started_at | Batch start time. |
| finished_at | Batch finish time. |
| status | success or failed. |
| rows_processed | Clean offers processed. |
| skills_processed | Skill rows processed. |
| parquet_path | Local Parquet output path. |
| error_message | Failure details. |

## stream_dead_letter_jobs

Invalid raw messages rejected by the consumer.

| Column | Description |
|---|---|
| dead_letter_id | Rejected record identifier. |
| topic | Kafka topic. |
| source | Source if available. |
| url | URL if available. |
| title | Title if available. |
| reason | Validation failure reason. |
| raw_payload | Original message as JSON. |
| created_at | Rejection time. |

## data_quality_results

Persisted batch and streaming quality check results.

| Column | Description |
|---|---|
| run_at | Time checks ran. |
| target | batch, stream, or file target. |
| check_name | Quality rule name. |
| severity | error or warning. |
| status | passed or failed. |
| failed_count | Number of failed records. |
| total_count | Total checked records. |
| details | Human-readable details. |
