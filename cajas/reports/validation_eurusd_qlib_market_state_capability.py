"""Validation report for Qlib support of EURUSD market-state research."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def build_qlib_market_state_capability_report(*, audit_doc: Path, trial_approval_json: Path) -> dict[str, Any]:
    trial = _load_json(trial_approval_json)
    trial_status = str((trial or {}).get("status", "not_approved"))
    real_llm_approved = trial_status not in {"not_approved", "blocked", ""}

    if not audit_doc.exists():
        return {
            "report_status": "blocked",
            "reason": "audit_doc_missing",
            "trial_approval_status": trial_status,
            "real_llm_integration_approved": real_llm_approved,
        }

    short_horizon = {"min": 3, "max": 8}
    mid_horizon = {"min": 1, "max": 24}
    long_horizon = {"min": 1, "max": 64}

    report_status = "qlib_market_state_capability_ready"
    blocking_reasons: list[str] = []
    if trial_status != "not_approved":
        report_status = "blocked"
        blocking_reasons.append(f"trial_approval_must_remain_not_approved:{trial_status}")

    return {
        "report_status": report_status,
        "qlib_can_support_market_state_research": True,
        "requires_cajas_adapter": True,
        "qlib_core_modification_required": False,
        "short_horizon_bars": short_horizon,
        "mid_horizon_bars": mid_horizon,
        "long_horizon_bars": long_horizon,
        "feature_builder_required": True,
        "label_builder_required": True,
        "qlib_adapter_required": True,
        "human_review_layer_outside_qlib_core": True,
        "llm_layer_outside_qlib_core": True,
        "live_execution_excluded": True,
        "model_training_excluded_this_phase": True,
        "real_llm_integration_approved": real_llm_approved,
        "trial_approval_status": trial_status,
        "recommended_next_phase": "define_market_state_taxonomy_v0_and_feature_contract",
        "suitability_matrix": {
            "raw_15m_data_storage": "supports_with_cajas_adapter",
            "feature_engineering": "supports_with_cajas_adapter",
            "label_generation": "supports_with_cajas_adapter",
            "supervised_modeling": "supports_directly",
            "market_dynamics_modeling": "supports_with_cajas_adapter",
            "state_taxonomy_semantics": "not_suitable_current_scope",
            "human_review_rationale": "not_suitable_current_scope",
            "llm_second_review": "not_suitable_current_scope",
            "backtest_event_study": "supports_directly",
            "live_execution": "not_suitable_current_scope",
            "broker_integration": "not_suitable_current_scope",
        },
        "blocking_reasons": blocking_reasons,
    }


def render_qlib_market_state_capability_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# EURUSD Qlib Market-State Capability",
        "",
        f"- report_status: `{report.get('report_status')}`",
        f"- qlib_can_support_market_state_research: `{report.get('qlib_can_support_market_state_research')}`",
        f"- requires_cajas_adapter: `{report.get('requires_cajas_adapter')}`",
        f"- qlib_core_modification_required: `{report.get('qlib_core_modification_required')}`",
        f"- short_horizon_bars: `{report.get('short_horizon_bars')}`",
        f"- mid_horizon_bars: `{report.get('mid_horizon_bars')}`",
        f"- long_horizon_bars: `{report.get('long_horizon_bars')}`",
        f"- feature_builder_required: `{report.get('feature_builder_required')}`",
        f"- label_builder_required: `{report.get('label_builder_required')}`",
        f"- qlib_adapter_required: `{report.get('qlib_adapter_required')}`",
        f"- human_review_layer_outside_qlib_core: `{report.get('human_review_layer_outside_qlib_core')}`",
        f"- llm_layer_outside_qlib_core: `{report.get('llm_layer_outside_qlib_core')}`",
        f"- live_execution_excluded: `{report.get('live_execution_excluded')}`",
        f"- model_training_excluded_this_phase: `{report.get('model_training_excluded_this_phase')}`",
        f"- real_llm_integration_approved: `{report.get('real_llm_integration_approved')}`",
        f"- trial_approval_status: `{report.get('trial_approval_status')}`",
        f"- recommended_next_phase: `{report.get('recommended_next_phase')}`",
        "",
        "## Suitability Matrix",
        "",
    ]
    for k, v in (report.get("suitability_matrix") or {}).items():
        lines.append(f"- {k}: `{v}`")
    lines.extend(["", "## Blocking Reasons", ""])
    reasons = report.get("blocking_reasons") or []
    if reasons:
        lines.extend([f"- {r}" for r in reasons])
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"
