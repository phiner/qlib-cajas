"""Build EURUSD 15m pattern review batch merge report."""
import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_pattern_review_batch_merge import (
    build_batch_merge_report,
    format_batch_merge_markdown
)


def main():
    parser = argparse.ArgumentParser(description="Build EURUSD 15m pattern review batch merge report")
    parser.add_argument("--batch-completion-report", type=Path, required=True)
    parser.add_argument("--completed-batch-csv", type=Path, required=True)
    parser.add_argument("--full-completed-review-csv", type=Path, required=True)
    parser.add_argument("--label-schema", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    
    args = parser.parse_args()
    
    report = build_batch_merge_report(
        batch_completion_report_json=args.batch_completion_report,
        completed_batch_csv=args.completed_batch_csv,
        full_completed_review_csv=args.full_completed_review_csv,
        label_schema_json=args.label_schema
    )
    
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_json, "w") as f:
        json.dump(report, f, indent=2)
    
    md = format_batch_merge_markdown(report)
    with open(args.output_md, "w") as f:
        f.write(md)
    
    print(f"Merge report: {report['status']}")
    print(f"Merge performed: {report.get('merge_performed', False)}")
    print(f"Reviewed added: {report.get('reviewed_count_added', 0)}")
    print(f"Output JSON: {args.output_json}")
    print(f"Output MD: {args.output_md}")


if __name__ == "__main__":
    main()
