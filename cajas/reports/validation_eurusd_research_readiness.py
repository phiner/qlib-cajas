"""EURUSD 15m pattern research readiness packet."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cajas.research.eurusd_pattern_features import validate_feature_scaffold_contract


def _safe_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_validation_eurusd_research_readiness(
    *,
    base_maintenance_continuation_report: Path,
    dataset_contract_report: Path,
    dataset_audit_report: Path,
    clean_dataset_view_report: Path | None = None,
    pattern_candidate_pack_report: Path | None = None,
) -> dict[str, Any]:
    base = _safe_json(base_maintenance_continuation_report)
    contract = _safe_json(dataset_contract_report)
    audit = _safe_json(dataset_audit_report)
    clean_view = _safe_json(clean_dataset_view_report)
    candidate_pack = _safe_json(pattern_candidate_pack_report)
    feature = validate_feature_scaffold_contract()

    base_status = base.get("status", "missing")
    contract_status = contract.get("status", "missing")
    audit_status = audit.get("status", "missing")
    clean_view_status = clean_view.get("status", "missing")
    candidate_pack_status = candidate_pack.get("status", "missing")
    feature_status = feature.get("status", "fail")

    blockers: list[str] = []
    warnings: list[str] = []

    if base_status not in {"routine_continues", "ready"}:
        blockers.append("base_maintenance_not_ready")
    if contract_status != "ready":
        blockers.append("dataset_contract_not_ready")
    raw_blocked = audit_status == "blocked"
    clean_view_allows_research = clean_view_status in {"ready", "watch"}
    if raw_blocked and not clean_view_allows_research:
        blockers.append("dataset_audit_blocked")
    elif raw_blocked and clean_view_allows_research:
        warnings.append("raw_blocked_clean_view_used")
    if feature_status != "pass":
        blockers.append("feature_scaffold_failed")
    if candidate_pack and candidate_pack_status == "blocked":
        blockers.append("pattern_candidate_pack_blocked")

    if not blockers and audit_status == "watch":
        warnings.append("dataset_audit_watch_non_blocking")

    if blockers:
        status = "blocked"
    elif raw_blocked and clean_view_allows_research:
        status = "ready_for_pattern_research_with_clean_view"
    elif warnings:
        status = "watch"
    else:
        status = "ready_for_pattern_research"

    return {
        "schema_version": 1,
        "status": status,
        "blocking": bool(blockers),
        "blocking_reasons": blockers,
        "warnings": warnings,
        "symbol": "EURUSD",
        "timeframe": "15m",
        "price_side": "Bid",
        "base_maintenance_status": base_status,
        "dataset_contract_status": contract_status,
        "dataset_audit_status": audit_status,
        "raw_dataset_blocked": raw_blocked,
        "clean_dataset_view_status": clean_view_status,
        "clean_view_approved_for_pattern_research": clean_view_allows_research,
        "clean_view_path": (clean_view.get("output_paths") or {}).get("clean_csv"),
        "quarantine_count": clean_view.get("quarantined_row_count"),
        "pattern_candidate_pack_status": candidate_pack_status,
        "pattern_candidate_count": candidate_pack.get("candidate_count"),
        "next_action": "review_pattern_samples" if candidate_pack_status in {"ready", "watch"} else "build_or_review_candidate_pack",
        "feature_scaffold_status": feature_status,
        "feature_scaffold_details": feature,
        "scope_boundary": {
            "qlib_core_changes": False,
            "live_or_paper_trading": False,
            "broker_routing": False,
            "order_generation": False,
            "production_model_training": False,
            "timeframe_aggregation": False,
        },
        "next_research_path": [
            "validate eurusd dataset",
            "compute pattern features",
            "create manual label and review examples",
            "test simple non-execution strategy hypotheses offline",
            "later evaluate ml labels or model training",
        ],
    }


def render_validation_eurusd_research_readiness_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Validation EURUSD Research Readiness",
        "",
        f"- status: `{payload.get('status')}`",
        f"- blocking: `{payload.get('blocking')}`",
        f"- base_maintenance_status: `{payload.get('base_maintenance_status')}`",
        f"- dataset_contract_status: `{payload.get('dataset_contract_status')}`",
        f"- dataset_audit_status: `{payload.get('dataset_audit_status')}`",
        f"- raw_dataset_blocked: `{payload.get('raw_dataset_blocked')}`",
        f"- clean_dataset_view_status: `{payload.get('clean_dataset_view_status')}`",
        f"- clean_view_approved_for_pattern_research: `{payload.get('clean_view_approved_for_pattern_research')}`",
        f"- clean_view_path: `{payload.get('clean_view_path')}`",
        f"- quarantine_count: `{payload.get('quarantine_count')}`",
        f"- pattern_candidate_pack_status: `{payload.get('pattern_candidate_pack_status')}`",
        f"- pattern_candidate_count: `{payload.get('pattern_candidate_count')}`",
        f"- next_action: `{payload.get('next_action')}`",
        f"- feature_scaffold_status: `{payload.get('feature_scaffold_status')}`",
        "",
        "## Scope Boundary",
        "",
        f"- `{payload.get('scope_boundary', {})}`",
        "",
        "## Next Research Path",
        "",
    ]
    lines.extend(f"- {item}" for item in payload.get("next_research_path", []))
    lines.extend(
        [
            "",
            "## Policy",
            "",
            "- Fixed to EURUSD 15m Bid research; no timeframe aggregation.",
            "- No live trading, broker routing, order generation, or production model training.",
            "- No Qlib core changes.",
            "",
        ]
    )
    return "\n".join(lines)
