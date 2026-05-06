"""Deterministic LLM-ready EURUSD review sample artifact export and validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from cajas.research.eurusd_pattern_review_gui import (
    default_review_values,
    extract_chart_window_with_diagnostics,
    load_clean_view,
    summarize_compressed_gap_axis,
    build_compressed_gap_axis,
)

ARTIFACT_VERSION = "eurusd_llm_review_sample_v0"
STANDARD_VERSION = "eurusd_15m_review_standard_v0"
REQUIRED_ZH_FIELDS = [
    "human_rationale_zh",
    "human_counterexample_zh",
    "human_uncertainty_reason_zh",
    "human_context_notes_zh",
]
MULTI_LAYER_EVIDENCE_FIELDS = [
    "human_pattern_3_agreement",
    "human_pattern_3_correct_label",
    "human_pattern_3_feedback_zh",
    "human_market_8_agreement",
    "human_market_8_correct_state",
    "human_market_8_feedback_zh",
    "human_market_24_agreement",
    "human_market_24_correct_state",
    "human_market_24_feedback_zh",
    "human_market_128_agreement",
    "human_market_128_correct_state",
    "human_market_128_feedback_zh",
    "human_local_structure_agreement",
    "human_local_structure_correct_state",
    "human_local_structure_feedback_zh",
    "human_definition_issue_zh",
    "human_rule_adjustment_suggestion_zh",
]
FORBIDDEN_OUTPUTS = [
    "trade_signal",
    "entry",
    "exit",
    "position_size",
    "pnl_prediction",
    "order_recommendation",
    "execution_instruction",
]


def _is_english_runtime_identifier(value: str) -> bool:
    return bool(value) and value.isascii() and value.replace("_", "").isalnum() and value == value.lower()


def _collect_non_english_keys(node: Any, prefix: str = "") -> list[str]:
    bad: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if not _is_english_runtime_identifier(str(key)):
                bad.append(path)
            bad.extend(_collect_non_english_keys(value, path))
    elif isinstance(node, list):
        for idx, item in enumerate(node):
            bad.extend(_collect_non_english_keys(item, f"{prefix}[{idx}]"))
    return bad


def _safe_float(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_text(value: Any, default: str = "") -> str:
    if value is None or pd.isna(value):
        return default
    text = str(value)
    if text.strip().lower() == "nan":
        return default
    return text


def _build_sample_row(sample: pd.Series, clean_view: pd.DataFrame, review: dict[str, Any]) -> dict[str, Any]:
    sample_ts = sample.get("timestamp")
    window, diagnostics = extract_chart_window_with_diagnostics(
        clean_view,
        sample_ts,
        lookback=72,
        forward=48,
        pre_context_ratio=0.6,
        full_ohlc_source=clean_view,
    )
    axis_info = build_compressed_gap_axis(window["timestamp"].tolist()) if not window.empty else {"display_axis": "unknown", "gaps": []}
    axis_summary = summarize_compressed_gap_axis(axis_info)
    target_row = clean_view.loc[clean_view["timestamp"] == pd.to_datetime(sample_ts, utc=True)]
    if target_row.empty:
        target = {"timestamp": _safe_text(sample_ts), "open": None, "high": None, "low": None, "close": None}
    else:
        tr = target_row.iloc[0]
        target = {
            "timestamp": _safe_text(tr.get("timestamp")),
            "open": _safe_float(tr.get("open")),
            "high": _safe_float(tr.get("high")),
            "low": _safe_float(tr.get("low")),
            "close": _safe_float(tr.get("close")),
        }

    return {
        "artifact_version": ARTIFACT_VERSION,
        "sample_id": _safe_text(sample.get("sample_id")),
        "symbol": "EURUSD",
        "timeframe": "15m",
        "candidate_type": _safe_text(sample.get("candidate_type")),
        "standard_version": STANDARD_VERSION,
        "language_policy": {
            "runtime_language": "en",
            "semantic_language": "zh",
            "zh_fields_authoritative": True,
        },
        "target_candle": target,
        "context_window": {
            "lookback_bars": 72,
            "forward_bars": 48,
            "target_index": diagnostics.get("target_index_in_window"),
            "window_bar_count": int(diagnostics.get("chart_window_row_count", 0)),
            "gap_count": int(axis_summary.get("time_gap_count", 0)),
            "largest_gap_hours": axis_summary.get("largest_gap_hours"),
        },
        "deterministic_diagnostics": {
            "display_axis": axis_summary.get("display_axis", "unknown"),
            "exact_match": bool(diagnostics.get("exact_timestamp_match_found", False)),
            "fallback_used": bool(diagnostics.get("nearest_fallback_used", False)),
        },
        "human_review": {
            "human_label": _safe_text(review.get("review_outcome"), "not_reviewed"),
            "human_confidence": _safe_text(review.get("review_confidence"), "not_reviewed"),
            "human_rationale_zh": _safe_text(review.get("human_rationale_zh")),
            "human_counterexample_zh": _safe_text(review.get("human_counterexample_zh")),
            "human_uncertainty_reason_zh": _safe_text(review.get("human_uncertainty_reason_zh")),
            "human_context_notes_zh": _safe_text(review.get("human_context_notes_zh")),
        },
        "multi_layer_evidence": {
            key: _safe_text(review.get(key), "not_reviewed" if not key.endswith("_zh") else "")
            for key in MULTI_LAYER_EVIDENCE_FIELDS
        },
        "future_llm_boundary": {
            "role": "second_reviewer",
            "allowed_tasks": [
                "review_pattern_validity",
                "identify_supporting_observations",
                "identify_counter_observations",
                "flag_uncertainty",
                "recommend_human_review",
            ],
            "forbidden_outputs": FORBIDDEN_OUTPUTS,
        },
    }


def build_llm_review_artifacts_report(
    *,
    batch_csv: Path,
    clean_view_csv: Path,
    completed_csv: Path,
    policy_doc: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not batch_csv.exists():
        return [], {"report_status": "blocked", "reason": "batch_csv_missing", "batch_csv": str(batch_csv)}
    if not clean_view_csv.exists():
        return [], {"report_status": "blocked", "reason": "clean_view_csv_missing", "clean_view_csv": str(clean_view_csv)}

    batch_df = pd.read_csv(batch_csv, parse_dates=["timestamp"])
    clean_view = load_clean_view(clean_view_csv)
    completed_df = pd.read_csv(completed_csv, parse_dates=["timestamp"]) if completed_csv.exists() else None
    defaults = default_review_values()

    review_by_sample: dict[str, dict[str, Any]] = {}
    if completed_df is not None and "sample_id" in completed_df.columns:
        latest = completed_df.drop_duplicates(subset=["sample_id"], keep="last")
        for _, row in latest.iterrows():
            review_by_sample[str(row["sample_id"])] = row.to_dict()

    artifacts: list[dict[str, Any]] = []
    reviewed_count = 0
    zh_presence_counts = {field: 0 for field in REQUIRED_ZH_FIELDS}
    required_row_keys = [
        "artifact_version", "sample_id", "symbol", "timeframe", "candidate_type", "standard_version",
        "language_policy", "target_candle", "context_window", "deterministic_diagnostics", "human_review", "multi_layer_evidence", "future_llm_boundary",
    ]
    missing_required_field_count = 0

    for _, sample in batch_df.iterrows():
        sample_id = str(sample.get("sample_id"))
        review = dict(defaults)
        review.update(review_by_sample.get(sample_id, {}))
        row = _build_sample_row(sample=sample, clean_view=clean_view, review=review)
        artifacts.append(row)
        if row["human_review"]["human_label"] != "not_reviewed":
            reviewed_count += 1
        for field in REQUIRED_ZH_FIELDS:
            if _safe_text(row["human_review"].get(field)):
                zh_presence_counts[field] += 1
        missing_required_field_count += sum(1 for key in required_row_keys if key not in row)

    non_english_schema_keys = _collect_non_english_keys(artifacts[0]) if artifacts else []
    language_boundary_present = policy_doc.exists()
    forbidden_output_boundary_present = all(
        item in FORBIDDEN_OUTPUTS for item in ["trade_signal", "entry", "exit", "position_size"]
    )
    report_status = "llm_review_artifacts_ready"
    if missing_required_field_count > 0 or non_english_schema_keys:
        report_status = "blocked"

    report = {
        "report_status": report_status,
        "artifact_version": ARTIFACT_VERSION,
        "artifact_row_count": len(artifacts),
        "reviewed_row_count": reviewed_count,
        "rationale_field_presence": zh_presence_counts,
        "language_boundary_present": language_boundary_present,
        "forbidden_output_boundary_present": forbidden_output_boundary_present,
        "schema_key_language_check": "pass" if not non_english_schema_keys else "blocked",
        "non_english_schema_keys": non_english_schema_keys,
        "missing_required_field_count": missing_required_field_count,
        "batch_csv": str(batch_csv),
        "clean_view_csv": str(clean_view_csv),
        "completed_csv": str(completed_csv),
    }
    return artifacts, report


def render_llm_review_artifacts_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# EURUSD LLM Review Artifacts Validation",
        "",
        f"**Status**: `{report['report_status']}`",
        "",
        f"- artifact_version: `{report['artifact_version']}`",
        f"- artifact_row_count: `{report['artifact_row_count']}`",
        f"- reviewed_row_count: `{report['reviewed_row_count']}`",
        f"- language_boundary_present: `{report['language_boundary_present']}`",
        f"- forbidden_output_boundary_present: `{report['forbidden_output_boundary_present']}`",
        f"- schema_key_language_check: `{report['schema_key_language_check']}`",
        f"- missing_required_field_count: `{report['missing_required_field_count']}`",
        "",
        "## Rationale Field Presence",
        "",
    ]
    for key, value in report.get("rationale_field_presence", {}).items():
        lines.append(f"- {key}: {value}")
    if report.get("non_english_schema_keys"):
        lines.extend(["", "## Non-English Schema Keys", ""])
        lines.extend([f"- `{item}`" for item in report["non_english_schema_keys"]])
    return "\n".join(lines)


def write_artifacts_jsonl(path: Path, artifacts: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fp:
        for row in artifacts:
            fp.write(json.dumps(row, ensure_ascii=True) + "\n")
