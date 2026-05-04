"""Build EURUSD 15m pattern review guide."""
import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_pattern_review_guide import (
    build_review_guide_report,
    format_review_guide_markdown
)


def main():
    parser = argparse.ArgumentParser(description="Build EURUSD 15m pattern review guide")
    parser.add_argument("--label-schema", type=Path, required=True)
    parser.add_argument("--batch-report", type=Path)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    
    args = parser.parse_args()
    
    report = build_review_guide_report(
        label_schema_json=args.label_schema,
        batch_report_json=args.batch_report
    )
    
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_json, "w") as f:
        json.dump(report, f, indent=2)
    
    md = format_review_guide_markdown(report)
    with open(args.output_md, "w") as f:
        f.write(md)
    
    print(f"Guide report: {report['status']}")
    print(f"Output JSON: {args.output_json}")
    print(f"Output MD: {args.output_md}")


if __name__ == "__main__":
    main()
