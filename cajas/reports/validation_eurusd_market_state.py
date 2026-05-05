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
    "range_high_3", "range_low_3", "range_high_8", "range_low_8", "range_high_24", "range_low_24", "range_high_128", "range_low_128",
    "range_position_3", "range_position_8", "range_position_24", "range_position_128",
    "range_width_3", "range_width_8", "range_width_24", "range_width_128",
    "range_ratio_3_8", "range_ratio_8_128", "range_ratio_24_128",
    "volatility_state_3", "volatility_state_8", "volatility_state_24", "volatility_state_128",
    "body_ratio_latest", "upper_wick_ratio_latest", "lower_wick_ratio_latest", "directional_body_latest", "latest_close_position_in_candle",
    "three_bar_direction_change", "three_bar_reversal_score", "three_bar_rejection_score",
    "latest_bar_breaks_prior_3_high", "latest_bar_breaks_prior_3_low", "latest_bar_returns_inside_prior_3_range",
    "higher_high_count_24", "higher_low_count_24", "lower_high_count_24", "lower_low_count_24",
    "higher_high_count_128", "higher_low_count_128", "lower_high_count_128", "lower_low_count_128",
    "gap_count_128", "largest_gap_hours_128",
]
STATE_COLUMNS = [
    "ultra_short_state_3",
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
        "ultra_short_window_bars": ULTRA_SHORT_WINDOW_BARS,
        "short_window_bars": SHORT_WINDOW_BARS,
        "mid_window_bars": MID_WINDOW_BARS,
        "long_window_bars": LONG_WINDOW_BARS,
        "state_distribution": summary.get("state_distribution", {}),
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
        f"- market_state_rule_version: `{report.get('market_state_rule_version')}`",
        f"- input_row_count: `{report.get('input_row_count')}`",
        f"- output_row_count: `{report.get('output_row_count')}`",
        f"- ultra_short_window_bars: `{report.get('ultra_short_window_bars')}`",
        f"- short_window_bars: `{report.get('short_window_bars')}`",
        f"- mid_window_bars: `{report.get('mid_window_bars')}`",
        f"- long_window_bars: `{report.get('long_window_bars')}`",
        f"- unknown_state_count: `{report.get('unknown_state_count')}`",
        f"- gap_caveat_count: `{report.get('gap_caveat_count')}`",
        f"- feature_columns_present: `{report.get('feature_columns_present')}`",
        f"- state_columns_present: `{report.get('state_columns_present')}`",
        f"- rationale_zh_present: `{report.get('rationale_zh_present')}`",
        f"- trading_outputs_excluded: `{report.get('trading_outputs_excluded')}`",
        f"- real_llm_integration_approved: `{report.get('real_llm_integration_approved')}`",
        f"- trial_approval_status: `{report.get('trial_approval_status')}`",
        f"- recommended_next_phase: `{report.get('recommended_next_phase')}`",
        "",
        "## Confidence Distribution",
        "",
        f"- {report.get('confidence_distribution')}",
        "",
        "## State Distribution",
        "",
        f"- {report.get('state_distribution')}",
    ]
    reasons = report.get("blocking_reasons") or []
    lines.extend(["", "## Blocking Reasons", ""])
    if reasons:
        lines.extend([f"- {r}" for r in reasons])
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"
