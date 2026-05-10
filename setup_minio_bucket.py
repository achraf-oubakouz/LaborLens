from src.common.storage import MINIO_BUCKET, ensure_bucket


def main() -> None:
    ensure_bucket()
    print(f"MinIO bucket ready: {MINIO_BUCKET}")


if __name__ == "__main__":
    main()
