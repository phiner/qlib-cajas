#!/usr/bin/env python3
"""Check validation runtime against budgets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_runtime_budget import (
    build_validation_runtime_budget_report,
    generate_budget_report_markdown,
    load_budget_config,
)


def safe_json_write(path: Path, data: dict) -> None:
    """Write JSON safely."""
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Check validation runtime against budgets")
    parser.add_argument("--budgets", required=True, help="Budget configuration JSON path")
    parser.add_argument("--timing-json", required=True, help="Timing data JSON path")
    parser.add_argument("--out-json", required=True, help="Output budget report JSON path")
    parser.add_argument("--out-md", required=True, help="Output budget report Markdown path")
    parser.add_argument("--fail-on-warn", action="store_true", help="Exit non-zero on warn status")
    parser.add_argument("--expected-tier", default="fast", help="Expected timing tier (set empty to disable check)")
    parser.add_argument("--max-age-seconds", type=int, default=3600, help="Maximum timing age before warning")
    args = parser.parse_args(argv)

    budget_path = Path(args.budgets)
    timing_path = Path(args.timing_json)

    if not budget_path.exists():
        print(f"error: budget config not found: {budget_path}", file=sys.stderr)
        return 1

    if not timing_path.exists():
        print(f"error: timing data not found: {timing_path}", file=sys.stderr)
        return 1

    try:
        budget_config = load_budget_config(budget_path)
        timing_data = json.loads(timing_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"error: failed to parse JSON: {e}", file=sys.stderr)
        return 1

    report_data = build_validation_runtime_budget_report(
        timing_data,
        budget_config,
        expected_tier=args.expected_tier or None,
        max_age_seconds=args.max_age_seconds,
        timing_path=timing_path,
    )
    overall_status = report_data["overall_status"]

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    safe_json_write(out_json, report_data)

    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    # Rebuild dataclass-style rows for markdown rendering.
    from cajas.reports.validation_runtime_budget import BudgetCheckResult  # local import to avoid circular changes

    rows = [
        BudgetCheckResult(
            component=item["component"],
            status=item["status"],
            observed_seconds=item.get("observed_seconds"),
            budget_seconds=item.get("budget_seconds"),
            delta_seconds=item.get("delta_seconds"),
            ratio=item.get("ratio"),
            warn_margin_seconds=item.get("warn_margin_seconds"),
            reason_code=item.get("reason_code", "unknown"),
            category=item.get("category", "unknown"),
            action=item.get("action", "review"),
            reviewer_note=item.get("reviewer_note", ""),
        )
        for item in report_data.get("results", [])
    ]
    markdown = generate_budget_report_markdown(
        rows,
        overall_status,
        budget_config,
        timing_consistency=report_data.get("timing_consistency"),
    )
    out_md.write_text(markdown, encoding="utf-8")

    # Determine exit code
    if overall_status == "fail":
        print(
            json.dumps({"status": "fail", "overall_status": overall_status}, ensure_ascii=True),
            file=sys.stderr,
        )
        return 1
    elif overall_status == "warn" and args.fail_on_warn:
        print(
            json.dumps({"status": "warn", "overall_status": overall_status}, ensure_ascii=True),
            file=sys.stderr,
        )
        return 1

    print(json.dumps({"status": "ok", "overall_status": overall_status}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
