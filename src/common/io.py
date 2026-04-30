import json
from pathlib import Path
from typing import Any


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, rows: list[dict[str, Any]]) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))
