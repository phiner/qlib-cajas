"""Localize current research readiness blockers."""

from __future__ import annotations


def _classify_repro_path(path: str) -> str:
    p = path.lower()
    if "registry" in p and p.endswith(".jsonl"):
        return "generated_id_drift"
    if "manifest" in p:
        return "run_metadata_drift"
    if "reproducibility_report" in p:
        return "normalizer_coverage_gap"
    return "unknown_semantic_drift"


def build_research_blocker_localization(
    *,
    stable_repro_report: dict,
    repro_explanation: dict,
    normalization_coverage: dict | None,
    governance_audit: dict,
    governance_remediation: dict,
    final_readiness: dict,
) -> dict:
    mismatches = []
    for item in stable_repro_report.get("changed_normalized_hashes", []):
        rel = item.get("relative_path", "")
        mismatches.append(
            {
                "relative_path": rel,
                "blocker_type": _classify_repro_path(rel),
                "recommended_fix": "Normalize non-semantic run metadata/ids and enforce deterministic serialization.",
                "expected_status_after_fix": "stable_reproducible_with_warnings",
            }
        )
    true_violations = governance_remediation.get("true_violations", [])
    gov_rows = []
    for item in true_violations:
        fp = str(item.get("file", "")).lower()
        source_type = "code"
        if "/tests/" in fp:
            source_type = "test_fixture"
        elif fp.endswith(".md"):
            source_type = "docs"
        elif "/tasks/" in fp:
            source_type = "prompt"
        gov_rows.append(
            {
                "file": item.get("file"),
                "line": item.get("line"),
                "category": item.get("category"),
                "source_type": source_type,
                "recommended_fix": "Treat self-audit implementation tokens as audit internals, not runtime violations.",
                "expected_status_after_fix": "needs_manual_review",
            }
        )
    return {
        "schema_version": "v1",
        "current_final_readiness": final_readiness.get("final_status"),
        "repro_classification": repro_explanation.get("classification"),
        "stable_repro_status": stable_repro_report.get("final_status"),
        "governance_status": governance_audit.get("status"),
        "governance_remediation_status": governance_remediation.get("final_suggested_status"),
        "repro_mismatch_blockers": mismatches,
        "governance_true_violations": gov_rows,
        "warnings": [] if normalization_coverage is not None else ["normalization_coverage missing"],
    }


def render_research_blocker_localization_md(*, report: dict) -> str:
    lines = [
        "# Research Blocker Localization",
        "",
        f"- current_final_readiness: `{report.get('current_final_readiness')}`",
        f"- stable_repro_status: `{report.get('stable_repro_status')}`",
        f"- repro_classification: `{report.get('repro_classification')}`",
        f"- governance_remediation_status: `{report.get('governance_remediation_status')}`",
        "",
        "## Reproducibility Blockers",
    ]
    for row in report.get("repro_mismatch_blockers", []):
        lines.append(f"- `{row.get('relative_path')}`: `{row.get('blocker_type')}`")
    lines += ["", "## Governance True Violations"]
    gov = report.get("governance_true_violations", [])
    if not gov:
        lines.append("- none")
    else:
        for row in gov:
            lines.append(f"- `{row.get('file')}:{row.get('line')}` `{row.get('category')}` `{row.get('source_type')}`")
    return "\n".join(lines) + "\n"
