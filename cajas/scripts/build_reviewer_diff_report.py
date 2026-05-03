#!/usr/bin/env python3
"""Build reviewer diff report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.reviewer_report_diff import (
    build_reviewer_diff_report,
    generate_reviewer_diff_markdown,
)


def safe_json_write(path: Path, data: dict) -> None:
    """Write JSON safely."""
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Build reviewer diff report")
    parser.add_argument("--baseline-root", required=True, help="Baseline report root directory")
    parser.add_argument("--current-root", required=True, help="Current report root directory")
    parser.add_argument("--out-json", required=True, help="Output diff report JSON path")
    parser.add_argument("--out-md", required=True, help="Output diff report Markdown path")
    parser.add_argument("--warn-only", action="store_true", help="Never exit non-zero (warn only mode)")
    args = parser.parse_args(argv)

    baseline_root = Path(args.baseline_root)
    current_root = Path(args.current_root)

    if not baseline_root.exists():
        print(f"error: baseline root not found: {baseline_root}", file=sys.stderr)
        return 1

    if not current_root.exists():
        print(f"error: current root not found: {current_root}", file=sys.stderr)
        return 1

    result = build_reviewer_diff_report(baseline_root, current_root)

    # Write JSON report
    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)

    report_data = {
        "overall_status": result.overall_status,
        "baseline_root": result.baseline_root,
        "current_root": result.current_root,
        "changed_fields": result.changed_fields,
        "missing_artifacts": result.missing_artifacts,
        "extra_artifacts": result.extra_artifacts,
        "quality_score_delta": result.quality_score_delta,
        "status_change": result.status_change,
        "contract_error_delta": result.contract_error_delta,
        "semantic_error_delta": result.semantic_error_delta,
        "drift_breaking_delta": result.drift_breaking_delta,
        "runtime_budget_change": result.runtime_budget_change,
        "reviewer_notes": result.reviewer_notes,
    }
    safe_json_write(out_json, report_data)

    # Write Markdown report
    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    markdown = generate_reviewer_diff_markdown(result)
    out_md.write_text(markdown, encoding="utf-8")

    # Determine exit code
    if result.overall_status == "fail" and not args.warn_only:
        print(
            json.dumps({"status": "fail", "overall_status": result.overall_status}, ensure_ascii=True),
            file=sys.stderr,
        )
        return 1

    print(json.dumps({"status": "ok", "overall_status": result.overall_status}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
