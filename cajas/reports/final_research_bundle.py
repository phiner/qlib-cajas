"""Final consolidated research bundle builder."""

from __future__ import annotations


def build_final_research_bundle(
    *,
    root: str,
    final_readiness_packet: dict,
    final_readiness_summary_path: str,
    stable_repro_report: dict,
    governance_audit: dict,
    artifact_lineage: dict,
    run_catalog: dict,
    offline_review_packet: dict,
    ci_validation_plan: dict,
    governance_review_decision: dict | None = None,
    research_only_approval_packet: dict | None = None,
) -> dict:
    return {
        "schema_version": "v1",
        "bundle_status": offline_review_packet.get("overall_review_state", "blocked"),
        "root": root,
        "key_artifact_paths": {
            "final_readiness_summary": final_readiness_summary_path,
        },
        "top_level_statuses": {
            "final_readiness": final_readiness_packet.get("final_status"),
            "stable_reproducibility": stable_repro_report.get("final_status"),
            "governance": governance_audit.get("status"),
            "offline_review": offline_review_packet.get("overall_review_state"),
            "governance_review": (governance_review_decision or {}).get("governance_review_status"),
            "research_only_approval": (research_only_approval_packet or {}).get("approval_status"),
        },
        "known_risks": [
            "research-only stack; no execution semantics",
            "stable reproducibility may still flag semantic drift",
        ],
        "blocked_execution_actions": final_readiness_packet.get("blocked_actions", []),
        "next_allowed_steps": offline_review_packet.get("permitted_next_actions", []),
        "next_forbidden_steps": ["broker integration", "live execution", "paper execution", "pnl optimization"],
        "manual_review_checklist": offline_review_packet.get("review_checklist", []),
        "references": {
            "lineage_nodes": len(artifact_lineage.get("nodes", [])),
            "catalog_summary": run_catalog.get("summary", {}),
            "ci_tiers": len(ci_validation_plan.get("tiers", [])),
        },
    }


def render_final_research_bundle_md(*, bundle: dict) -> str:
    lines = ["# Final Research Bundle", "", f"- bundle_status: `{bundle.get('bundle_status')}`", "", "## Top-level Statuses"]
    for k, v in bundle.get("top_level_statuses", {}).items():
        lines.append(f"- {k}: `{v}`")
    lines += ["", "## Blocked Execution Actions"]
    for b in bundle.get("blocked_execution_actions", []):
        if isinstance(b, dict):
            lines.append(f"- {b.get('action')}: {b.get('reason')}")
        else:
            lines.append(f"- {b}")
    lines += ["", "## Next Allowed Steps"]
    for s in bundle.get("next_allowed_steps", []):
        lines.append(f"- {s}")
    return "\n".join(lines) + "\n"
