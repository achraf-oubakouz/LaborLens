import time

from confluent_kafka.admin import AdminClient, NewTopic

from src.streaming.settings import KAFKA_BOOTSTRAP_SERVERS, RAW_OFFERS_TOPIC


def _wait_for_kafka(admin: AdminClient, attempts: int = 20) -> None:
    for attempt in range(1, attempts + 1):
        try:
            metadata = admin.list_topics(timeout=5)
            print(f"Kafka ready with broker(s): {', '.join(str(broker.id) for broker in metadata.brokers.values())}")
            return
        except Exception as exc:
            print(f"Waiting for Kafka ({attempt}/{attempts}): {exc}")
            time.sleep(3)
    raise TimeoutError("Kafka did not become ready in time.")


def main() -> None:
    admin = AdminClient({"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS})
    _wait_for_kafka(admin)
    topics = [NewTopic(RAW_OFFERS_TOPIC, num_partitions=3, replication_factor=1)]
    results = admin.create_topics(topics)

    for topic, result in results.items():
        try:
            result.result()
            print(f"Created topic: {topic}")
        except Exception as exc:
            if "already exists" in str(exc).lower():
                print(f"Topic already exists: {topic}")
            else:
                raise


if __name__ == "__main__":
    main()
