import json
from pathlib import Path
from typing import Any


JOB_BRONZE_SCHEMA = {
    "type": "record",
    "name": "JobPostingBronze",
    "namespace": "laborlens",
    "fields": [
        {"name": "source", "type": ["null", "string"], "default": None},
        {"name": "title", "type": ["null", "string"], "default": None},
        {"name": "company", "type": ["null", "string"], "default": None},
        {"name": "city", "type": ["null", "string"], "default": None},
        {"name": "sector", "type": ["null", "string"], "default": None},
        {"name": "description", "type": ["null", "string"], "default": None},
        {"name": "experience_level", "type": ["null", "string"], "default": None},
        {"name": "contract_type", "type": ["null", "string"], "default": None},
        {"name": "published_at", "type": ["null", "string"], "default": None},
        {"name": "url", "type": ["null", "string"], "default": None},
    ],
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, rows: list[dict[str, Any]]) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_avro(path: Path, rows: list[dict[str, Any]]) -> None:
    try:
        from fastavro import parse_schema, writer
    except ModuleNotFoundError as exc:
        raise SystemExit("Dependance manquante: installez fastavro avec `pip install -r requirements.txt`.") from exc

    ensure_dir(path.parent)
    schema = parse_schema(JOB_BRONZE_SCHEMA)
    normalized_rows = [{field["name"]: row.get(field["name"]) for field in JOB_BRONZE_SCHEMA["fields"]} for row in rows]
    with path.open("wb") as output:
        writer(output, schema, normalized_rows)


def read_avro(path: Path) -> list[dict[str, Any]]:
    try:
        from fastavro import reader
    except ModuleNotFoundError as exc:
        raise SystemExit("Dependance manquante: installez fastavro avec `pip install -r requirements.txt`.") from exc

    with path.open("rb") as input_file:
        return [dict(row) for row in reader(input_file)]
