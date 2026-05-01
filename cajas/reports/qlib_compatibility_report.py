"""Compatibility report for Qlib research-boundary handoff."""

from __future__ import annotations

from .qlib_adapter_contract import ContractIssue


def build_qlib_compatibility_report(*, contract: dict, issues: list[ContractIssue], strict: bool = False) -> dict:
    blocking: list[dict] = []
    warnings: list[dict] = []
    for issue in issues:
        if issue.severity == "error":
            blocking.append(issue.to_dict())
        else:
            warnings.append(issue.to_dict())

    if contract.get("promotion_status") not in {"candidate_for_manual_review", "draft"}:
        blocking.append(
            ContractIssue("error", "promotion_status_not_acceptable", "promotion status is not acceptable for qlib handoff", "promotion_status").to_dict()
        )

    required_ids = ["candidate_id", "feature_set_id", "label_variant_id", "dataset_version", "target_name"]
    for key in required_ids:
        if not contract.get(key):
            blocking.append(ContractIssue("error", "missing_identifier", f"required identifier missing: {key}", key).to_dict())

    decision = "compatible_for_dry_run" if not blocking else "incompatible"
    if strict and warnings and decision == "compatible_for_dry_run":
        decision = "compatible_with_warnings"

    return {
        "compatibility_decision": decision,
        "blocking_issues": blocking,
        "non_blocking_warnings": warnings,
        "strict_mode": strict,
        "candidate_id": contract.get("candidate_id", ""),
    }
