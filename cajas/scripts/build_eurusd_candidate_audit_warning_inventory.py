#!/usr/bin/env python3
"""Build EURUSD candidate-audit warning inventory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _warn(
    warning_id: str,
    section: str,
    description: str,
    affected_count: int,
    severity: str,
    classification: str,
    recommended_action: str,
    fix_now: bool,
    reason: str,
    affected_examples: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "warning_id": warning_id,
        "section": section,
        "description": description,
        "affected_count": int(affected_count),
        "affected_sample_ids": list(affected_examples or []),
        "severity": severity,
        "classification": classification,
        "recommended_action": recommended_action,
        "fix_now": bool(fix_now),
        "reason": reason,
    }


def build_warning_inventory(payload: dict[str, Any]) -> dict[str, Any]:
    warnings: list[dict[str, Any]] = []
    c = payload.get("causality_summary", {}) or {}
    e = payload.get("selection_explainability_summary", {}) or {}
    m = payload.get("multi_label_summary", {}) or {}
    d = payload.get("duplicate_region_summary", {}) or {}
    g = payload.get("audit_gates", {}) or {}
    bq = payload.get("batch_quality_metrics", {}) or {}

    missing_cols = c.get("missing_causality_columns", []) or []
    if missing_cols:
        warnings.append(
            _warn(
                "causality_columns_missing",
                "causality",
                "Required causality/future-usage fields are missing.",
                len(missing_cols),
                "critical",
                "must_fix_now",
                "add missing causality columns in candidate generation output",
                True,
                "audit cannot deterministically separate candidate logic vs review filter future usage",
                missing_cols[:10],
            )
        )
    if int(c.get("candidate_logic_uses_future_bars_true_count", 0)) > 0:
        warnings.append(
            _warn(
                "candidate_logic_future_usage_detected",
                "causality",
                "Selected batch rows include candidate logic using future bars.",
                int(c.get("candidate_logic_uses_future_bars_true_count", 0)),
                "critical",
                "must_fix_now",
                "remove future-bar dependency from candidate logic for selected rows",
                True,
                "causal boundary violated",
            )
        )
    if int(e.get("missing_selection_reason", 0)) > 0:
        warnings.append(
            _warn(
                "selected_rows_missing_primary_selection_reason",
                "explainability",
                "Selected rows are missing primary selection reason.",
                int(e.get("missing_selection_reason", 0)),
                "high",
                "must_fix_now",
                "populate primary_selection_reason for all selected rows",
                True,
                "selected sample explainability incomplete",
            )
        )
    if int(e.get("trend_missing_segment_metadata", 0)) > 0:
        warnings.append(
            _warn(
                "trend_rows_missing_segment_metadata",
                "explainability",
                "Selected trend rows are missing required segment metadata.",
                int(e.get("trend_missing_segment_metadata", 0)),
                "high",
                "must_fix_now",
                "populate segment metadata fields for trend selections",
                True,
                "trend selection provenance incomplete",
            )
        )
    if int(d.get("same_region_duplicates", 0)) > 0:
        warnings.append(
            _warn(
                "same_region_duplicates_present",
                "duplicate_region",
                "Batch contains same-region near-duplicate anchors.",
                int(d.get("same_region_duplicates", 0)),
                "medium",
                "should_fix_now",
                "tighten same-region cooldown and overlap thresholds",
                True,
                "review diversity risk",
            )
        )
    if int(m.get("timestamps_with_multiple_candidate_types", 0)) > 0:
        warnings.append(
            _warn(
                "multi_label_timestamps_present",
                "multi_label",
                "Candidate pool contains timestamps with multiple candidate types.",
                int(m.get("timestamps_with_multiple_candidate_types", 0)),
                "low",
                "acceptable_watch",
                "keep one primary candidate per timestamp in batch selection",
                False,
                "expected in rich candidate pool; manageable if batch deduplicates timestamp rows",
            )
        )
    for item in g.get("should_fix_failures", []) or []:
        warnings.append(
            _warn(
                f"gate_should_fix_{item}",
                "gates",
                f"Should-fix gate failed: {item}",
                1,
                "medium",
                "should_fix_now",
                "tune batch selection thresholds and fallback reasons",
                True,
                "quality gate regression",
            )
        )
    for item in bq.get("coverage_warnings", []) or []:
        warnings.append(
            _warn(
                f"coverage_{item}",
                "coverage",
                f"Coverage warning: {item}",
                1,
                "low",
                "future_extension",
                "improve stratified sampling controls over time",
                False,
                "non-blocking coverage optimization",
            )
        )

    by_classification: dict[str, int] = {}
    for w in warnings:
        by_classification[w["classification"]] = by_classification.get(w["classification"], 0) + 1
    return {
        "status": payload.get("status", "unknown"),
        "warning_count": len(warnings),
        "warning_count_by_classification": by_classification,
        "warnings": warnings,
    }


def render_inventory_md(inventory: dict[str, Any]) -> str:
    lines = [
        "# EURUSD Candidate Audit Warning Inventory",
        "",
        f"- status: `{inventory.get('status')}`",
        f"- warning_count: `{inventory.get('warning_count')}`",
        "",
        "## Classification Summary",
        "",
    ]
    for key, value in sorted((inventory.get("warning_count_by_classification") or {}).items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Warnings", ""])
    for w in inventory.get("warnings", []):
        lines.extend(
            [
                f"- `{w['warning_id']}` [{w['classification']}] severity={w['severity']} count={w['affected_count']}",
                f"  section={w['section']}; action={w['recommended_action']}",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build EURUSD candidate audit warning inventory")
    parser.add_argument("--audit-json", type=Path, default=Path("tmp/validation-eurusd-candidate-audit.json"))
    parser.add_argument("--output-json", type=Path, default=Path("tmp/validation-eurusd-candidate-audit-warning-inventory.json"))
    parser.add_argument("--output-md", type=Path, default=Path("tmp/validation-eurusd-candidate-audit-warning-inventory.md"))
    args = parser.parse_args()

    payload = json.loads(args.audit_json.read_text(encoding="utf-8"))
    inventory = build_warning_inventory(payload)
    args.output_json.write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    args.output_md.write_text(render_inventory_md(inventory), encoding="utf-8")
    print(json.dumps({"status": inventory.get("status"), "warning_count": inventory.get("warning_count")}))


if __name__ == "__main__":
    main()
