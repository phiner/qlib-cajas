#!/usr/bin/env python3
"""Build EURUSD human review quality report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_human_review_quality import (
    build_human_review_quality_report,
    render_human_review_quality_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD human review quality report")
    parser.add_argument("--batch-csv", type=Path, default=Path("tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv"))
    parser.add_argument("--completed-csv", type=Path, default=Path("tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv"))
    parser.add_argument("--output-json", type=Path, default=Path("tmp/validation-eurusd-human-review-quality.json"))
    parser.add_argument("--output-md", type=Path, default=Path("tmp/validation-eurusd-human-review-quality.md"))
    args = parser.parse_args()

    payload = build_human_review_quality_report(batch_csv=args.batch_csv, completed_csv=args.completed_csv)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.output_md.write_text(render_human_review_quality_markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "ok",
                "report_status": payload.get("report_status"),
                "output_json": str(args.output_json),
                "output_md": str(args.output_md),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
