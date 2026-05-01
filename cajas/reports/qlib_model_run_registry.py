"""Research-only registry for qlib model bridge runs."""

from __future__ import annotations

import json
from pathlib import Path


def register_qlib_model_run(*, registry_path: str | Path, record: dict) -> dict:
    path = Path(registry_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n")
    return {"registry_path": str(path), "status": "ok"}


def load_qlib_model_registry(*, registry_path: str | Path) -> list[dict]:
    path = Path(registry_path).expanduser().resolve()
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows
