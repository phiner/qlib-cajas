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
) -> dict:
    blocked_actions = no_broker_packet.get("next_blocked_actions") or no_broker_packet.get("disabled_capabilities", [])
    repro_status = reproducibility_report.get("final_status")
    stable_repro_status = (stable_reproducibility_report or {}).get("final_status")
    gate_status = gate_packet.get("final_status")
    missing_artifacts = manifest.get("missing_artifact_paths", [])

    if stable_repro_status == "not_stable_reproducible":
        final = "blocked"
    elif gate_status == "blocked":
        final = "blocked"
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
            "warnings": (stable_reproducibility_report or {}).get("warnings", []),
            "normalized_artifact_count": len((stable_reproducibility_report or {}).get("matching_normalized_artifacts", [])),
            "true_mismatch_count": int((stable_reproducibility_report or {}).get("true_mismatch_count", 0)),
            "expected_variability_count": int((stable_reproducibility_report or {}).get("expected_variability_absorbed_count", 0)),
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
    }
