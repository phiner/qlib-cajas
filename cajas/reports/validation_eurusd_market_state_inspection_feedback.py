"""Validate completed four-layer inspection feedback and summarize definition gaps."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

AGREEMENT_VALUES = {"", "agree", "disagree", "uncertain"}
FORBIDDEN_FIELDS = {"trade_signal", "entry", "exit", "order", "position_size", "target_position"}
LAYER_SPECS = [
    ("pattern_3", "human_pattern_3_agreement", "human_pattern_3_feedback_zh", "human_pattern_3_correct_label"),
    ("market_8", "human_market_8_agreement", "human_market_8_feedback_zh", "human_market_8_correct_state"),
    ("market_24", "human_market_24_agreement", "human_market_24_feedback_zh", "human_market_24_correct_state"),
    ("market_128", "human_market_128_agreement", "human_market_128_feedback_zh", "human_market_128_correct_state"),
    ("local_structure", "human_local_structure_agreement", "human_local_structure_feedback_zh", "human_local_structure_correct_state"),
]
REQUIRED_FIELDS = [x for _, a, f, c in LAYER_SPECS for x in (a, f, c)] + [
    "sample_id",
    "human_definition_issue_zh",
    "human_rule_adjustment_suggestion_zh",
    "review_updated_at_utc",
]


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def build_market_state_inspection_feedback_report(
    *,
    inspection_packet_csv: Path,
    completed_feedback_csv: Path,
    trial_approval_json: Path,
) -> dict[str, Any]:
    if not inspection_packet_csv.exists():
        return {
            "report_status": "blocked",
            "source_packet_row_count": 0,
            "completed_feedback_csv_exists": False,
            "reviewed_row_count": 0,
            "recommended_next_phase": "fix_inspection_feedback_schema",
            "real_llm_integration_approved": False,
            "trial_approval_status": "not_approved",
        }
    source = pd.read_csv(inspection_packet_csv)
    if not completed_feedback_csv.exists():
        return {
            "report_status": "awaiting_market_state_inspection_feedback",
            "source_packet_row_count": int(len(source)),
            "completed_feedback_csv_exists": False,
            "reviewed_row_count": 0,
            "agreement_distribution_by_layer": {},
            "disagreement_count_by_layer": {},
            "uncertain_count_by_layer": {},
            "missing_feedback_rationale_count": 0,
            "definition_issue_count": 0,
            "rule_adjustment_suggestion_count": 0,
            "top_corrected_pattern_labels": {},
            "top_corrected_market_states": {},
            "definition_gap_summary": {},
            "recommended_next_phase": "manual_inspect_four_layer_samples",
            "real_llm_integration_approved": False,
            "trial_approval_status": "not_approved",
        }

    completed = pd.read_csv(completed_feedback_csv)
    missing = [c for c in REQUIRED_FIELDS if c not in completed.columns]
    if missing:
        return {
            "report_status": "blocked",
            "source_packet_row_count": int(len(source)),
            "completed_feedback_csv_exists": True,
            "reviewed_row_count": 0,
            "blocking_reasons": [f"missing_required_fields:{','.join(missing)}"],
            "recommended_next_phase": "fix_inspection_feedback_schema",
            "real_llm_integration_approved": False,
            "trial_approval_status": "not_approved",
        }

    if int(completed["sample_id"].astype(str).duplicated().sum()) > 0:
        return {
            "report_status": "blocked",
            "source_packet_row_count": int(len(source)),
            "completed_feedback_csv_exists": True,
            "reviewed_row_count": 0,
            "blocking_reasons": ["duplicate_sample_id"],
            "recommended_next_phase": "fix_inspection_feedback_schema",
            "real_llm_integration_approved": False,
            "trial_approval_status": "not_approved",
        }

    chinese_schema = [c for c in completed.columns if any("\u4e00" <= ch <= "\u9fff" for ch in c)]
    forbidden = [c for c in completed.columns if c.lower() in FORBIDDEN_FIELDS]
    if chinese_schema or forbidden:
        reasons = []
        if chinese_schema:
            reasons.append("chinese_schema_keys_present")
        if forbidden:
            reasons.append("forbidden_trading_fields_present")
        return {
            "report_status": "blocked",
            "source_packet_row_count": int(len(source)),
            "completed_feedback_csv_exists": True,
            "reviewed_row_count": 0,
            "blocking_reasons": reasons,
            "recommended_next_phase": "fix_inspection_feedback_schema",
            "real_llm_integration_approved": False,
            "trial_approval_status": "not_approved",
        }

    invalid = []
    for _, agr_col, _, _ in LAYER_SPECS:
        values = set(completed[agr_col].fillna("").astype(str).str.strip().unique().tolist())
        bad = sorted(v for v in values if v not in AGREEMENT_VALUES)
        if bad:
            invalid.append(f"{agr_col}:{','.join(bad)}")
    if invalid:
        return {
            "report_status": "blocked",
            "source_packet_row_count": int(len(source)),
            "completed_feedback_csv_exists": True,
            "reviewed_row_count": 0,
            "blocking_reasons": [f"invalid_agreement_enum:{'|'.join(invalid)}"],
            "recommended_next_phase": "fix_inspection_feedback_schema",
            "real_llm_integration_approved": False,
            "trial_approval_status": "not_approved",
        }

    reviewed_mask = pd.Series([False] * len(completed))
    for _, agr_col, _, _ in LAYER_SPECS:
        reviewed_mask = reviewed_mask | (completed[agr_col].fillna("").astype(str).str.strip() != "")
    reviewed = completed[reviewed_mask].copy()
    if reviewed.empty:
        return {
            "report_status": "awaiting_market_state_inspection_feedback",
            "source_packet_row_count": int(len(source)),
            "completed_feedback_csv_exists": True,
            "reviewed_row_count": 0,
            "agreement_distribution_by_layer": {},
            "disagreement_count_by_layer": {},
            "uncertain_count_by_layer": {},
            "missing_feedback_rationale_count": 0,
            "definition_issue_count": 0,
            "rule_adjustment_suggestion_count": 0,
            "top_corrected_pattern_labels": {},
            "top_corrected_market_states": {},
            "definition_gap_summary": {},
            "recommended_next_phase": "manual_inspect_four_layer_samples",
            "real_llm_integration_approved": False,
            "trial_approval_status": "not_approved",
        }

    agreement_distribution_by_layer: dict[str, dict[str, int]] = {}
    disagreement_count_by_layer: dict[str, int] = {}
    uncertain_count_by_layer: dict[str, int] = {}
    missing_rationale = 0
    for layer, agr_col, fb_col, _ in LAYER_SPECS:
        vals = reviewed[agr_col].fillna("").astype(str).str.strip()
        agreement_distribution_by_layer[layer] = {str(k): int(v) for k, v in vals.value_counts().items()}
        disagreement_count_by_layer[layer] = int((vals == "disagree").sum())
        uncertain_count_by_layer[layer] = int((vals == "uncertain").sum())
        missing_rationale += int(((vals == "disagree") & (reviewed[fb_col].fillna("").astype(str).str.strip() == "")).sum())

    top_corrected_pattern_labels = {
        str(k): int(v)
        for k, v in reviewed["human_pattern_3_correct_label"].fillna("").astype(str).str.strip().value_counts().items()
        if str(k)
    }
    state_corrections = pd.concat(
        [
            reviewed["human_market_8_correct_state"],
            reviewed["human_market_24_correct_state"],
            reviewed["human_market_128_correct_state"],
            reviewed["human_local_structure_correct_state"],
        ]
    )
    top_corrected_market_states = {
        str(k): int(v)
        for k, v in state_corrections.fillna("").astype(str).str.strip().value_counts().items()
        if str(k)
    }

    definition_issue_count = int((reviewed["human_definition_issue_zh"].fillna("").astype(str).str.strip() != "").sum())
    rule_adjustment_suggestion_count = int(
        (reviewed["human_rule_adjustment_suggestion_zh"].fillna("").astype(str).str.strip() != "").sum()
    )

    trial_payload = _load_json(trial_approval_json) or {}
    trial_status = str(trial_payload.get("status", "not_approved"))
    if trial_status != "not_approved":
        report_status = "blocked"
        next_phase = "fix_inspection_feedback_schema"
    elif missing_rationale > 0:
        report_status = "market_state_inspection_feedback_watch"
        next_phase = "manual_inspect_four_layer_samples"
    else:
        report_status = "market_state_inspection_feedback_ready"
        next_phase = "summarize_market_state_definition_gaps"

    definition_gap_summary = {
        "most_disagreed_layer": max(disagreement_count_by_layer, key=disagreement_count_by_layer.get),
        "disagreement_count_by_layer": disagreement_count_by_layer,
        "taxonomy_issue_signals": definition_issue_count,
        "rule_adjustment_signals": rule_adjustment_suggestion_count,
    }

    return {
        "report_status": report_status,
        "source_packet_row_count": int(len(source)),
        "completed_feedback_csv_exists": True,
        "reviewed_row_count": int(len(reviewed)),
        "agreement_distribution_by_layer": agreement_distribution_by_layer,
        "disagreement_count_by_layer": disagreement_count_by_layer,
        "uncertain_count_by_layer": uncertain_count_by_layer,
        "missing_feedback_rationale_count": int(missing_rationale),
        "definition_issue_count": definition_issue_count,
        "rule_adjustment_suggestion_count": rule_adjustment_suggestion_count,
        "top_corrected_pattern_labels": top_corrected_pattern_labels,
        "top_corrected_market_states": top_corrected_market_states,
        "definition_gap_summary": definition_gap_summary,
        "recommended_next_phase": next_phase,
        "real_llm_integration_approved": False,
        "trial_approval_status": trial_status,
    }


def render_market_state_inspection_feedback_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# EURUSD Market-state Inspection Feedback",
        "",
        f"- report_status: `{report.get('report_status')}`",
        f"- reviewed_row_count: `{report.get('reviewed_row_count')}`",
        f"- missing_feedback_rationale_count: `{report.get('missing_feedback_rationale_count')}`",
        f"- recommended_next_phase: `{report.get('recommended_next_phase')}`",
        "",
        "## Definition Gap Summary",
        "",
        f"- {report.get('definition_gap_summary', {})}",
        "",
        "## Boundary",
        "",
        "- research-only feedback loop",
        "- no automatic taxonomy/rule changes",
        "- no LLM calls and no trading outputs",
        f"- trial approval: `{report.get('trial_approval_status')}`",
    ]
    return "\n".join(lines) + "\n"
