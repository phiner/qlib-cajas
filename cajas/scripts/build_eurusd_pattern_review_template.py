#!/usr/bin/env python3
"""Build EURUSD pattern review template artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cajas.reports.validation_eurusd_pattern_review_template import (
    build_validation_eurusd_pattern_review_template,
    render_validation_eurusd_pattern_review_template_markdown,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD pattern review template")
    parser.add_argument("--samples-csv", type=Path, default=Path("tmp/eurusd/EURUSD_15m_pattern_review_samples.csv"))
    parser.add_argument("--label-schema", required=True, type=Path)
    parser.add_argument("--output-template-csv", required=True, type=Path)
    parser.add_argument("--output-template-jsonl", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    args = parser.parse_args(argv)

    payload = build_validation_eurusd_pattern_review_template(
        samples_path=args.samples_csv,
        label_schema_path=args.label_schema,
        output_template_csv=args.output_template_csv,
        output_template_jsonl=args.output_template_jsonl,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.output_md.write_text(render_validation_eurusd_pattern_review_template_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "out_json": str(args.output_json), "out_md": str(args.output_md)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
