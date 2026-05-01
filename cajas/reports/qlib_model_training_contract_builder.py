"""Build training contracts from offline handler/dataset artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .qlib_model_training_contract import ModelContractIssue, QlibModelTrainingContract, utc_now_iso


def build_qlib_model_training_contract(
    *,
    handler_input_path: str | Path,
    handler_manifest_path: str | Path,
    dataset_contract_path: str | Path,
    handler_smoke_report_path: str | Path,
    out_path: str | Path | None = None,
    run_id: str = "phase086_model_bridge",
    label_col: str | None = None,
    split_ratios: dict | None = None,
) -> dict:
    hp = Path(handler_input_path).expanduser().resolve()
    hm = Path(handler_manifest_path).expanduser().resolve()
    dc = Path(dataset_contract_path).expanduser().resolve()
    hs = Path(handler_smoke_report_path).expanduser().resolve()

    warnings: list[ModelContractIssue] = []
    blocking: list[ModelContractIssue] = []

    df = pd.read_csv(hp)
    manifest = json.loads(hm.read_text(encoding="utf-8"))
    dataset_contract = json.loads(dc.read_text(encoding="utf-8"))
    smoke = json.loads(hs.read_text(encoding="utf-8"))

    instrument_col = dataset_contract.get("instrument_col", "instrument")
    datetime_col = dataset_contract.get("datetime_col", "datetime")
    label_candidates = dataset_contract.get("label_columns", [])
    chosen_label = label_col or (label_candidates[0] if label_candidates else "future_direction_8")

    required = [instrument_col, datetime_col, chosen_label]
    for col in required:
        if col not in df.columns:
            blocking.append(ModelContractIssue("error", "missing_required_column", f"missing required column: {col}", col))

    feature_columns = [c for c in df.columns if c not in {instrument_col, datetime_col, chosen_label}]
    leakage_like = [c for c in feature_columns if c.startswith("future_") and c != chosen_label]
    if leakage_like:
        warnings.append(ModelContractIssue("warning", "potential_leakage_columns", "future-like columns detected in features", "feature_columns"))

    non_numeric = [c for c in feature_columns if c in df.columns and not pd.api.types.is_numeric_dtype(df[c])]
    if non_numeric:
        blocking.append(ModelContractIssue("error", "non_numeric_features", "non-numeric feature columns detected", "feature_columns"))

    if len(df) == 0:
        blocking.append(ModelContractIssue("error", "empty_dataset", "handler input has zero rows", "handler_input"))

    if smoke.get("status") == "fail":
        blocking.append(ModelContractIssue("error", "handler_smoke_failed", "handler smoke report indicates fail status", "handler_smoke_report"))

    readiness = "blocked" if blocking else ("ready_with_warnings" if warnings else "ready_for_training_smoke")

    contract = QlibModelTrainingContract(
        schema_version="v1",
        run_id=run_id,
        created_at_utc=utc_now_iso(),
        handler_input_path=str(hp),
        handler_manifest_path=str(hm),
        dataset_contract_path=str(dc),
        handler_smoke_report_path=str(hs),
        instrument_col=instrument_col,
        datetime_col=datetime_col,
        label_col=chosen_label,
        feature_columns=feature_columns,
        split_ratios=split_ratios or {"train": 0.7, "valid": 0.15, "test": 0.15},
        row_count=int(len(df)),
        warnings=[w.to_dict() for w in warnings],
        blocking_issues=[b.to_dict() for b in blocking],
        readiness_status=readiness,
    ).to_dict()

    if out_path is not None:
        out = Path(out_path).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(contract, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _ = manifest
    return contract
