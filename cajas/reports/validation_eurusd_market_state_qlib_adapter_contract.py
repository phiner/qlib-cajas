"""Qlib adapter contract for EURUSD market-state dataset."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def build_market_state_qlib_adapter_contract_report(market_state_csv: Path, trial_approval_json: Path) -> dict[str, Any]:
    if not market_state_csv.exists():
        return {"report_status": "blocked", "reason": "market_state_csv_missing"}

    df = pd.read_csv(market_state_csv, nrows=5)
    required_feature_cols = ["micro_pattern_event_3", "short_term_state_8", "mid_term_state_24", "long_term_state_128", "return_8", "return_24", "return_128"]
    feature_ok = all(c in df.columns for c in required_feature_cols)
    label_ok = all(c in df.columns for c in ["local_structure_state", "structure_confidence"])

    trial_status = "not_approved"
    t = _load_json(trial_approval_json)
    if t:
        trial_status = str(t.get("status", "not_approved"))

    status = "qlib_adapter_contract_ready"
    if not feature_ok or not label_ok or trial_status != "not_approved":
        status = "blocked"

    return {
        "report_status": status,
        "instrument_column": "symbol",
        "datetime_column": "timestamp",
        "frequency": "15m",
        "feature_columns_defined": feature_ok,
        "label_columns_defined": label_ok,
        "future_human_label_columns_defined": True,
        "leakage_rules_documented": True,
        "time_split_required": True,
        "qlib_core_modification_required": False,
        "model_training_deferred": True,
        "execution_excluded": True,
        "real_llm_integration_approved": False,
        "trial_approval_status": trial_status,
    }


def render_market_state_qlib_adapter_contract_markdown(report: dict[str, Any]) -> str:
    return "\n".join([
        "# EURUSD Market-state Qlib Adapter Contract",
        "",
        f"- report_status: `{report.get('report_status')}`",
        f"- feature_columns_defined: `{report.get('feature_columns_defined')}`",
        f"- label_columns_defined: `{report.get('label_columns_defined')}`",
        f"- time_split_required: `{report.get('time_split_required')}`",
    ]) + "\n"
