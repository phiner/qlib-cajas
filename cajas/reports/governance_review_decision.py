"""Build manual governance review decision artifacts."""

from __future__ import annotations


ALLOWED_DECISIONS = {"approve_offline_research_only", "needs_changes", "rejected"}
FORBIDDEN_CAPABILITIES = [
    "broker integration",
    "live trading",
    "paper trading execution",
    "order generation",
    "order routing",
    "position sizing",
    "portfolio optimization",
    "PnL optimization",
    "execution simulation",
]


def build_governance_review_decision(
    *,
    governance_remediation_report: dict,
    final_readiness_packet: dict,
    stable_reproducibility_report: dict,
    decision: dict | None = None,
) -> dict:
    decision = decision or {}
    value = decision.get("decision")
    true_violations = governance_remediation_report.get("true_violations", [])
    has_true_violations = bool(true_violations)
    valid = value in ALLOWED_DECISIONS

    if has_true_violations:
        status = "blocked"
    elif not valid or value != "approve_offline_research_only":
        status = "needs_manual_governance_review"
    else:
        status = "offline_research_governance_approved"

    rejected_capabilities = decision.get("rejected_capabilities", [])
    merged_rejected = []
    for item in FORBIDDEN_CAPABILITIES + rejected_capabilities:
        if item not in merged_rejected:
            merged_rejected.append(item)

    return {
        "schema_version": "v1",
        "governance_review_status": status,
        "reviewer": decision.get("reviewer", "manual"),
        "decision": value if valid else "needs_changes",
        "scope": decision.get("scope", "offline_research_only"),
        "notes": decision.get("notes", ""),
        "accepted_findings": decision.get("accepted_findings", []),
        "rejected_capabilities": merged_rejected,
        "required_next_controls": decision.get("required_next_controls", []),
        "source_statuses": {
            "governance_remediation": governance_remediation_report.get("final_suggested_status"),
            "final_readiness": final_readiness_packet.get("final_status"),
            "stable_reproducibility": stable_reproducibility_report.get("final_status"),
        },
        "true_execution_violation_count": len(true_violations),
    }


def render_governance_review_decision_md(*, packet: dict) -> str:
    lines = [
        "# Governance Review Decision",
        "",
        f"- governance_review_status: `{packet.get('governance_review_status')}`",
        f"- decision: `{packet.get('decision')}`",
        f"- scope: `{packet.get('scope')}`",
        "",
        "## Rejected Capabilities",
    ]
    for item in packet.get("rejected_capabilities", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"

