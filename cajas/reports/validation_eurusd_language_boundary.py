"""EURUSD review bilingual language-boundary validation report."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cajas.research.eurusd_review_schema import ALLOWED_VALUES, CANONICAL_REVIEW_FIELDS


def _is_english_runtime_identifier(value: str) -> bool:
    return bool(value) and value.isascii() and value.replace("_", "").isalnum() and value == value.lower()


def _contains_all(text: str, required: list[str]) -> bool:
    lowered = text.lower()
    return all(item.lower() in lowered for item in required)


def build_language_boundary_report(policy_doc: Path, kickoff_doc: Path, roadmap_doc: Path) -> dict[str, Any]:
    missing_paths = [str(path) for path in [policy_doc, kickoff_doc, roadmap_doc] if not path.exists()]
    if missing_paths:
        return {
            "status": "blocked",
            "reason": "missing_required_docs",
            "missing_paths": missing_paths,
            "policy_doc_path": str(policy_doc),
            "kickoff_doc_path": str(kickoff_doc),
            "roadmap_doc_path": str(roadmap_doc),
            "machine_identifiers_english": False,
        }

    policy_text = policy_doc.read_text(encoding="utf-8")
    kickoff_text = kickoff_doc.read_text(encoding="utf-8")
    roadmap_text = roadmap_doc.read_text(encoding="utf-8")

    english_runtime_documented = _contains_all(
        policy_text,
        ["english runtime", "schema keys", "cli flags", "status enums"],
    )
    chinese_semantic_documented = _contains_all(
        policy_text,
        ["chinese semantic", "human rationale", "counterexample", "future llm"],
    )
    zh_suffix_documented = _contains_all(
        policy_text,
        ["_zh", "human_rationale_zh", "supporting_observations_zh"],
    )
    prohibited_direction_documented = _contains_all(
        policy_text,
        ["prohibited", "chinese schema keys", "chinese cli flags", "chinese enum values"],
    )
    kickoff_references_policy = "eurusd_review_language_policy.md" in kickoff_text
    roadmap_references_policy = "eurusd_review_language_policy.md" in roadmap_text

    all_fields = list(CANONICAL_REVIEW_FIELDS)
    all_enum_values = sorted({item for values in ALLOWED_VALUES.values() for item in values})
    non_english_runtime_fields = [field for field in all_fields if not _is_english_runtime_identifier(field)]
    non_english_enum_values = [value for value in all_enum_values if not _is_english_runtime_identifier(value)]
    machine_identifiers_english = not non_english_runtime_fields and not non_english_enum_values

    checks = {
        "english_runtime_policy_documented": english_runtime_documented,
        "chinese_semantic_policy_documented": chinese_semantic_documented,
        "zh_suffix_convention_documented": zh_suffix_documented,
        "prohibited_full_localization_documented": prohibited_direction_documented,
        "kickoff_references_policy": kickoff_references_policy,
        "roadmap_references_policy": roadmap_references_policy,
        "machine_identifiers_english": machine_identifiers_english,
    }

    status = "language_boundary_ready" if all(checks.values()) else "blocked"
    return {
        "status": status,
        "policy_doc_path": str(policy_doc),
        "kickoff_doc_path": str(kickoff_doc),
        "roadmap_doc_path": str(roadmap_doc),
        "checks": checks,
        "canonical_review_fields": all_fields,
        "non_english_runtime_fields": non_english_runtime_fields,
        "non_english_enum_values": non_english_enum_values,
    }


def format_language_boundary_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# EURUSD Language Boundary Validation",
        "",
        f"**Status**: `{report['status']}`",
        "",
        "## Document Paths",
        "",
        f"- Policy: `{report['policy_doc_path']}`",
        f"- Kickoff: `{report['kickoff_doc_path']}`",
        f"- Roadmap: `{report['roadmap_doc_path']}`",
    ]
    checks = report.get("checks", {})
    if checks:
        lines.extend(
            [
                "",
                "## Checks",
                "",
                f"- English runtime policy documented: {checks.get('english_runtime_policy_documented')}",
                f"- Chinese semantic policy documented: {checks.get('chinese_semantic_policy_documented')}",
                f"- `_zh` suffix convention documented: {checks.get('zh_suffix_convention_documented')}",
                f"- Prohibited full localization documented: {checks.get('prohibited_full_localization_documented')}",
                f"- Kickoff references policy: {checks.get('kickoff_references_policy')}",
                f"- Roadmap references policy: {checks.get('roadmap_references_policy')}",
                f"- Machine-facing identifiers remain English: {checks.get('machine_identifiers_english')}",
            ]
        )
    if report.get("non_english_runtime_fields"):
        lines.extend(["", "## Non-English Runtime Fields", ""])
        lines.extend([f"- `{field}`" for field in report["non_english_runtime_fields"]])
    if report.get("non_english_enum_values"):
        lines.extend(["", "## Non-English Enum Values", ""])
        lines.extend([f"- `{value}`" for value in report["non_english_enum_values"]])
    return "\n".join(lines)
