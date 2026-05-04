#!/usr/bin/env python3
"""Build EURUSD pattern review feedback report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_eurusd_pattern_review_feedback import (
    build_validation_eurusd_pattern_review_feedback,
    render_validation_eurusd_pattern_review_feedback_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD pattern review feedback report")
    parser.add_argument("--template-csv", type=Path, default=Path("tmp/eurusd/EURUSD_15m_pattern_review_template.csv"))
    parser.add_argument("--completed-review-csv", type=Path, default=Path("tmp/eurusd/EURUSD_15m_pattern_review_completed.csv"))
    parser.add_argument("--label-schema", type=Path, default=Path("tmp/validation-eurusd-pattern-label-schema.json"))
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    args = parser.parse_args(argv)

    payload = build_validation_eurusd_pattern_review_feedback(
        template_csv=args.template_csv,
        completed_review_csv=args.completed_review_csv,
        label_schema=args.label_schema,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.output_md.write_text(render_validation_eurusd_pattern_review_feedback_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.output_json), "out_md": str(args.output_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
