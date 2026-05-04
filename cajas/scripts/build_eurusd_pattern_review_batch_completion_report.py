"""Build EURUSD 15m pattern review batch completion report."""
import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_pattern_review_batch_completion import (
    build_batch_completion_report,
    format_batch_completion_markdown
)


def main():
    parser = argparse.ArgumentParser(description="Build EURUSD 15m pattern review batch completion report")
    parser.add_argument("--batch-csv", type=Path, required=True)
    parser.add_argument("--completed-batch-csv", type=Path, required=True)
    parser.add_argument("--label-schema", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    
    args = parser.parse_args()
    
    report = build_batch_completion_report(
        batch_csv=args.batch_csv,
        completed_batch_csv=args.completed_batch_csv,
        label_schema_json=args.label_schema
    )
    
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_json, "w") as f:
        json.dump(report, f, indent=2)
    
    md = format_batch_completion_markdown(report)
    with open(args.output_md, "w") as f:
        f.write(md)
    
    print(f"Completion report: {report['status']}")
    print(f"Reviewed: {report.get('reviewed_count', 0)}")
    print(f"Pending: {report.get('pending_count', 0)}")
    print(f"Output JSON: {args.output_json}")
    print(f"Output MD: {args.output_md}")


if __name__ == "__main__":
    main()
