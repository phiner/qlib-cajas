"""Training contract schema for Qlib model experiment bridge."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class ModelContractIssue:
    severity: str
    code: str
    message: str
    field: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class QlibModelTrainingContract:
    schema_version: str
    run_id: str
    created_at_utc: str
    handler_input_path: str
    handler_manifest_path: str
    dataset_contract_path: str
    handler_smoke_report_path: str
    instrument_col: str
    datetime_col: str
    label_col: str
    feature_columns: list[str]
    split_ratios: dict
    row_count: int
    warnings: list[dict] = field(default_factory=list)
    blocking_issues: list[dict] = field(default_factory=list)
    readiness_status: str = "blocked"

    def to_dict(self) -> dict:
        return asdict(self)


def utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat()
