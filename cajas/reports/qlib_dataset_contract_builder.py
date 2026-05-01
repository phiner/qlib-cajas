"""Build Qlib offline dataset contract from handler-style CSV input."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .qlib_dataset_contract import DatasetContractIssue, QlibDatasetContract, utc_now_iso


def build_qlib_dataset_contract(
    *,
    input_csv: str | Path,
    out_path: str | Path | None,
    dataset_id: str,
    source_contract_path: str = "",
    source_integration_packet_path: str = "",
    instrument_col: str = "instrument",
    datetime_col: str = "datetime",
    label_columns: list[str] | None = None,
    split_metadata: dict | None = None,
) -> dict:
    path = Path(input_csv).expanduser().resolve()
    df = pd.read_csv(path)
    labels = label_columns or ["future_direction_8"]
    required_columns = [instrument_col, datetime_col] + labels
    issues: list[DatasetContractIssue] = []
    warnings: list[DatasetContractIssue] = []

    for col in required_columns:
        if col not in df.columns:
            issues.append(DatasetContractIssue("error", "missing_required_column", f"missing required column: {col}", col))

    feature_columns = [c for c in df.columns if c not in {instrument_col, datetime_col, *labels}]
    non_numeric = [c for c in feature_columns if not pd.api.types.is_numeric_dtype(df[c])]
    if non_numeric:
        warnings.append(DatasetContractIssue("warning", "non_numeric_features", "non-numeric feature columns detected", "feature_columns"))

    null_summary = {c: int(df[c].isna().sum()) for c in df.columns}
    dtype_summary = {c: str(df[c].dtype) for c in df.columns}

    label_distribution: dict[str, dict[str, int]] = {}
    for col in labels:
        if col in df.columns:
            label_distribution[col] = {str(k): int(v) for k, v in df[col].value_counts(dropna=False).to_dict().items()}

    parsed_dt = pd.to_datetime(df[datetime_col], errors="coerce") if datetime_col in df.columns else pd.Series([], dtype="datetime64[ns]")
    if len(parsed_dt) > 0 and parsed_dt.isna().all():
        issues.append(DatasetContractIssue("error", "datetime_parse_failed", "datetime column failed to parse", datetime_col))

    readiness = "blocked"
    if issues:
        readiness = "blocked"
    elif warnings:
        readiness = "ready_with_warnings"
    else:
        readiness = "ready_for_handler_smoke"

    contract = QlibDatasetContract(
        schema_version="v1",
        dataset_id=dataset_id,
        created_at_utc=utc_now_iso(),
        source_contract_path=source_contract_path,
        source_integration_packet_path=source_integration_packet_path,
        instrument_col=instrument_col,
        datetime_col=datetime_col,
        feature_columns=feature_columns,
        label_columns=labels,
        required_columns=required_columns,
        optional_columns=[],
        split_metadata=split_metadata or {"available": False, "reason": "not_provided"},
        time_range={
            "min": None if len(parsed_dt) == 0 or parsed_dt.dropna().empty else str(parsed_dt.min()),
            "max": None if len(parsed_dt) == 0 or parsed_dt.dropna().empty else str(parsed_dt.max()),
        },
        instrument_count=int(df[instrument_col].nunique()) if instrument_col in df.columns else 0,
        row_count=int(len(df)),
        null_summary=null_summary,
        dtype_summary=dtype_summary,
        numeric_feature_count=len(feature_columns) - len(non_numeric),
        non_numeric_feature_columns=non_numeric,
        label_distribution_summary=label_distribution,
        warnings=[w.to_dict() for w in warnings],
        blocking_issues=[i.to_dict() for i in issues],
        readiness_status=readiness,
    ).to_dict()

    if out_path is not None:
        out = Path(out_path).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(contract, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return contract
