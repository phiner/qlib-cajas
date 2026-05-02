"""Schema contracts for dataset quality reports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ContractIssue:
    """Schema contract validation issue."""

    severity: str  # "error", "warning", "info"
    path: str
    message: str


@dataclass
class SchemaDiff:
    """Schema shape difference."""

    added_fields: list[str]
    removed_fields: list[str]
    type_changes: list[tuple[str, str, str]]
    is_breaking: bool


REQUIRED_REPORT_KEYS = {
    "dataset_quality_report": {
        "schema_version": str,
        "report_type": str,
        "status": str,
        "severity_counts": dict,
        "scope": str,
        "row_count": int,
        "column_count": int,
        "quality_score": dict,
        "label_diagnostics": list,
        "label_review_buckets": list,
        "time_coverage": dict,
        "feature_readiness": dict,
    },
    "label_coverage_diagnostics": {
        "schema_version": str,
        "scope": str,
        "label_diagnostics": list,
    },
    "time_coverage_diagnostics": {
        "schema_version": str,
        "scope": str,
        "time_coverage": dict,
    },
    "chunked_feature_dry_run": {
        "schema_version": str,
        "scope": str,
        "chunked_feature_dry_run": dict,
    },
    "feature_schema_manifest": {
        "schema_version": str,
        "features": list,
    },
    "offline_research_queue_summary": {
        "schema_version": str,
        "scope": str,
        "items": list,
        "ranked_review_items": list,
    },
}


def validate_report_contract(report: dict, report_type: str) -> list[ContractIssue]:
    """Validate report against schema contract."""
    issues = []
    if report_type not in REQUIRED_REPORT_KEYS:
        issues.append(ContractIssue("error", "", f"unknown report_type: {report_type}"))
        return issues

    required = REQUIRED_REPORT_KEYS[report_type]
    for key, expected_type in required.items():
        if key not in report:
            issues.append(ContractIssue("error", key, f"missing required key: {key}"))
        elif not isinstance(report[key], expected_type):
            actual_type = type(report[key]).__name__
            issues.append(ContractIssue("error", key, f"type mismatch: expected {expected_type.__name__}, got {actual_type}"))

    # Validate quality_score structure for dataset_quality_report
    if report_type == "dataset_quality_report" and "quality_score" in report:
        qs = report["quality_score"]
        for qkey in ["score", "max_score", "grade", "components"]:
            if qkey not in qs:
                issues.append(ContractIssue("error", f"quality_score.{qkey}", f"missing required key: {qkey}"))

    # Validate ranked_review_items structure for offline queue
    if report_type == "offline_research_queue_summary" and "ranked_review_items" in report:
        for idx, item in enumerate(report["ranked_review_items"]):
            for rkey in ["rank", "priority", "category", "title", "recommended_action"]:
                if rkey not in item:
                    issues.append(ContractIssue("warning", f"ranked_review_items[{idx}].{rkey}", f"missing key: {rkey}"))

    return issues


def validate_bundle_contract(bundle: dict) -> list[ContractIssue]:
    """Validate combined bundle contract."""
    issues = []
    expected_keys = ["dataset_quality_report", "feature_schema_manifest", "offline_research_queue_summary"]
    for key in expected_keys:
        if key not in bundle:
            issues.append(ContractIssue("error", key, f"missing bundle key: {key}"))
        else:
            issues.extend(validate_report_contract(bundle[key], key))
    return issues


def extract_schema_shape(value: Any, max_depth: int = 5, current_depth: int = 0) -> Any:
    """Extract schema shape from value."""
    if current_depth >= max_depth:
        return "..."
    if isinstance(value, dict):
        return {k: extract_schema_shape(v, max_depth, current_depth + 1) for k, v in value.items()}
    if isinstance(value, list):
        if not value:
            return []
        return [extract_schema_shape(value[0], max_depth, current_depth + 1)]
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "str"
    if isinstance(value, bool):
        return "bool"
    if value is None:
        return "null"
    return type(value).__name__


def compare_schema_shapes(old: dict, new: dict, path: str = "") -> SchemaDiff:
    """Compare two schema shapes."""
    added = []
    removed = []
    type_changes = []

    old_keys = set(old.keys()) if isinstance(old, dict) else set()
    new_keys = set(new.keys()) if isinstance(new, dict) else set()

    for key in new_keys - old_keys:
        added.append(f"{path}.{key}" if path else key)

    for key in old_keys - new_keys:
        removed.append(f"{path}.{key}" if path else key)

    for key in old_keys & new_keys:
        old_val = old[key]
        new_val = new[key]
        if isinstance(old_val, dict) and isinstance(new_val, dict):
            sub_diff = compare_schema_shapes(old_val, new_val, f"{path}.{key}" if path else key)
            added.extend(sub_diff.added_fields)
            removed.extend(sub_diff.removed_fields)
            type_changes.extend(sub_diff.type_changes)
        elif type(old_val) != type(new_val):
            full_path = f"{path}.{key}" if path else key
            type_changes.append((full_path, str(type(old_val)), str(type(new_val))))

    is_breaking = len(removed) > 0 or len(type_changes) > 0
    return SchemaDiff(added, removed, type_changes, is_breaking)
