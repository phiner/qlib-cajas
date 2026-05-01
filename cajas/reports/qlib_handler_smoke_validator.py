"""Validate offline handler input package for Qlib handler smoke readiness."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def validate_qlib_handler_input(*, handler_dir: str | Path) -> dict:
    d = Path(handler_dir).expanduser().resolve()
    checked_paths = {
        "manifest": str(d / "handler_input_manifest.json"),
        "handler_input_csv": str(d / "handler_input.csv"),
        "columns": str(d / "columns.json"),
        "splits": str(d / "splits.json"),
    }
    warnings: list[dict] = []
    blocking: list[dict] = []

    for key, path in checked_paths.items():
        if not Path(path).exists():
            blocking.append({"severity": "error", "code": "missing_path", "message": f"missing required file: {key}", "field": key})

    if blocking:
        return {
            "schema_version": "v1",
            "status": "fail",
            "checked_paths": checked_paths,
            "row_count": 0,
            "feature_count": 0,
            "label_count": 0,
            "warnings": warnings,
            "blocking_issues": blocking,
            "next_phase_recommendation": "fix missing files before Phase 86-95 bridge",
        }

    manifest = json.loads((d / "handler_input_manifest.json").read_text(encoding="utf-8"))
    columns = json.loads((d / "columns.json").read_text(encoding="utf-8"))
    splits = json.loads((d / "splits.json").read_text(encoding="utf-8"))
    df = pd.read_csv(d / "handler_input.csv")

    req_cols = columns.get("required_columns", [])
    for col in req_cols:
        if col not in df.columns:
            blocking.append({"severity": "error", "code": "missing_required_column", "message": f"missing required column: {col}", "field": col})

    dt_col = columns.get("datetime_col")
    inst_col = columns.get("instrument_col")
    label_cols = columns.get("label_columns", [])
    feature_cols = columns.get("feature_columns", [])

    if dt_col in df.columns:
        parsed = pd.to_datetime(df[dt_col], errors="coerce")
        if parsed.isna().all():
            blocking.append({"severity": "error", "code": "datetime_parse_failed", "message": "datetime column failed to parse", "field": dt_col})
    else:
        blocking.append({"severity": "error", "code": "missing_datetime_col", "message": "datetime column missing", "field": "datetime_col"})

    if inst_col in df.columns:
        if df[inst_col].astype(str).str.strip().eq("").all():
            blocking.append({"severity": "error", "code": "empty_instrument", "message": "instrument column is empty", "field": inst_col})
    else:
        blocking.append({"severity": "error", "code": "missing_instrument_col", "message": "instrument column missing", "field": "instrument_col"})

    for c in feature_cols:
        if c in df.columns and not pd.api.types.is_numeric_dtype(df[c]):
            warnings.append({"severity": "warning", "code": "non_numeric_feature", "message": f"feature column is non-numeric: {c}", "field": c})

    for c in label_cols:
        if c in df.columns and df[c].notna().sum() == 0:
            blocking.append({"severity": "error", "code": "empty_label_distribution", "message": f"label column has no non-null values: {c}", "field": c})

    if not isinstance(splits, dict) or ("available" not in splits and "train" not in splits):
        warnings.append({"severity": "warning", "code": "missing_split_metadata", "message": "split metadata unavailable", "field": "splits"})

    status = "fail" if blocking else ("pass_with_warnings" if warnings else "pass")
    return {
        "schema_version": "v1",
        "status": status,
        "checked_paths": checked_paths,
        "row_count": int(len(df)),
        "feature_count": int(len(feature_cols)),
        "label_count": int(len(label_cols)),
        "warnings": warnings,
        "blocking_issues": blocking,
        "next_phase_recommendation": "proceed to Phase 86-95 model/experiment bridge" if status != "fail" else "fix blocking issues first",
        "manifest_status": manifest.get("status", "unknown"),
    }
