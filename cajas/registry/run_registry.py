"""Append-only local run registry for dry-runs and baseline training artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path


@dataclass(frozen=True)
class RunRegistryRecord:
    run_id: str
    run_name: str
    run_type: str
    phase: str
    status: str
    output_dir: str
    artifact_files: list[str]
    created_by: str
    training_executed: bool
    model_artifact_created: bool
    notes: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class RunRegistryAppendResult:
    registry_path: str
    record: dict
    total_records: int

    def to_dict(self) -> dict:
        return asdict(self)


def build_run_id(run_name: str, run_type: str) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    seed = f"{run_name}|{run_type}|{stamp}".encode("utf-8")
    short = hashlib.sha1(seed).hexdigest()[:12]
    return f"{stamp}_{run_type}_{short}"


def _validate_record(record: RunRegistryRecord) -> None:
    if not record.run_id.strip():
        raise ValueError("run_id is required")
    if not record.run_name.strip():
        raise ValueError("run_name is required")
    if not record.run_type.strip():
        raise ValueError("run_type is required")
    if not record.phase.strip():
        raise ValueError("phase is required")
    if not record.status.strip():
        raise ValueError("status is required")
    if not record.output_dir.strip():
        raise ValueError("output_dir is required")
    if not isinstance(record.artifact_files, list):
        raise ValueError("artifact_files must be a list")
    if not isinstance(record.notes, list):
        raise ValueError("notes must be a list")


def read_run_registry(registry_path: str | Path) -> list[dict]:
    path = Path(registry_path).expanduser().resolve()
    if not path.exists():
        return []

    rows: list[dict] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL at line {line_no}: {exc}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"Invalid JSONL object at line {line_no}: expected object")
        rows.append(payload)
    return rows


def append_run_registry_record(
    *,
    registry_path: str | Path,
    record: RunRegistryRecord,
) -> RunRegistryAppendResult:
    _validate_record(record)

    path = Path(registry_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    existing = read_run_registry(path)
    payload = record.to_dict()

    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True, sort_keys=True) + "\n")

    return RunRegistryAppendResult(
        registry_path=str(path),
        record=payload,
        total_records=len(existing) + 1,
    )
