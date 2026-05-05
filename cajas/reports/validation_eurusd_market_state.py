"""Validation/report builder for EURUSD market-state prototype dataset."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from cajas.research.eurusd_market_state import (
    LONG_WINDOW_BARS,
    MARKET_STATE_RULE_VERSION,
    MID_WINDOW_BARS,
    SHORT_WINDOW_BARS,
    ULTRA_SHORT_WINDOW_BARS,
    build_market_state_dataset,
    summarize_market_state_dataset,
    write_market_state_jsonl,
)

FORBIDDEN_FIELDS = {"trade_signal", "entry", "exit", "order", "position_size", "target_position"}
FEATURE_COLUMNS = [
    "return_1", "return_3", "return_8", "return_24", "return_128",
    "slope_3", "slope_8", "slope_24", "slope_128",
    "normalized_slope_3", "normalized_slope_8", "normalized_slope_24", "normalized_slope_128",
    "range_position_3", "range_position_8", "range_position_24", "range_position_128",
    "range_width_3", "range_width_8", "range_width_24", "range_width_128",
    "gap_count_128", "largest_gap_hours_128",
]
STATE_COLUMNS = [
    "micro_pattern_event_3",
    "micro_pattern_direction_3",
    "micro_pattern_strength_3",
    "micro_reversal_detected_3",
    "micro_rejection_detected_3",
    "micro_sweep_detected_3",
    "micro_event_rationale_zh",
    "micro_pattern_rule_version",
    "micro_pattern_rule_id",
    "short_term_state_8",
    "mid_term_state_24",
    "long_term_state_128",
    "local_structure_state",
    "structure_confidence",
    "market_state_rule_version",
    "market_state_rationale_zh",
]


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def build_market_state_report(
    *,
    input_csv: Path,
    output_csv: Path,
    output_jsonl: Path,
    trial_approval_json: Path,
) -> dict[str, Any]:
    if not input_csv.exists():
        return {
            "report_status": "blocked",
            "reason": "input_csv_missing",
            "input_csv": str(input_csv),
        }

    input_df = pd.read_csv(input_csv)
    dataset = build_market_state_dataset(input_df)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(output_csv, index=False)
    write_market_state_jsonl(dataset, str(output_jsonl))

    summary = summarize_market_state_dataset(dataset)

    trial_payload = _load_json(trial_approval_json) or {}
    trial_status = str(trial_payload.get("status", "not_approved"))
    real_llm_approved = trial_status not in {"not_approved", "blocked", ""}

    forbidden_found = sorted([c for c in dataset.columns if c.lower() in FORBIDDEN_FIELDS])
    trading_excluded = len(forbidden_found) == 0

    feature_columns_present = all(c in dataset.columns for c in FEATURE_COLUMNS)
    state_columns_present = all(c in dataset.columns for c in STATE_COLUMNS)
    rationale_zh_present = bool((dataset.get("market_state_rationale_zh", pd.Series(dtype=str)).fillna("").astype(str).str.strip() != "").any())

    report_status = "market_state_dataset_ready"
    reasons: list[str] = []
    if summary.get("status") != "ready":
        report_status = "blocked"
        reasons.append("summary_not_ready")
    if not trading_excluded:
        report_status = "blocked"
        reasons.append(f"forbidden_fields_present:{','.join(forbidden_found)}")
    if trial_status != "not_approved":
        report_status = "blocked"
        reasons.append(f"trial_approval_must_be_not_approved:{trial_status}")

    return {
        "report_status": report_status,
        "market_state_rule_version": MARKET_STATE_RULE_VERSION,
        "input_row_count": int(len(input_df)),
        "output_row_count": int(len(dataset)),
        "three_bar_logic_type": "pattern_event_rule_library",
        "structure_logic_type": "quantitative_8_24_128",
        "micro_pattern_rule_version": summary.get("micro_pattern_rule_version"),
        "micro_pattern_rules_loaded": bool(summary.get("micro_pattern_rule_count", 0) > 0),
        "micro_pattern_rule_count": int(summary.get("micro_pattern_rule_count", 0)),
        "ultra_short_window_bars": ULTRA_SHORT_WINDOW_BARS,
        "short_window_bars": SHORT_WINDOW_BARS,
        "mid_window_bars": MID_WINDOW_BARS,
        "long_window_bars": LONG_WINDOW_BARS,
        "micro_pattern_event_distribution": summary.get("micro_pattern_event_distribution", {}),
        "micro_pattern_direction_distribution": summary.get("micro_pattern_direction_distribution", {}),
        "micro_pattern_strength_distribution": summary.get("micro_pattern_strength_distribution", {}),
        "micro_reversal_count": int(summary.get("micro_reversal_count", 0)),
        "micro_rejection_count": int(summary.get("micro_rejection_count", 0)),
        "micro_sweep_count": int(summary.get("micro_sweep_count", 0)),
        "short_term_state_distribution": summary.get("short_term_state_distribution", {}),
        "mid_term_state_distribution": summary.get("mid_term_state_distribution", {}),
        "long_term_state_distribution": summary.get("long_term_state_distribution", {}),
        "local_structure_state_distribution": summary.get("local_structure_state_distribution", {}),
        "confidence_distribution": summary.get("confidence_distribution", {}),
        "unknown_state_count": int(summary.get("unknown_state_count", 0)),
        "gap_caveat_count": int(summary.get("gap_caveat_count", 0)),
        "feature_columns_present": feature_columns_present,
        "state_columns_present": state_columns_present,
        "rationale_zh_present": rationale_zh_present,
        "trading_outputs_excluded": trading_excluded,
        "real_llm_integration_approved": real_llm_approved,
        "trial_approval_status": trial_status,
        "recommended_next_phase": "wire_market_state_into_review_gui_and_artifacts",
        "blocking_reasons": reasons,
    }


def render_market_state_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# EURUSD Market State Validation",
        "",
        f"- report_status: `{report.get('report_status')}`",
        f"- three_bar_logic_type: `{report.get('three_bar_logic_type')}`",
        f"- structure_logic_type: `{report.get('structure_logic_type')}`",
        f"- micro_pattern_rule_version: `{report.get('micro_pattern_rule_version')}`",
        f"- micro_pattern_rules_loaded: `{report.get('micro_pattern_rules_loaded')}`",
        f"- micro_pattern_rule_count: `{report.get('micro_pattern_rule_count')}`",
        f"- market_state_rule_version: `{report.get('market_state_rule_version')}`",
        f"- input_row_count: `{report.get('input_row_count')}`",
        f"- output_row_count: `{report.get('output_row_count')}`",
        f"- trial_approval_status: `{report.get('trial_approval_status')}`",
        f"- trading_outputs_excluded: `{report.get('trading_outputs_excluded')}`",
        "",
        "## Micro Event Distributions",
        "",
        f"- event: {report.get('micro_pattern_event_distribution')}",
        f"- direction: {report.get('micro_pattern_direction_distribution')}",
        f"- strength: {report.get('micro_pattern_strength_distribution')}",
        f"- reversal_count: {report.get('micro_reversal_count')}",
        f"- rejection_count: {report.get('micro_rejection_count')}",
        f"- sweep_count: {report.get('micro_sweep_count')}",
        "",
        "## Structure Distributions",
        "",
        f"- short_term: {report.get('short_term_state_distribution')}",
        f"- mid_term: {report.get('mid_term_state_distribution')}",
        f"- long_term: {report.get('long_term_state_distribution')}",
        f"- local_structure: {report.get('local_structure_state_distribution')}",
        f"- confidence: {report.get('confidence_distribution')}",
    ]
    reasons = report.get("blocking_reasons") or []
    lines.extend(["", "## Blocking Reasons", ""])
    if reasons:
        lines.extend([f"- {r}" for r in reasons])
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"
