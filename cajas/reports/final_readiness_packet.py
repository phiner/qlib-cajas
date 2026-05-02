"""Build final readiness packet from gate/no-broker/repro/CI artifacts."""

from __future__ import annotations


def build_final_readiness_packet(
    *,
    gate_packet: dict,
    no_broker_packet: dict,
    manifest: dict,
    reproducibility_report: dict,
    ci_plan: dict,
    stable_reproducibility_report: dict | None = None,
    stable_reproducibility_explanation: dict | None = None,
    governance_remediation_report: dict | None = None,
    normalization_coverage_report: dict | None = None,
    governance_review_decision: dict | None = None,
    research_only_approval_packet: dict | None = None,
) -> dict:
    blocked_actions = no_broker_packet.get("next_blocked_actions") or no_broker_packet.get("disabled_capabilities", [])
    repro_status = reproducibility_report.get("final_status")
    stable_repro_status = (stable_reproducibility_report or {}).get("final_status")
    repro_explain_status = (stable_reproducibility_explanation or {}).get("classification")
    gate_status = gate_packet.get("final_status")
    missing_artifacts = manifest.get("missing_artifact_paths", [])
    governance_status = (governance_remediation_report or {}).get("final_suggested_status")
    true_violations = (governance_remediation_report or {}).get("true_violations", [])
    semantic_mismatch = repro_explain_status == "semantic_mismatch"
    normalization_gap = repro_explain_status in {"normalization_gap", "expected_variability_not_normalized"}
    manual_review_items = (governance_remediation_report or {}).get("manual_review_findings", [])
    governance_review_status = (governance_review_decision or {}).get("governance_review_status")
    approval_status = (research_only_approval_packet or {}).get("approval_status")

    gate_hard_block = gate_status == "blocked" and not blocked_actions

    if true_violations:
        final = "blocked"
    elif stable_repro_status == "not_stable_reproducible" and semantic_mismatch:
        final = "needs_reproducibility_review"
    elif stable_repro_status == "not_stable_reproducible":
        final = "blocked"
    elif gate_hard_block:
        final = "blocked"
    elif approval_status == "offline_research_approved" and governance_review_status == "offline_research_governance_approved":
        final = "offline_research_approved"
    elif governance_status == "needs_manual_review":
        final = "needs_manual_governance_review"
    elif governance_status == "warn" and manual_review_items:
        final = "needs_manual_governance_review"
    elif normalization_gap:
        final = "needs_normalization_review"
    elif missing_artifacts:
        final = "needs_artifact_review"
    elif stable_repro_status == "stable_reproducible_with_warnings":
        final = "needs_reproducibility_review"
    elif repro_status == "not_reproducible" and stable_repro_status == "stable_reproducible":
        final = "research_stack_ready_for_manual_review"
    elif repro_status == "not_reproducible":
        final = "needs_reproducibility_review"
    else:
        final = "research_stack_ready_for_manual_review"

    return {
        "schema_version": "v1",
        "final_status": final,
        "gate_summary": {"final_status": gate_status, "metric_summary": gate_packet.get("metric_summary", {})},
        "no_broker_summary": {"disabled_capabilities": no_broker_packet.get("disabled_capabilities", [])},
        "manifest_summary": {
            "root": manifest.get("root"),
            "artifact_count": len(manifest.get("artifact_inventory", [])),
            "missing_artifacts": missing_artifacts,
        },
        "reproducibility_summary": {"final_status": repro_status, "warnings": reproducibility_report.get("warnings", [])},
        "stable_reproducibility_summary": {
            "final_status": stable_repro_status,
            "explanation_status": repro_explain_status,
            "warnings": (stable_reproducibility_report or {}).get("warnings", []),
            "normalized_artifact_count": len((stable_reproducibility_report or {}).get("matching_normalized_artifacts", [])),
            "true_mismatch_count": int((stable_reproducibility_report or {}).get("true_mismatch_count", 0)),
            "expected_variability_count": int((stable_reproducibility_report or {}).get("expected_variability_absorbed_count", 0)),
        },
        "governance_remediation_summary": {
            "final_suggested_status": governance_status,
            "true_violation_count": len(true_violations),
            "manual_review_count": len(manual_review_items),
        },
        "normalization_coverage_summary": {
            "supported_file_types": (normalization_coverage_report or {}).get("supported_file_types", []),
            "candidate_rule_count": len((normalization_coverage_report or {}).get("candidate_new_normalization_rules", [])),
        },
        "governance_review_summary": {
            "governance_review_status": governance_review_status,
            "approval_status": approval_status,
        },
        "ci_plan_summary": {"tier_count": len(ci_plan.get("tiers", []))},
        "known_boundaries": [
            "no_qllib_core_modifications",
            "no_broker_or_order_execution",
            "no_pnl_optimization",
            "research_only_outputs",
        ],
        "blocked_actions": blocked_actions,
        "permitted_next_actions": ["manual artifact review", "manual threshold tuning", "prepare next planning phase"],
        "manual_review_checklist": gate_packet.get("manual_review_checklist", []),
        "unresolved_true_violations": true_violations,
        "unresolved_semantic_mismatches": (stable_reproducibility_report or {}).get("changed_normalized_hashes", []) if semantic_mismatch else [],
        "unresolved_normalization_gaps": (stable_reproducibility_report or {}).get("changed_normalized_hashes", []) if normalization_gap else [],
        "manual_review_items": manual_review_items,
    }
