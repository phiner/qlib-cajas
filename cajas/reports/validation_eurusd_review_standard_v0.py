"""Validation for human-governed EURUSD review standard v0 and example library."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REQUIRED_DECISIONS = {"valid", "invalid", "uncertain"}
REQUIRED_SCENARIO_TAGS = {"wick", "false_positive", "gap_caveat"}
FORBIDDEN_OUTPUT_KEYS = {
    "trade_signal",
    "entry",
    "exit",
    "position_size",
    "pnl_prediction",
    "order_recommendation",
    "execution_instruction",
}
REQUIRED_ZH_FIELDS = {"rationale_zh", "counter_observation_zh", "uncertainty_reason_zh", "context_notes_zh"}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        rows.append(json.loads(text))
    return rows


def _is_english_key(key: str) -> bool:
    return bool(key) and key.isascii() and key.replace("_", "").isalnum() and key == key.lower()


def build_review_standard_v0_report(*, standard_doc: Path, example_jsonl: Path, language_policy_doc: Path) -> dict[str, Any]:
    if not standard_doc.exists():
        return {"status": "blocked", "reason": "standard_doc_missing", "standard_doc": str(standard_doc)}
    if not example_jsonl.exists():
        return {"status": "blocked", "reason": "example_library_missing", "example_jsonl": str(example_jsonl)}
    if not language_policy_doc.exists():
        return {"status": "blocked", "reason": "language_policy_missing", "language_policy_doc": str(language_policy_doc)}

    standard_text = standard_doc.read_text(encoding="utf-8")
    rows = _read_jsonl(example_jsonl)
    decisions = {str(r.get("decision", "")) for r in rows}
    scenario_tags = {str(tag) for r in rows for tag in (r.get("scenario_tags") or [])}

    missing_decisions = sorted(REQUIRED_DECISIONS - decisions)
    missing_scenarios = sorted(REQUIRED_SCENARIO_TAGS - scenario_tags)
    non_english_keys: list[str] = []
    missing_zh_field_count = 0
    forbidden_output_violation_count = 0

    for row in rows:
        for key in row.keys():
            if not _is_english_key(str(key)):
                non_english_keys.append(str(key))
            if key in FORBIDDEN_OUTPUT_KEYS and bool(row.get(key)):
                forbidden_output_violation_count += 1
        for field in REQUIRED_ZH_FIELDS:
            if field not in row:
                missing_zh_field_count += 1
        if bool(row.get("forbidden_trade_output_present", False)):
            forbidden_output_violation_count += 1

    language_boundary_referenced = "eurusd_review_language_policy.md" in standard_text
    forbidden_outputs_listed = all(item in standard_text for item in ["trade_signal", "entry", "exit", "position_size"])

    status = "review_standard_v0_ready"
    if missing_decisions or missing_scenarios or non_english_keys or missing_zh_field_count > 0 or forbidden_output_violation_count > 0:
        status = "blocked"

    return {
        "status": status,
        "standard_doc_path": str(standard_doc),
        "example_library_path": str(example_jsonl),
        "language_boundary_referenced": language_boundary_referenced,
        "forbidden_outputs_listed": forbidden_outputs_listed,
        "example_count": len(rows),
        "decisions_present": sorted(decisions),
        "missing_decisions": missing_decisions,
        "scenario_tags_present": sorted(scenario_tags),
        "missing_required_scenarios": missing_scenarios,
        "all_keys_english": len(non_english_keys) == 0,
        "non_english_keys": sorted(set(non_english_keys)),
        "missing_zh_field_count": missing_zh_field_count,
        "forbidden_output_violation_count": forbidden_output_violation_count,
    }


def render_review_standard_v0_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# EURUSD Review Standard v0 Validation",
        "",
        f"**Status**: `{report.get('status')}`",
        "",
        f"- standard_doc_path: `{report.get('standard_doc_path')}`",
        f"- example_library_path: `{report.get('example_library_path')}`",
        f"- language_boundary_referenced: `{report.get('language_boundary_referenced')}`",
        f"- forbidden_outputs_listed: `{report.get('forbidden_outputs_listed')}`",
        f"- example_count: `{report.get('example_count')}`",
        f"- all_keys_english: `{report.get('all_keys_english')}`",
        f"- missing_zh_field_count: `{report.get('missing_zh_field_count')}`",
        f"- forbidden_output_violation_count: `{report.get('forbidden_output_violation_count')}`",
        "",
        "## Coverage",
        "",
        f"- decisions_present: `{report.get('decisions_present')}`",
        f"- missing_decisions: `{report.get('missing_decisions')}`",
        f"- scenario_tags_present: `{report.get('scenario_tags_present')}`",
        f"- missing_required_scenarios: `{report.get('missing_required_scenarios')}`",
    ]
    if report.get("non_english_keys"):
        lines.extend(["", "## Non-English Keys", ""])
        lines.extend([f"- `{item}`" for item in report["non_english_keys"]])
    return "\n".join(lines)
