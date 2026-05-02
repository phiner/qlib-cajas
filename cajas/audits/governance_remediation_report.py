"""Build governance remediation report from baseline audit findings."""

from __future__ import annotations

from cajas.audits.governance_finding_classifier import classify_governance_finding


def build_governance_remediation_report(*, governance_audit: dict) -> dict:
    findings = governance_audit.get("findings", [])
    classified = []
    counts: dict[str, int] = {}
    true_violations = []
    false_positive_candidates = []
    manual_review = []
    boundary_docs = []

    for item in findings:
        cls = classify_governance_finding(finding=item)
        row = dict(item)
        row["classification"] = cls
        classified.append(row)
        counts[cls] = counts.get(cls, 0) + 1
        if cls == "true_violation":
            true_violations.append(row)
        elif cls == "false_positive_candidate":
            false_positive_candidates.append(row)
        elif cls == "allowed_boundary_documentation":
            boundary_docs.append(row)
        elif cls == "needs_manual_review":
            manual_review.append(row)

    if true_violations:
        suggested = "fail"
    elif manual_review:
        suggested = "needs_manual_review"
    elif governance_audit.get("status") == "fail" and false_positive_candidates:
        suggested = "warn"
    else:
        suggested = "pass"

    return {
        "schema_version": "v1",
        "original_governance_status": governance_audit.get("status"),
        "finding_classification_counts": counts,
        "classified_findings": classified,
        "true_violations": true_violations,
        "allowed_boundary_documentation": boundary_docs,
        "false_positive_candidates": false_positive_candidates,
        "manual_review_findings": manual_review,
        "suggested_code_or_doc_remediation": [
            "Keep explicit no-broker/no-live boundaries in docs.",
            "Refactor ambiguous forbidden keyword usage in implementation files.",
        ],
        "suggested_allowlist_updates": [
            {
                "pattern": "no broker|do not add live trading|paper trading execution is blocked",
                "justification": "Boundary documentation statements should not be treated as execution violations.",
            }
        ],
        "final_suggested_status": suggested,
    }


def render_governance_remediation_report_md(*, report: dict) -> str:
    lines = [
        "# Governance Remediation Report",
        "",
        f"- original_governance_status: `{report.get('original_governance_status')}`",
        f"- final_suggested_status: `{report.get('final_suggested_status')}`",
        "",
        "## Classification Counts",
    ]
    for k, v in sorted(report.get("finding_classification_counts", {}).items()):
        lines.append(f"- {k}: `{v}`")
    lines += ["", "## True Violations"]
    tv = report.get("true_violations", [])
    if not tv:
        lines.append("- none")
    else:
        for item in tv:
            lines.append(f"- `{item.get('file')}:{item.get('line')}` `{item.get('category')}`")
    lines += ["", "## Manual Review Findings"]
    mr = report.get("manual_review_findings", [])
    if not mr:
        lines.append("- none")
    else:
        for item in mr:
            lines.append(f"- `{item.get('file')}:{item.get('line')}` `{item.get('category')}`")
    return "\n".join(lines) + "\n"

