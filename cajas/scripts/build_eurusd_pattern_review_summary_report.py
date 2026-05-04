#!/usr/bin/env python3
"""Build EURUSD pattern review summary report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_eurusd_pattern_review_summary import (
    build_validation_eurusd_pattern_review_summary,
    render_validation_eurusd_pattern_review_summary_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD pattern review summary report")
    parser.add_argument("--feedback-report", type=Path, default=Path("tmp/validation-eurusd-pattern-review-feedback.json"))
    parser.add_argument("--completed-review-csv", type=Path, default=Path("tmp/eurusd/EURUSD_15m_pattern_review_completed.csv"))
    parser.add_argument("--candidate-pack-report", type=Path, default=Path("tmp/validation-eurusd-pattern-candidate-pack.json"))
    parser.add_argument("--minimum-review-threshold", type=int, default=100)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    args = parser.parse_args(argv)

    payload = build_validation_eurusd_pattern_review_summary(
        feedback_report=args.feedback_report,
        completed_review_csv=args.completed_review_csv,
        candidate_pack_report=args.candidate_pack_report,
        minimum_review_threshold=args.minimum_review_threshold,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.output_md.write_text(render_validation_eurusd_pattern_review_summary_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.output_json), "out_md": str(args.output_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
