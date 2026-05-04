#!/usr/bin/env python3
"""Build EURUSD sampling source-range report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_sampling_source_range import (
    RAW_DEFAULT,
    build_validation_eurusd_sampling_source_range,
    render_validation_eurusd_sampling_source_range_markdown,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build EURUSD sampling source-range report")
    parser.add_argument("--raw-source", type=Path, default=RAW_DEFAULT)
    parser.add_argument("--clean-view", type=Path, default=Path("tmp/eurusd/EURUSD_15m_Bid_clean_view.csv"))
    parser.add_argument("--candidates", type=Path, default=Path("tmp/eurusd/EURUSD_15m_pattern_candidates.csv"))
    parser.add_argument("--template", type=Path, default=Path("tmp/eurusd/EURUSD_15m_pattern_review_template.csv"))
    parser.add_argument("--batch", type=Path, default=Path("tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv"))
    parser.add_argument("--output-json", type=Path, default=Path("tmp/validation-eurusd-sampling-source-range.json"))
    parser.add_argument("--output-md", type=Path, default=Path("tmp/validation-eurusd-sampling-source-range.md"))
    args = parser.parse_args()

    payload = build_validation_eurusd_sampling_source_range(
        raw_source_path=args.raw_source,
        clean_view_path=args.clean_view,
        candidate_path=args.candidates,
        template_path=args.template,
        batch_path=args.batch,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    args.output_md.write_text(render_validation_eurusd_sampling_source_range_markdown(payload), encoding="utf-8")
    print(json.dumps({"status": "ok", "output_json": str(args.output_json), "output_md": str(args.output_md)}))


if __name__ == "__main__":
    main()
