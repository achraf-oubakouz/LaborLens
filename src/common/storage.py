import os
from pathlib import Path


MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://127.0.0.1:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "laborlens")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"
MINIO_UPLOAD_ENABLED = os.getenv("MINIO_UPLOAD_ENABLED", "true").lower() == "true"
KEEP_LOCAL_DEBUG_COPY = os.getenv("KEEP_LOCAL_DEBUG_COPY", "true").lower() == "true"


def _client():
    try:
        from minio import Minio
    except ModuleNotFoundError as exc:
        raise RuntimeError("Dependance manquante: installez minio avec `pip install -r requirements.txt`.") from exc

    return Minio(
        MINIO_ENDPOINT.replace("http://", "").replace("https://", ""),
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE,
    )


def ensure_bucket() -> None:
    client = _client()
    if not client.bucket_exists(MINIO_BUCKET):
        client.make_bucket(MINIO_BUCKET)


def upload_file(local_path: str | Path, object_name: str) -> str | None:
    if not MINIO_UPLOAD_ENABLED:
        return None

    path = Path(local_path)
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable pour upload MinIO: {path}")

    try:
        ensure_bucket()
        _client().fput_object(MINIO_BUCKET, object_name.replace("\\", "/"), str(path))
        uri = f"s3://{MINIO_BUCKET}/{object_name.replace('\\', '/')}"
        print(f"MinIO: {uri}")
        return uri
    except Exception as exc:
        print(f"WARNING: upload MinIO ignore pour {path}: {exc}")
        return None


def put_lake_file(local_path: str | Path, object_name: str) -> str:
    """Upload a lake artifact to MinIO and return its canonical lake URI.

    The caller is still responsible for writing the local debug mirror first.
    If MinIO is unavailable, the local path is returned so local development can
    continue with the same pipeline commands.
    """
    uploaded_uri = upload_file(local_path, object_name)
    return uploaded_uri or str(Path(local_path))
