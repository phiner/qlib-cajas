"""Dataset-quality gate for EURUSD market-state artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

FORBIDDEN_FIELDS = {"trade_signal", "entry", "exit", "order", "position_size", "target_position"}
REQUIRED_MICRO = ["micro_pattern_event_3", "micro_pattern_direction_3", "micro_pattern_strength_3", "micro_pattern_rule_version"]
REQUIRED_STRUCTURE = ["short_term_state_8", "mid_term_state_24", "long_term_state_128", "local_structure_state", "structure_confidence"]
REQUIRED_FEATURES = ["range_position_3", "range_position_8", "range_position_24", "range_position_128", "return_3", "return_8", "return_24", "return_128"]
REQUIRED_RATIONALES = ["micro_event_rationale_zh", "market_state_rationale_zh"]
ALLOWED_CONF = {"low", "medium", "high", "unknown"}


def build_market_state_dataset_quality_report(market_state_csv: Path, market_state_jsonl: Path) -> dict[str, Any]:
    if not market_state_csv.exists() or not market_state_jsonl.exists():
        return {"report_status": "blocked", "reason": "market_state_artifact_missing"}

    df = pd.read_csv(market_state_csv)
    if len(df) == 0:
        return {"report_status": "blocked", "reason": "empty_dataset"}

    ts_parse = pd.to_datetime(df.get("timestamp", pd.Series(dtype=str)), utc=True, errors="coerce")
    ts_parseable = bool(ts_parse.notna().all())
    monotonic = bool(ts_parse.is_monotonic_increasing) if ts_parseable else False
    dup_count = int(ts_parse.duplicated().sum()) if ts_parseable else -1

    missing_micro = [c for c in REQUIRED_MICRO if c not in df.columns]
    missing_structure = [c for c in REQUIRED_STRUCTURE if c not in df.columns]
    missing_features = [c for c in REQUIRED_FEATURES if c not in df.columns]
    missing_rationales = [c for c in REQUIRED_RATIONALES if c not in df.columns]

    chinese_schema = [c for c in df.columns if any("\u4e00" <= ch <= "\u9fff" for ch in c)]
    forbidden = [c for c in df.columns if c.lower() in FORBIDDEN_FIELDS]

    rp_cols = [c for c in ["range_position_3", "range_position_8", "range_position_24", "range_position_128"] if c in df.columns]
    rp_ok = True
    for c in rp_cols:
        s = df[c].dropna()
        if len(s) and not (((s >= 0.0) & (s <= 1.0)).all()):
            rp_ok = False
            break

    conf_ok = True
    if "structure_confidence" in df.columns:
        values = set(df["structure_confidence"].fillna("unknown").astype(str).unique())
        conf_ok = values.issubset(ALLOWED_CONF)

    blocked_reasons = []
    for name, miss in [("missing_micro_fields", missing_micro), ("missing_structure_fields", missing_structure), ("missing_feature_fields", missing_features), ("missing_rationale_fields", missing_rationales)]:
        if miss:
            blocked_reasons.append(f"{name}:{','.join(miss)}")
    if not ts_parseable:
        blocked_reasons.append("timestamp_not_parseable")
    if chinese_schema:
        blocked_reasons.append("chinese_schema_keys_present")
    if forbidden:
        blocked_reasons.append("forbidden_trading_fields_present")
    if not rp_ok:
        blocked_reasons.append("range_position_out_of_bounds")
    if not conf_ok:
        blocked_reasons.append("invalid_confidence_enum")

    watch_reasons = []
    noise_ratio = float((df["micro_pattern_event_3"].astype(str) == "micro_noise").mean()) if "micro_pattern_event_3" in df.columns else 0.0
    if noise_ratio > 0.3:
        watch_reasons.append("micro_noise_overconcentrated")
    if not monotonic:
        watch_reasons.append("timestamp_not_monotonic")

    status = "market_state_dataset_quality_ready"
    if blocked_reasons:
        status = "blocked"
    elif watch_reasons:
        status = "market_state_dataset_quality_watch"

    return {
        "report_status": status,
        "row_count": int(len(df)),
        "timestamp_parseable": ts_parseable,
        "timestamp_monotonic": monotonic,
        "duplicate_timestamp_count": dup_count,
        "required_micro_fields_present": len(missing_micro) == 0,
        "required_structure_fields_present": len(missing_structure) == 0,
        "required_feature_fields_present": len(missing_features) == 0,
        "required_rationale_fields_present": len(missing_rationales) == 0,
        "no_chinese_schema_keys": len(chinese_schema) == 0,
        "trading_outputs_excluded": len(forbidden) == 0,
        "range_position_bounds_ok": rp_ok,
        "confidence_enum_ok": conf_ok,
        "market_state_rule_version_present": "market_state_rule_version" in df.columns,
        "micro_pattern_rule_version_present": "micro_pattern_rule_version" in df.columns,
        "gap_caveat_fields_present": all(c in df.columns for c in ["gap_count_128", "largest_gap_hours_128"]),
        "micro_noise_ratio": noise_ratio,
        "blocking_reasons": blocked_reasons,
        "watch_reasons": watch_reasons,
    }


def render_market_state_dataset_quality_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# EURUSD Market-state Dataset Quality",
        "",
        f"- report_status: `{report.get('report_status')}`",
        f"- row_count: `{report.get('row_count')}`",
        f"- duplicate_timestamp_count: `{report.get('duplicate_timestamp_count')}`",
        f"- micro_noise_ratio: `{report.get('micro_noise_ratio')}`",
    ]
    return "\n".join(lines) + "\n"
