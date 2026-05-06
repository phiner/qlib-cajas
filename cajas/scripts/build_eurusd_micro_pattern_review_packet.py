#!/usr/bin/env python3
"""Build EURUSD micro-pattern review packet artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cajas.reports.validation_eurusd_micro_pattern_review_packet import (
    build_micro_pattern_review_packet,
    render_micro_pattern_review_packet_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build EURUSD micro-pattern review packet")
    parser.add_argument("--market-state-csv", type=Path, default=Path("tmp/eurusd/EURUSD_15m_market_state_dataset.csv"))
    parser.add_argument("--output-csv", type=Path, default=Path("tmp/eurusd/EURUSD_15m_micro_pattern_review_packet.csv"))
    parser.add_argument("--output-jsonl", type=Path, default=Path("tmp/eurusd/EURUSD_15m_micro_pattern_review_packet.jsonl"))
    parser.add_argument("--trial-approval-json", type=Path, default=Path("tmp/validation-eurusd-llm-trial-approval.json"))
    parser.add_argument("--output-json", type=Path, default=Path("tmp/validation-eurusd-micro-pattern-review-packet.json"))
    parser.add_argument("--output-md", type=Path, default=Path("tmp/validation-eurusd-micro-pattern-review-packet.md"))
    parser.add_argument("--max-rows", type=int, default=200)
    args = parser.parse_args()

    report = build_micro_pattern_review_packet(
        market_state_csv=args.market_state_csv,
        output_csv=args.output_csv,
        output_jsonl=args.output_jsonl,
        trial_approval_json=args.trial_approval_json,
        max_rows=args.max_rows,
    )

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.output_md.write_text(render_micro_pattern_review_packet_markdown(report), encoding="utf-8")
    print(json.dumps({"status": "ok", "report_status": report.get("report_status"), "output_json": str(args.output_json), "output_md": str(args.output_md)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
