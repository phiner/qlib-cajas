"""Qlib adapter contract schema and validation helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class ContractIssue:
    severity: str
    code: str
    message: str
    field: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class QlibAdapterContract:
    contract_version: str
    candidate_id: str
    research_run_id: str
    dataset_version: str
    feature_set_id: str
    label_variant_id: str
    target_name: str
    prediction_horizon: int
    instrument_universe: list[str]
    frequency: str
    required_feature_columns: list[str]
    required_label_columns: list[str]
    artifact_paths: dict[str, str]
    known_limitations: list[str] = field(default_factory=list)
    promotion_status: str = "draft"
    created_at_utc: str = ""

    def to_dict(self) -> dict:
        payload = asdict(self)
        if not payload["created_at_utc"]:
            payload["created_at_utc"] = utc_now_iso()
        return payload


def utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat()


def validate_qlib_adapter_contract(contract: dict, *, strict_paths: bool = False) -> list[ContractIssue]:
    issues: list[ContractIssue] = []
    required = [
        "contract_version",
        "candidate_id",
        "research_run_id",
        "dataset_version",
        "feature_set_id",
        "label_variant_id",
        "target_name",
        "prediction_horizon",
        "instrument_universe",
        "frequency",
        "required_feature_columns",
        "required_label_columns",
        "artifact_paths",
        "promotion_status",
        "created_at_utc",
    ]
    for field in required:
        if field not in contract:
            issues.append(ContractIssue("error", "missing_required_field", f"required field missing: {field}", field))
            continue
        value = contract.get(field)
        if value in (None, ""):
            issues.append(ContractIssue("error", "missing_required_field", f"required field missing: {field}", field))

    if contract.get("promotion_status") not in {"draft", "blocked", "candidate_for_manual_review"}:
        issues.append(ContractIssue("error", "invalid_promotion_status", "promotion_status is invalid", "promotion_status"))

    horizon = contract.get("prediction_horizon")
    if isinstance(horizon, int):
        if horizon <= 0:
            issues.append(ContractIssue("error", "invalid_horizon", "prediction_horizon must be positive", "prediction_horizon"))
    else:
        issues.append(ContractIssue("error", "invalid_horizon_type", "prediction_horizon must be integer", "prediction_horizon"))

    paths = contract.get("artifact_paths", {})
    if not isinstance(paths, dict):
        issues.append(ContractIssue("error", "invalid_artifact_paths", "artifact_paths must be an object", "artifact_paths"))
        return issues

    if strict_paths:
        from pathlib import Path

        for key, value in paths.items():
            if not value:
                issues.append(ContractIssue("error", "missing_artifact_path", f"artifact path missing for {key}", "artifact_paths"))
                continue
            if not Path(value).expanduser().exists():
                issues.append(ContractIssue("error", "artifact_path_not_found", f"artifact path does not exist: {value}", "artifact_paths"))
    return issues
