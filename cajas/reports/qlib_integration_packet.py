"""Dry-run Qlib integration packet builder."""

from __future__ import annotations

from .qlib_adapter_contract import ContractIssue


def build_qlib_integration_packet(*, contract: dict, issues: list[ContractIssue]) -> dict:
    blocking = [i.to_dict() for i in issues if i.severity == "error"]
    warnings = [i.to_dict() for i in issues if i.severity == "warning"]
    readiness = "ready_for_dry_run_trial" if not blocking and contract.get("promotion_status") == "candidate_for_manual_review" else "blocked"
    return {
        "adapter_contract_summary": {
            "contract_version": contract.get("contract_version"),
            "candidate_id": contract.get("candidate_id"),
            "research_run_id": contract.get("research_run_id"),
        },
        "required_datasets": [contract.get("dataset_version")],
        "required_feature_columns": contract.get("required_feature_columns", []),
        "required_label_columns": contract.get("required_label_columns", []),
        "expected_prediction_output_shape": {
            "rows": "same_as_input_rows",
            "columns": ["datetime", "instrument", "prediction", "score"],
        },
        "evaluation_artifacts": contract.get("artifact_paths", {}),
        "readiness_decision": readiness,
        "blocking_issues": blocking,
        "non_blocking_warnings": warnings,
        "next_manual_steps": [
            "Review blocking and warning issues with research owner.",
            "Confirm dataset and feature contracts before any Qlib workflow enablement.",
        ],
    }
