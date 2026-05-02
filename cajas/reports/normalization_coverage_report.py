"""Build a conservative normalization coverage report."""

from __future__ import annotations

from pathlib import Path

from cajas.reports.normalization_rule_registry import get_normalization_rules


def build_normalization_coverage_report(*, stable_fingerprint: dict, artifacts_root: str | Path | None = None) -> dict:
    included = stable_fingerprint.get("included_files", [])
    types: dict[str, int] = {}
    for item in included:
        path = str(item.get("relative_path", ""))
        suffix = Path(path).suffix.lower() or "<none>"
        types[suffix] = types.get(suffix, 0) + 1

    supported = sorted([k for k in types if k in {".json", ".md"}])
    skipped = sorted([k for k in types if k not in {".json", ".md"}])
    rules = get_normalization_rules()
    candidate = []
    risky = []
    for rule in rules:
        row = {"rule_id": rule.rule_id, "risk_level": rule.risk_level, "description": rule.description}
        if rule.risk_level == "low":
            candidate.append(row)
        else:
            risky.append(row)

    return {
        "schema_version": "v1",
        "artifacts_root": "" if artifacts_root is None else str(Path(artifacts_root).expanduser().resolve()),
        "supported_file_types": supported,
        "skipped_file_types": skipped,
        "normalized_field_paths": ["created_at_utc", "timestamp", "working_directory", "root", "absolute_path", "string:tmp_paths", "string:run_labels"],
        "preserved_field_paths": ["metrics", "labels", "row_count", "status", "blocked_actions", "check_names"],
        "high_frequency_variable_fields": ["root", "absolute_path", "working_directory", "created_at_utc", "timestamp"],
        "candidate_new_normalization_rules": candidate,
        "risky_normalization_candidates": risky,
        "file_type_counts": types,
    }


def render_normalization_coverage_report_md(*, report: dict) -> str:
    lines = [
        "# Normalization Coverage Report",
        "",
        "## File Types",
        f"- supported_file_types: `{', '.join(report.get('supported_file_types', [])) or 'none'}`",
        f"- skipped_file_types: `{', '.join(report.get('skipped_file_types', [])) or 'none'}`",
        "",
        "## High-Frequency Variable Fields",
    ]
    for path in report.get("high_frequency_variable_fields", []):
        lines.append(f"- `{path}`")
    lines += ["", "## Candidate New Rules"]
    for row in report.get("candidate_new_normalization_rules", []):
        lines.append(f"- `{row.get('rule_id')}` ({row.get('risk_level')}): {row.get('description')}")
    lines += ["", "## Risky Candidates"]
    for row in report.get("risky_normalization_candidates", []):
        lines.append(f"- `{row.get('rule_id')}` ({row.get('risk_level')}): {row.get('description')}")
    return "\n".join(lines) + "\n"
