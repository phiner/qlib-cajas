"""Offline Qlib dataset/handler contract schema and helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class DatasetContractIssue:
    severity: str
    code: str
    message: str
    field: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class QlibDatasetContract:
    schema_version: str
    dataset_id: str
    created_at_utc: str
    source_contract_path: str
    source_integration_packet_path: str
    instrument_col: str
    datetime_col: str
    feature_columns: list[str]
    label_columns: list[str]
    required_columns: list[str]
    optional_columns: list[str]
    split_metadata: dict
    time_range: dict
    instrument_count: int
    row_count: int
    null_summary: dict
    dtype_summary: dict
    numeric_feature_count: int
    non_numeric_feature_columns: list[str]
    label_distribution_summary: dict
    warnings: list[dict] = field(default_factory=list)
    blocking_issues: list[dict] = field(default_factory=list)
    readiness_status: str = "blocked"

    def to_dict(self) -> dict:
        return asdict(self)


def utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat()
