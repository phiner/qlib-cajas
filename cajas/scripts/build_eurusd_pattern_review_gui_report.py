"""Build EURUSD pattern review GUI validation report."""
import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_pattern_review_gui import (
    build_gui_validation_report,
    format_gui_validation_markdown
)


def main():
    parser = argparse.ArgumentParser(description="Build EURUSD pattern review GUI validation report")
    parser.add_argument("--app-path", type=Path, default=Path("cajas/apps/eurusd_pattern_review_app.py"))
    parser.add_argument("--clean-view-csv", type=Path, required=True)
    parser.add_argument("--review-batch-csv", type=Path, required=True)
    parser.add_argument("--completed-output-csv", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    
    args = parser.parse_args()
    
    report = build_gui_validation_report(
        app_path=args.app_path,
        clean_view_csv=args.clean_view_csv,
        review_batch_csv=args.review_batch_csv,
        completed_output_csv=args.completed_output_csv
    )
    
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_json, "w") as f:
        json.dump(report, f, indent=2)
    
    md = format_gui_validation_markdown(report)
    with open(args.output_md, "w") as f:
        f.write(md)
    
    print(f"GUI validation: {report['status']}")
    print(f"Streamlit: {report['streamlit_available']}")
    print(f"Plotly: {report['plotly_available']}")
    print(f"Output JSON: {args.output_json}")
    print(f"Output MD: {args.output_md}")


if __name__ == "__main__":
    main()
