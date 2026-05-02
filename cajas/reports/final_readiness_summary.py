"""Render markdown final readiness summary."""

from __future__ import annotations


def render_final_readiness_summary(*, packet: dict) -> str:
    lines = [
        "# Final Readiness Summary",
        "",
        f"- final_status: `{packet.get('final_status')}`",
        f"- gate_status: `{packet.get('gate_summary', {}).get('final_status')}`",
        f"- reproducibility_status: `{packet.get('reproducibility_summary', {}).get('final_status')}`",
        f"- stable_reproducibility_status: `{packet.get('stable_reproducibility_summary', {}).get('final_status')}`",
        f"- reproducibility_explanation_status: `{packet.get('stable_reproducibility_summary', {}).get('explanation_status')}`",
        f"- governance_remediation_status: `{packet.get('governance_remediation_summary', {}).get('final_suggested_status')}`",
        f"- ci_tiers: `{packet.get('ci_plan_summary', {}).get('tier_count')}`",
        "",
        "## Stable Reproducibility",
        f"- normalized_artifact_count: `{packet.get('stable_reproducibility_summary', {}).get('normalized_artifact_count')}`",
        f"- true_mismatch_count: `{packet.get('stable_reproducibility_summary', {}).get('true_mismatch_count')}`",
        f"- expected_variability_count: `{packet.get('stable_reproducibility_summary', {}).get('expected_variability_count')}`",
        "",
        "## Missing Artifacts",
    ]
    missing = packet.get("manifest_summary", {}).get("missing_artifacts", [])
    if not missing:
        lines.append("- none")
    else:
        for m in missing:
            lines.append(f"- `{m}`")

    lines += ["", "## Blocked Actions"]
    blocked = packet.get("blocked_actions", [])
    if not blocked:
        lines.append("- none")
    else:
        for b in blocked:
            if isinstance(b, dict):
                lines.append(f"- {b.get('action')}: {b.get('reason')}")
            else:
                lines.append(f"- {b}")

    lines += ["", "## Manual Checklist"]
    for item in packet.get("manual_review_checklist", []):
        lines.append(f"- {item.get('item')}: {item.get('rationale')}")
    lines += ["", "## Unresolved True Violations"]
    violations = packet.get("unresolved_true_violations", [])
    if not violations:
        lines.append("- none")
    else:
        for item in violations:
            lines.append(f"- `{item.get('file')}:{item.get('line')}` `{item.get('category')}`")

    lines += ["", "## Next Phase Options", "- Continue research-only manual review", "- Improve reproducibility parity", "- Keep no-broker boundary before any future planning"]
    return "\n".join(lines) + "\n"
