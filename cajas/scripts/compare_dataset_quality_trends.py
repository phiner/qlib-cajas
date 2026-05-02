#!/usr/bin/env python3
"""Compare dataset quality trend snapshots."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def safe_json_write(path: Path, data: dict) -> None:
    """Write JSON safely."""
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def compare_trends(current: dict, previous: dict) -> dict:
    """Compare two trend snapshots."""
    changes = {}
    numeric_fields = [
        "quality_score",
        "error_count",
        "warning_count",
        "semantic_error_count",
        "semantic_warning_count",
        "drift_breaking_count",
        "drift_additive_count",
        "files_checked",
        "row_count",
        "column_count",
    ]

    for field in numeric_fields:
        if field in current and field in previous:
            curr_val = current[field]
            prev_val = previous[field]
            if curr_val != prev_val:
                changes[field] = {"previous": prev_val, "current": curr_val, "delta": curr_val - prev_val}

    status_fields = ["status", "contract_status", "quality_grade"]
    for field in status_fields:
        if field in current and field in previous:
            if current[field] != previous[field]:
                changes[field] = {"previous": previous[field], "current": current[field]}

    return changes


def detect_regressions(changes: dict, current: dict) -> list[str]:
    """Detect regressions from changes."""
    regressions = []

    # Contract status changed to fail
    if "contract_status" in changes:
        if changes["contract_status"]["current"] == "fail" and changes["contract_status"]["previous"] == "pass":
            regressions.append("contract_status changed from pass to fail")

    # Semantic errors increased
    if "semantic_error_count" in changes:
        if changes["semantic_error_count"]["delta"] > 0:
            regressions.append(f"semantic_error_count increased by {changes['semantic_error_count']['delta']}")

    # Breaking drift increased
    if "drift_breaking_count" in changes:
        if changes["drift_breaking_count"]["delta"] > 0:
            regressions.append(f"drift_breaking_count increased by {changes['drift_breaking_count']['delta']}")

    # Quality score dropped significantly
    if "quality_score" in changes:
        delta = changes["quality_score"]["delta"]
        if delta < -5:
            regressions.append(f"quality_score dropped by {abs(delta):.1f}")

    # Status degraded
    if "status" in changes:
        status_order = {"pass": 0, "warn": 1, "review_needed": 2, "blocked": 3}
        prev_status = changes["status"]["previous"]
        curr_status = changes["status"]["current"]
        if status_order.get(curr_status, 99) > status_order.get(prev_status, 0):
            regressions.append(f"status degraded from {prev_status} to {curr_status}")

    return regressions


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Compare dataset quality trend snapshots")
    parser.add_argument("--current", required=True, help="Current trend snapshot JSON")
    parser.add_argument("--previous", required=True, help="Previous trend snapshot JSON")
    parser.add_argument("--out-json", required=True, help="Output comparison JSON")
    parser.add_argument("--out-md", required=True, help="Output comparison Markdown")
    parser.add_argument("--fail-on-regression", action="store_true", help="Exit non-zero on regression")
    args = parser.parse_args(argv)

    current_path = Path(args.current)
    previous_path = Path(args.previous)

    if not current_path.exists():
        print(f"error: current snapshot not found: {current_path}", file=sys.stderr)
        return 1

    if not previous_path.exists():
        print(f"error: previous snapshot not found: {previous_path}", file=sys.stderr)
        return 1

    current = json.loads(current_path.read_text(encoding="utf-8"))
    previous = json.loads(previous_path.read_text(encoding="utf-8"))

    changes = compare_trends(current, previous)
    regressions = detect_regressions(changes, current)

    comparison = {
        "current_generated_at": current.get("generated_at", "unknown"),
        "previous_generated_at": previous.get("generated_at", "unknown"),
        "changes": changes,
        "regressions": regressions,
        "regression_count": len(regressions),
    }

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    safe_json_write(out_json, comparison)

    md_lines = [
        "# Dataset Quality Trend Comparison",
        "",
        f"- current_generated_at: `{comparison['current_generated_at']}`",
        f"- previous_generated_at: `{comparison['previous_generated_at']}`",
        f"- regression_count: `{comparison['regression_count']}`",
        "",
    ]

    if regressions:
        md_lines.append("## Regressions Detected")
        md_lines.append("")
        for reg in regressions:
            md_lines.append(f"- {reg}")
        md_lines.append("")

    if changes:
        md_lines.append("## Changes")
        md_lines.append("")
        for field, change in changes.items():
            if "delta" in change:
                md_lines.append(
                    f"- {field}: {change['previous']} → {change['current']} (delta: {change['delta']:+.1f})"
                )
            else:
                md_lines.append(f"- {field}: {change['previous']} → {change['current']}")
        md_lines.append("")
    else:
        md_lines.append("No changes detected.")
        md_lines.append("")

    md_lines.append("## Reviewer Note")
    md_lines.append("")
    if regressions:
        md_lines.append("**Action required**: Regressions detected. Review changes and address issues.")
    else:
        md_lines.append("**No action needed**: No regressions detected.")
    md_lines.append("")

    out_md = Path(args.out_md)
    out_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    if args.fail_on_regression and regressions:
        print(
            json.dumps({"status": "regression", "regression_count": len(regressions)}, ensure_ascii=True),
            file=sys.stderr,
        )
        return 1

    print(json.dumps({"status": "ok", "regression_count": len(regressions)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
