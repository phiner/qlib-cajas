"""Offline human review packet builder."""

from __future__ import annotations


def build_offline_review_packet(
    *,
    final_readiness_packet: dict,
    stable_reproducibility_report: dict,
    governance_audit: dict,
    artifact_lineage: dict,
    run_catalog: dict,
    governance_review_decision: dict | None = None,
    research_only_approval_packet: dict | None = None,
) -> dict:
    fr = final_readiness_packet.get("final_status")
    sr = stable_reproducibility_report.get("final_status")
    gv = governance_audit.get("status")

    gov_review_status = (governance_review_decision or {}).get("governance_review_status")
    approval_status = (research_only_approval_packet or {}).get("approval_status")

    if approval_status == "offline_research_approved":
        state = "offline_research_approved"
    elif gv == "fail":
        state = "needs_governance_review"
    elif sr == "not_stable_reproducible":
        state = "needs_reproducibility_review"
    elif fr == "blocked":
        state = "blocked"
    else:
        state = "ready_for_human_review"

    return {
        "schema_version": "v1",
        "overall_review_state": state,
        "review_checklist": [
            "Confirm blocked actions remain explicit",
            "Review stable reproducibility mismatches",
            "Review governance findings",
            "Validate artifact lineage completeness",
        ],
        "reviewer_questions": [
            "Are mismatches semantic or environment-only?",
            "Any governance findings requiring refactor?",
            "Are manual follow-ups clearly documented?",
        ],
        "required_signoff_areas": ["reproducibility", "governance", "artifact_lineage", "readiness_boundaries"],
        "blocked_actions": final_readiness_packet.get("blocked_actions", []),
        "permitted_next_actions": final_readiness_packet.get("permitted_next_actions", []),
        "artifact_references": {
            "final_readiness_packet": final_readiness_packet.get("manifest_summary", {}).get("root"),
            "stable_reproducibility_status": sr,
            "governance_status": gv,
            "lineage_nodes": len(artifact_lineage.get("nodes", [])),
            "catalog_summary": run_catalog.get("summary", {}),
        },
        "unresolved_issues_summary": {
            "stable_repro_status": sr,
            "governance_status": gv,
            "final_readiness_status": fr,
            "governance_review_status": gov_review_status,
            "approval_status": approval_status,
        },
    }


def render_offline_review_packet_md(*, packet: dict) -> str:
    lines = ["# Offline Review Packet", "", f"- overall_review_state: `{packet.get('overall_review_state')}`", "", "## Review Checklist"]
    for x in packet.get("review_checklist", []):
        lines.append(f"- {x}")
    lines += ["", "## Blocked Actions"]
    for b in packet.get("blocked_actions", []):
        if isinstance(b, dict):
            lines.append(f"- {b.get('action')}: {b.get('reason')}")
        else:
            lines.append(f"- {b}")
    lines += ["", "## Reviewer Questions"]
    for q in packet.get("reviewer_questions", []):
        lines.append(f"- {q}")
    return "\n".join(lines) + "\n"
