import os


KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:9092")
SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", "http://localhost:8081")
RAW_OFFERS_TOPIC = os.getenv("RAW_OFFERS_TOPIC", "raw_job_offers")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://emploi:emploi@127.0.0.1:5432/emploi_maroc",
)
