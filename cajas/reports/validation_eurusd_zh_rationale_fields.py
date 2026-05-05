"""Validation report for first-class Chinese rationale fields in EURUSD review workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cajas.research.eurusd_review_schema import CANONICAL_REVIEW_FIELDS, DEFAULT_REVIEW_VALUES

REQUIRED_ZH_FIELDS = [
    "human_rationale_zh",
    "human_counterexample_zh",
    "human_uncertainty_reason_zh",
    "human_context_notes_zh",
]


def _is_runtime_identifier_english(value: str) -> bool:
    return bool(value) and value.isascii() and value.replace("_", "").isalnum() and value == value.lower()


def build_zh_rationale_fields_report(
    *,
    policy_doc_path: Path,
    app_path: Path,
    helper_path: Path,
) -> dict[str, Any]:
    missing_paths = [str(p) for p in [policy_doc_path, app_path, helper_path] if not p.exists()]
    if missing_paths:
        return {
            "status": "blocked",
            "reason": "missing_required_paths",
            "missing_paths": missing_paths,
        }

    policy_text = policy_doc_path.read_text(encoding="utf-8")
    app_text = app_path.read_text(encoding="utf-8")
    helper_text = helper_path.read_text(encoding="utf-8")

    policy_mentions_fields = all(field in policy_text for field in REQUIRED_ZH_FIELDS)
    schema_fields_present = all(field in CANONICAL_REVIEW_FIELDS for field in REQUIRED_ZH_FIELDS)
    schema_defaults_present = all(field in DEFAULT_REVIEW_VALUES for field in REQUIRED_ZH_FIELDS)
    helper_optional_text_fields_present = all(field in helper_text for field in REQUIRED_ZH_FIELDS)
    app_exposes_zh_inputs = all(field in app_text for field in REQUIRED_ZH_FIELDS)
    app_has_bilingual_labels = all(
        token in app_text
        for token in [
            "Human rationale (ZH) / 人工判断理由",
            "Counterexample notes (ZH) / 反例/否定理由",
            "Uncertainty reason (ZH) / 不确定原因",
            "Context notes (ZH) / 上下文备注",
        ]
    )
    runtime_field_names_english = all(_is_runtime_identifier_english(field) for field in REQUIRED_ZH_FIELDS)
    non_english_schema_keys = [field for field in CANONICAL_REVIEW_FIELDS if not _is_runtime_identifier_english(field)]

    checks = {
        "bilingual_policy_present": policy_doc_path.exists(),
        "required_zh_fields_documented": policy_mentions_fields,
        "required_zh_fields_in_schema": schema_fields_present,
        "required_zh_fields_have_defaults": schema_defaults_present,
        "csv_persistence_fields_known_by_helper": helper_optional_text_fields_present,
        "jsonl_review_fields_include_zh_via_canonical_row": helper_optional_text_fields_present,
        "gui_exposes_zh_rationale_inputs": app_exposes_zh_inputs and app_has_bilingual_labels,
        "runtime_field_names_remain_english": runtime_field_names_english and len(non_english_schema_keys) == 0,
    }
    status = "zh_rationale_fields_ready" if all(checks.values()) else "blocked"
    return {
        "status": status,
        "checks": checks,
        "required_zh_fields": REQUIRED_ZH_FIELDS,
        "non_english_schema_keys": non_english_schema_keys,
        "policy_doc_path": str(policy_doc_path),
        "app_path": str(app_path),
        "helper_path": str(helper_path),
    }


def format_zh_rationale_fields_markdown(report: dict[str, Any]) -> str:
    checks = report.get("checks", {})
    lines = [
        "# EURUSD ZH Rationale Fields Validation",
        "",
        f"**Status**: `{report['status']}`",
        "",
        "## Checks",
        "",
        f"- bilingual_policy_present: {checks.get('bilingual_policy_present')}",
        f"- required_zh_fields_documented: {checks.get('required_zh_fields_documented')}",
        f"- required_zh_fields_in_schema: {checks.get('required_zh_fields_in_schema')}",
        f"- required_zh_fields_have_defaults: {checks.get('required_zh_fields_have_defaults')}",
        f"- csv_persistence_fields_known_by_helper: {checks.get('csv_persistence_fields_known_by_helper')}",
        f"- jsonl_review_fields_include_zh_via_canonical_row: {checks.get('jsonl_review_fields_include_zh_via_canonical_row')}",
        f"- gui_exposes_zh_rationale_inputs: {checks.get('gui_exposes_zh_rationale_inputs')}",
        f"- runtime_field_names_remain_english: {checks.get('runtime_field_names_remain_english')}",
    ]
    return "\n".join(lines)
