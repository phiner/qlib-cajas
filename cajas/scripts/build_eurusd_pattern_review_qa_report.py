#!/usr/bin/env python3
"""Build EURUSD pattern review QA report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_eurusd_pattern_review_qa import (
    build_validation_eurusd_pattern_review_qa,
    render_validation_eurusd_pattern_review_qa_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD pattern review QA report")
    parser.add_argument("--candidates-csv", type=Path, default=Path("tmp/eurusd/EURUSD_15m_pattern_candidates.csv"))
    parser.add_argument("--samples-csv", type=Path, default=Path("tmp/eurusd/EURUSD_15m_pattern_review_samples.csv"))
    parser.add_argument("--candidate-pack-report", type=Path, default=Path("tmp/validation-eurusd-pattern-candidate-pack.json"))
    parser.add_argument("--clean-view-csv", type=Path, default=Path("tmp/eurusd/EURUSD_15m_Bid_clean_view.csv"))
    parser.add_argument("--expected-max-samples-per-type", type=int, default=50)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    args = parser.parse_args(argv)

    payload = build_validation_eurusd_pattern_review_qa(
        candidates_csv=args.candidates_csv,
        samples_path=args.samples_csv,
        candidate_pack_report=args.candidate_pack_report,
        clean_view_csv=args.clean_view_csv,
        expected_max_samples_per_type=args.expected_max_samples_per_type,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.output_md.write_text(render_validation_eurusd_pattern_review_qa_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.output_json), "out_md": str(args.output_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
