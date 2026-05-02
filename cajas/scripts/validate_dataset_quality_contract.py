#!/usr/bin/env python3
"""Validate dataset quality report schema contracts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cajas.reports.dataset_quality_schema_contract import validate_bundle_contract, validate_report_contract  # noqa: E402
from cajas.reports.runtime_io_summary import safe_json_write  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    """Validate dataset quality schema contracts."""
    p = argparse.ArgumentParser(description="Validate dataset quality report schema contracts.")
    p.add_argument("--report-json", help="Path to single report JSON")
    p.add_argument("--report-type", help="Report type for single report validation")
    p.add_argument("--bundle-root", help="Path to bundle root directory")
    p.add_argument("--out-json", help="Output JSON path")
    p.add_argument("--out-md", help="Output Markdown path")
    p.add_argument("--allow-warnings", action="store_true", help="Exit 0 even with warnings")
    args = p.parse_args(argv)

    issues = []

    if args.report_json:
        if not args.report_type:
            print("error: --report-type required with --report-json", file=sys.stderr)
            return 2
        report_path = Path(args.report_json).expanduser().resolve()
        if not report_path.exists():
            print(f"error: report not found: {report_path}", file=sys.stderr)
            return 2
        report = json.loads(report_path.read_text(encoding="utf-8"))
        issues = validate_report_contract(report, args.report_type)

    elif args.bundle_root:
        bundle_root = Path(args.bundle_root).expanduser().resolve()
        bundle = {}
        report_paths = {
            "dataset_quality_report": bundle_root / "dataset_quality" / "dataset_quality_report.json",
            "feature_schema_manifest": bundle_root / "features" / "feature_schema_manifest.json",
            "offline_research_queue_summary": bundle_root / "research_queue" / "offline_research_queue_summary.json",
        }
        for key, path in report_paths.items():
            if path.exists():
                bundle[key] = json.loads(path.read_text(encoding="utf-8"))
            else:
                print(f"warning: bundle file not found: {path}", file=sys.stderr)
        issues = validate_bundle_contract(bundle)

    else:
        print("error: either --report-json or --bundle-root required", file=sys.stderr)
        return 2

    error_count = sum(1 for i in issues if i.severity == "error")
    warning_count = sum(1 for i in issues if i.severity == "warning")

    result = {
        "status": "pass" if error_count == 0 else "fail",
        "error_count": error_count,
        "warning_count": warning_count,
        "issues": [{"severity": i.severity, "path": i.path, "message": i.message} for i in issues],
    }

    if args.out_json:
        out_json = Path(args.out_json).expanduser().resolve()
        out_json.parent.mkdir(parents=True, exist_ok=True)
        safe_json_write(out_json, result)

    if args.out_md:
        out_md = Path(args.out_md).expanduser().resolve()
        out_md.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Dataset Quality Contract Validation",
            "",
            f"- status: `{result['status']}`",
            f"- error_count: `{error_count}`",
            f"- warning_count: `{warning_count}`",
            "",
        ]
        if issues:
            lines.append("## Issues")
            lines.append("")
            for issue in issues:
                lines.append(f"- [{issue.severity}] {issue.path}: {issue.message}")
        else:
            lines.append("No issues found.")
        out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(result, ensure_ascii=True))

    if error_count > 0:
        return 1
    if warning_count > 0 and not args.allow_warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
