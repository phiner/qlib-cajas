"""Build offline research-only approval packet."""

from __future__ import annotations


FORBIDDEN_SCOPE = [
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


def build_research_only_approval_packet(
    *,
    final_readiness_packet: dict,
    stable_reproducibility_report: dict,
    governance_remediation_report: dict,
    governance_review_decision: dict,
    offline_review_packet: dict,
    final_research_bundle: dict,
) -> dict:
    decision = governance_review_decision.get("decision")
    gov_status = governance_review_decision.get("governance_review_status")
    true_violation_count = int(governance_review_decision.get("true_execution_violation_count", 0))
    if true_violation_count > 0:
        status = "blocked"
    elif gov_status == "offline_research_governance_approved" and decision == "approve_offline_research_only":
        status = "offline_research_approved"
    elif decision == "rejected":
        status = "rejected"
    elif decision == "needs_changes":
        status = "needs_changes"
    else:
        status = "needs_manual_governance_review"

    return {
        "schema_version": "v1",
        "approval_status": status,
        "approved_scope": "offline_research_only",
        "explicitly_forbidden_scope": FORBIDDEN_SCOPE,
        "stable_reproducibility_status": stable_reproducibility_report.get("final_status"),
        "governance_review_status": gov_status,
        "final_readiness_status": final_readiness_packet.get("final_status"),
        "allowed_next_actions": [
            "continue offline feature research",
            "continue label/quality review",
            "run bounded CPU-only experiments",
            "improve reports",
            "prepare future design docs",
        ],
        "forbidden_next_actions": [
            "implement broker",
            "implement paper trading execution",
            "implement live data connection",
            "implement order routing",
            "optimize PnL",
        ],
        "reviewer_notes": governance_review_decision.get("notes", ""),
        "accepted_findings": governance_review_decision.get("accepted_findings", []),
        "audit_trail": {
            "final_readiness_status": final_readiness_packet.get("final_status"),
            "stable_reproducibility_status": stable_reproducibility_report.get("final_status"),
            "governance_remediation_status": governance_remediation_report.get("final_suggested_status"),
            "offline_review_state": offline_review_packet.get("overall_review_state"),
            "bundle_status": final_research_bundle.get("bundle_status"),
        },
    }


def render_research_only_approval_packet_md(*, packet: dict) -> str:
    lines = [
        "# Research-Only Approval Packet",
        "",
        f"- approval_status: `{packet.get('approval_status')}`",
        f"- approved_scope: `{packet.get('approved_scope')}`",
        f"- stable_reproducibility_status: `{packet.get('stable_reproducibility_status')}`",
        f"- governance_review_status: `{packet.get('governance_review_status')}`",
        "",
        "## Forbidden Scope",
    ]
    for item in packet.get("explicitly_forbidden_scope", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"

