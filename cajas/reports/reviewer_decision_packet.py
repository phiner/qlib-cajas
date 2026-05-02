"""Build reviewer decision packet for research-only readiness."""

from __future__ import annotations


ALLOWED_DECISIONS = {"research_review_approved", "needs_changes", "rejected"}


def build_reviewer_decision_packet(
    *,
    decision: dict,
    final_readiness_packet: dict,
    governance_remediation_report: dict | None = None,
    reproducibility_explanation: dict | None = None,
) -> dict:
    value = decision.get("decision")
    if value not in ALLOWED_DECISIONS:
        raise ValueError(f"invalid decision: {value}")

    return {
        "schema_version": "v1",
        "reviewer": decision.get("reviewer", "manual"),
        "decision": value,
        "notes": decision.get("notes", ""),
        "accepted_risks": decision.get("accepted_risks", []),
        "rejected_actions": decision.get("rejected_actions", []),
        "source_final_readiness_packet": final_readiness_packet,
        "source_governance_remediation_report": governance_remediation_report or {},
        "source_reproducibility_explanation": reproducibility_explanation or {},
        "next_allowed_steps": ["continue offline research documentation", "remediate flagged reproducibility/governance items"],
        "still_forbidden_steps": ["broker integration", "live trading", "paper trading execution", "order routing", "position sizing"],
    }

