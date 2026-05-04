"""Build EURUSD 15m pattern review batch."""
import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_pattern_review_batch import (
    build_review_batch_report,
    format_batch_report_markdown
)


def main():
    parser = argparse.ArgumentParser(description="Build EURUSD 15m pattern review batch")
    parser.add_argument("--template-csv", type=Path, required=True)
    parser.add_argument("--label-schema", type=Path, required=True)
    parser.add_argument("--batch-id", default="eurusd_15m_pattern_review_batch_001")
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--per-type-target", type=int, default=10)
    parser.add_argument("--output-batch-csv", type=Path, required=True)
    parser.add_argument("--output-batch-jsonl", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    
    args = parser.parse_args()
    
    report = build_review_batch_report(
        template_csv=args.template_csv,
        label_schema_json=args.label_schema,
        batch_id=args.batch_id,
        batch_size=args.batch_size,
        per_type_target=args.per_type_target,
        output_batch_csv=args.output_batch_csv,
        output_batch_jsonl=args.output_batch_jsonl
    )
    
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_json, "w") as f:
        json.dump(report, f, indent=2)
    
    md = format_batch_report_markdown(report)
    with open(args.output_md, "w") as f:
        f.write(md)
    
    print(f"Batch report: {report['status']}")
    print(f"Batch rows: {report.get('batch_row_count', 0)}")
    print(f"Output JSON: {args.output_json}")
    print(f"Output MD: {args.output_md}")


if __name__ == "__main__":
    main()
