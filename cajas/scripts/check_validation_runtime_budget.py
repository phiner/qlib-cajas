#!/usr/bin/env python3
"""Check validation runtime against budgets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_runtime_budget import (
    check_validation_runtime_budgets,
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

    results, overall_status = check_validation_runtime_budgets(timing_data, budget_config)

    # Write JSON report
    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)

    report_data = {
        "overall_status": overall_status,
        "warn_threshold_ratio": budget_config.get("warn_threshold_ratio", 1.15),
        "results": [
            {
                "component": r.component,
                "status": r.status,
                "observed_seconds": r.observed_seconds,
                "budget_seconds": r.budget_seconds,
                "delta_seconds": r.delta_seconds,
                "ratio": r.ratio,
                "reviewer_note": r.reviewer_note,
            }
            for r in results
        ],
    }
    safe_json_write(out_json, report_data)

    # Write Markdown report
    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    markdown = generate_budget_report_markdown(results, overall_status, budget_config)
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
