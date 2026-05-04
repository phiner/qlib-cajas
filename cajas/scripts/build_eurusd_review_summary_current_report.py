#!/usr/bin/env python3
"""Build EURUSD current review summary report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_review_summary_current import (
    build_review_summary_current_report,
    render_review_summary_current_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD current review summary report")
    parser.add_argument("--batch-csv", type=Path, default=Path("tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv"))
    parser.add_argument("--completed-csv", type=Path, default=Path("tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv"))
    parser.add_argument("--output-json", type=Path, default=Path("tmp/validation-eurusd-review-summary-current.json"))
    parser.add_argument("--output-md", type=Path, default=Path("tmp/validation-eurusd-review-summary-current.md"))
    args = parser.parse_args()

    payload = build_review_summary_current_report(
        batch_csv=args.batch_csv,
        completed_csv=args.completed_csv,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.output_md.write_text(render_review_summary_current_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "output_json": str(args.output_json), "output_md": str(args.output_md)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
