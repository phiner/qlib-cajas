"""Build EURUSD rejected samples report artifacts."""

import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_rejected_samples import (
    build_rejected_samples_report,
    format_rejected_samples_markdown,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build EURUSD rejected samples report")
    parser.add_argument("--rejected-csv", type=Path, required=True)
    parser.add_argument("--rejected-events-jsonl", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    report = build_rejected_samples_report(
        rejected_csv=args.rejected_csv,
        rejected_events_jsonl=args.rejected_events_jsonl,
    )

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.output_md.write_text(format_rejected_samples_markdown(report), encoding="utf-8")

    print(f"Rejected report status: {report.get('status')}")
    print(f"Rejected count: {report.get('rejected_count', 0)}")
    print(f"Output JSON: {args.output_json}")
    print(f"Output MD: {args.output_md}")


if __name__ == "__main__":
    main()
