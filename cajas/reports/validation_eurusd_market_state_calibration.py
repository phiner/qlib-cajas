"""Calibration diagnostics for EURUSD market-state distributions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from cajas.reports.validation_eurusd_market_state import FORBIDDEN_FIELDS


REQUIRED_COLUMNS = [
    "micro_pattern_event_3",
    "micro_pattern_direction_3",
    "micro_pattern_strength_3",
    "short_term_state_8",
    "mid_term_state_24",
    "long_term_state_128",
    "local_structure_state",
    "structure_confidence",
]


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _distribution(df: pd.DataFrame, col: str) -> dict[str, int]:
    return {str(k): int(v) for k, v in df[col].fillna("unknown").astype(str).value_counts().items()}


def _dominant(dist: dict[str, int], total: int) -> tuple[str, float]:
    if total <= 0 or not dist:
        return "unknown", 0.0
    k = max(dist, key=dist.get)
    return k, float(dist[k]) / float(total)


def build_market_state_calibration_report(
    *,
    market_state_csv: Path,
    market_state_report_json: Path,
    trial_approval_json: Path,
) -> dict[str, Any]:
    if not market_state_csv.exists():
        return {
            "report_status": "blocked",
            "reason": "market_state_csv_missing",
            "market_state_csv": str(market_state_csv),
        }

    df = pd.read_csv(market_state_csv)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        return {
            "report_status": "blocked",
            "reason": "missing_required_market_state_columns",
            "missing_columns": missing,
        }

    total = int(len(df))
    micro_event_dist = _distribution(df, "micro_pattern_event_3")
    micro_direction_dist = _distribution(df, "micro_pattern_direction_3")
    micro_strength_dist = _distribution(df, "micro_pattern_strength_3")
    short_dist = _distribution(df, "short_term_state_8")
    mid_dist = _distribution(df, "mid_term_state_24")
    long_dist = _distribution(df, "long_term_state_128")
    local_dist = _distribution(df, "local_structure_state")
    conf_dist = _distribution(df, "structure_confidence")

    dominant_micro, dominant_micro_ratio = _dominant(micro_event_dist, total)
    dominant_structure, dominant_structure_ratio = _dominant(local_dist, total)

    warnings: list[str] = []
    if dominant_micro_ratio > 0.50:
        warnings.append("dominant_micro_event_overconcentrated")
    if (
        (micro_event_dist.get("micro_noise", 0) / max(total, 1) > 0.30)
        or (micro_event_dist.get("micro_compression", 0) / max(total, 1) > 0.30)
        or (micro_event_dist.get("unknown", 0) / max(total, 1) > 0.05)
    ):
        warnings.append("catch_all_micro_event_high")
    if dominant_structure_ratio > 0.60:
        warnings.append("dominant_structure_state_overconcentrated")
    if local_dist.get("unknown", 0) / max(total, 1) > 0.20:
        warnings.append("unknown_local_structure_high")
    if conf_dist.get("low", 0) / max(total, 1) > 0.80:
        warnings.append("low_confidence_dominant")

    threshold_sensitivity_notes = [
        "micro_compression uses strict compressed-range and low-body constraints",
        "breakout_attempt remains non-blocking and should be reviewed with 24/128 context",
    ]

    recommended_rule_adjustments: list[str] = []
    if "catch_all_micro_event_high" in warnings:
        recommended_rule_adjustments.append("review micro pause/compression thresholds and reclaim/reject precision")
    if "unknown_local_structure_high" in warnings:
        recommended_rule_adjustments.append("map more mid/long coherent combinations away from local unknown")
    if "low_confidence_dominant" in warnings:
        recommended_rule_adjustments.append("review confidence vote thresholds across 8/24/128 windows")

    manual_review_priority_states = []
    for k in ["micro_noise", "micro_compression", "unknown", dominant_micro, dominant_structure]:
        if k and k not in manual_review_priority_states:
            manual_review_priority_states.append(k)

    forbidden_found = sorted([c for c in df.columns if c.lower() in FORBIDDEN_FIELDS])

    market_state_report = _load_json(market_state_report_json) or {}
    trial_payload = _load_json(trial_approval_json) or {}
    trial_status = str(trial_payload.get("status", "not_approved"))

    reason_code_dist = {
        "micro_event_reason_code_distribution": _distribution(df, "micro_event_reason_code") if "micro_event_reason_code" in df.columns else {},
        "structure_reason_code_distribution": _distribution(df, "local_structure_reason_code") if "local_structure_reason_code" in df.columns else {},
        "confidence_reason_code_distribution": _distribution(df, "confidence_reason_code") if "confidence_reason_code" in df.columns else {},
    }

    report_status = "market_state_calibration_ready"
    if forbidden_found:
        report_status = "blocked"
    if trial_status != "not_approved":
        report_status = "blocked"

    return {
        "report_status": report_status,
        "input_row_count": total,
        "micro_pattern_event_distribution": micro_event_dist,
        "micro_pattern_direction_distribution": micro_direction_dist,
        "micro_pattern_strength_distribution": micro_strength_dist,
        "short_term_state_distribution": short_dist,
        "mid_term_state_distribution": mid_dist,
        "long_term_state_distribution": long_dist,
        "local_structure_state_distribution": local_dist,
        "confidence_distribution": conf_dist,
        "dominant_micro_event": dominant_micro,
        "dominant_micro_event_ratio": dominant_micro_ratio,
        "micro_noise_count": int(micro_event_dist.get("micro_noise", 0)),
        "micro_noise_ratio": float(micro_event_dist.get("micro_noise", 0)) / float(max(total, 1)),
        "micro_compression_ratio": float(micro_event_dist.get("micro_compression", 0)) / float(max(total, 1)),
        "dominant_structure_state": dominant_structure,
        "dominant_structure_state_ratio": dominant_structure_ratio,
        "catch_all_state_warnings": warnings,
        "threshold_sensitivity_notes": threshold_sensitivity_notes,
        "recommended_rule_adjustments": recommended_rule_adjustments,
        "manual_review_priority_states": manual_review_priority_states,
        "three_bar_logic_type": "pattern_event",
        "structure_logic_type": "quantitative_8_24_128",
        "real_llm_integration_approved": False,
        "trial_approval_status": trial_status,
        "reason_code_distribution": reason_code_dist,
        "market_state_report_status": market_state_report.get("report_status", "unknown"),
    }


def render_market_state_calibration_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# EURUSD Market State Calibration",
        "",
        f"- report_status: `{report.get('report_status')}`",
        f"- input_row_count: `{report.get('input_row_count')}`",
        f"- dominant_micro_event: `{report.get('dominant_micro_event')}` ({report.get('dominant_micro_event_ratio')})",
        f"- dominant_structure_state: `{report.get('dominant_structure_state')}` ({report.get('dominant_structure_state_ratio')})",
        f"- trial_approval_status: `{report.get('trial_approval_status')}`",
        "",
        "## Warnings",
        "",
    ]
    warnings = report.get("catch_all_state_warnings") or []
    if warnings:
        lines.extend([f"- {w}" for w in warnings])
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Micro Event Distribution",
            "",
            f"- {report.get('micro_pattern_event_distribution')}",
            "",
            "## Local Structure Distribution",
            "",
            f"- {report.get('local_structure_state_distribution')}",
            "",
            "## Reason Code Distribution",
            "",
            f"- {report.get('reason_code_distribution')}",
        ]
    )
    return "\n".join(lines) + "\n"
